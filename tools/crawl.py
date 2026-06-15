#!/usr/bin/env python3
"""Qosmic crawl orchestrator — Shopify URL in, evidence folder out.

Pipeline:
  1. fetch robots.txt        (Crawl-delay + presence only; polite, never a gate — D7)
  2. HEALTH GATE (pre-flight) homepage reachable? not 5xx / 404 / gate? (D11)
  3. BFS discover surfaces   (seeded homepage + functional routes; same-host — D6)
  4. HEALTH GATE (post-disc) any reachable pages at all? else abort (D11)
  5. select a capped sample  (representative across categories)
  6. capture each surface    (desktop + mobile screenshot, rendered HTML, meta.json)
  7. write manifest.json      (citation backbone; ALWAYS written — D9)

Output: a fresh, ordered run folder per invocation:
    evidence/<domain>_<YYYYMMDD-HHMMSS>/
      robots.txt, manifest.json
      pages/00_home_.../{screenshot.png, screenshot-mobile.png, page.html, meta.json}

Usage:
    python tools/crawl.py https://store.com
    python tools/crawl.py https://store.com --out evidence --max-capture 15
"""
from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path
from urllib.parse import urlparse

import httpx

# Allow running as a script (python tools/crawl.py ...) or as a module.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from qcrawl.capture import (  # noqa: E402
    UA_DESKTOP, capture_surfaces, detect_block, render_homepage_links,
)
from qcrawl.discovery import (  # noqa: E402
    Surface, bfs_discover, categorize, same_host, seed_surfaces, select_for_capture,
)
from qcrawl.health import assess_reachability, probe_homepage  # noqa: E402
from qcrawl.manifest import build_manifest, write_manifest  # noqa: E402
from qcrawl.robots import fetch_robots, root_url  # noqa: E402

# Realistic UA (no bot tag) so the httpx pre-flight isn't auto-blocked (D22).
UA = UA_DESKTOP


def _now() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def _finalize(start, run_dir, robots, surfaces, captured_surfaces, *,
              run_status, blocked_reason, started_at, delay, args) -> int:
    """Capture the selected surfaces and ALWAYS write a manifest, then summarize."""
    print(f"[crawl] capturing {len(captured_surfaces)} surface(s)...")
    evidence: list = []
    try:
        evidence = capture_surfaces(
            captured_surfaces, run_dir, timeout=args.timeout, crawl_delay=delay,
            headless=not args.headed, proxy=args.proxy, stealth=not args.no_stealth,
        )
    except Exception as exc:  # last-resort guard — never lose the run (D9)
        run_status = "capture_aborted"
        print(f"[crawl] capture aborted: {type(exc).__name__}: {exc}", file=sys.stderr)
    finally:
        manifest = build_manifest(
            start, run_dir, robots, surfaces, evidence,
            started_at=started_at, finished_at=_now(),
            run_status=run_status, blocked_reason=blocked_reason,
        )
        manifest_path = write_manifest(manifest, run_dir)

    ok = sum(1 for e in evidence if e.status and e.status < 400)
    blocked = [e for e in evidence if e.blocked]
    errored = [e for e in evidence if e.error]
    print(f"[crawl] done. status={run_status} captured={len(evidence)} ok={ok} "
          f"blocked={len(blocked)} errors={len(errored)}")
    print(f"[crawl] manifest: {manifest_path}")
    for e in evidence:
        flag = f" [{e.blocked}]" if e.blocked else (f" [{e.error}]" if e.error else "")
        print(f"   {e.order:02d} {str(e.status):>4} {e.category:<10} {e.url}{flag}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Crawl a Shopify storefront into an evidence folder.")
    ap.add_argument("url", help="storefront URL (e.g. https://store.com)")
    ap.add_argument("--out", default="evidence", help="root evidence dir (default: evidence)")
    ap.add_argument("--max-depth", type=int, default=3, help="BFS max depth (default: 3)")
    ap.add_argument("--max-fetch", type=int, default=60, help="max pages to fetch during discovery")
    ap.add_argument("--max-capture", type=int, default=30, help="max surfaces to screenshot/capture")
    ap.add_argument("--timeout", type=int, default=30, help="per-page timeout seconds (default: 30)")
    ap.add_argument("--max-delay", type=float, default=1.5,
                    help="cap on honored crawl-delay seconds (default: 1.5)")
    ap.add_argument("--no-throttle", action="store_true", help="disable politeness delay")
    ap.add_argument("--headed", action="store_true", help="run the browser headed (debug)")
    ap.add_argument("--proxy", default=None,
                    help="proxy server for browser + httpx (e.g. http://user:pass@host:port) — helps with IP-level WAF blocks")
    ap.add_argument("--no-stealth", action="store_true",
                    help="disable browser stealth (automation flags visible)")
    args = ap.parse_args(argv)

    start = args.url if "//" in args.url else "https://" + args.url
    domain = urlparse(root_url(start)).netloc
    if not domain:
        print(f"[crawl] invalid URL: {args.url!r}", file=sys.stderr)
        return 2

    ts = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = Path(args.out) / f"{domain}_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)
    started_at = _now()
    home_surface = Surface(url=start, category="home", depth=0)
    print(f"[crawl] {start}")
    print(f"[crawl] run dir: {run_dir}")

    homepage_blocked: str | None = None
    delay = 0.0
    surfaces: list = []
    # --- robots + health gate + discovery (httpx, fast) ---
    with httpx.Client(follow_redirects=True, timeout=args.timeout,
                      headers={"user-agent": UA}) as client:
        robots = fetch_robots(start, client)
        if robots.present and robots.raw:
            (run_dir / "robots.txt").write_text(robots.raw, encoding="utf-8")
        delay = 0.0 if args.no_throttle else min(robots.crawl_delay or 0.3, args.max_delay)
        print(f"[crawl] robots.txt present={robots.present} crawl_delay={robots.crawl_delay} "
              f"-> using {delay}s")

        # GATE 1 — homepage health via httpx (fast). (D11)
        health = probe_homepage(start, client, detect_block=detect_block)

        if health.blocked == "password":
            homepage_blocked = "password"  # a real gate — browser can't bypass
            print("[crawl] store is password-protected -> capturing homepage only")
        elif health.ok and not health.blocked:
            surfaces = bfs_discover(
                start, client, max_depth=args.max_depth, max_fetch=args.max_fetch, crawl_delay=delay
            )
        else:
            # httpx was challenged (Cloudflare) or failed — ESCALATE to a stealth
            # browser before giving up (D22). httpx can't run JS, the browser can.
            print(f"[crawl] httpx gate failed (blocked={health.blocked}, reason={health.reason}) "
                  f"-> escalating to stealth browser probe")
            b_html, b_links, b_status = render_homepage_links(
                start, timeout=args.timeout, headless=not args.headed,
                proxy=args.proxy, stealth=not args.no_stealth,
            )
            b_blocked = detect_block(b_html)
            if b_status and b_status < 400 and not b_blocked:
                print(f"[crawl] stealth browser PASSED (status {b_status}) "
                      f"-> browser-based discovery")
                surfaces = seed_surfaces(start, b_links)
            elif (b_blocked or health.blocked):
                homepage_blocked = b_blocked or health.blocked  # genuine gate
                print(f"[crawl] stealth browser also blocked ({homepage_blocked}) "
                      f"-> capturing homepage only")
            else:
                print(f"[crawl] homepage unreachable via httpx AND browser "
                      f"-> aborting (dead:{health.reason})")
                return _finalize(start, run_dir, robots, [], [home_surface],
                                 run_status=f"dead:{health.reason or 'unreachable'}",
                                 blocked_reason=None, started_at=started_at, delay=delay, args=args)

    fetched = sum(1 for s in surfaces if s.fetched)
    print(f"[crawl] discovered {len(surfaces)} surfaces ({fetched} fetched)")

    # Browser-fallback discovery if httpx came back near-empty (JS-rendered) (D9 #4).
    # Skip if already blocked or we already used browser-based discovery.
    strong = sum(1 for s in surfaces if s.fetched and s.status and s.status < 400
                 and s.category != "home")
    already_browser = any(getattr(s, "discovered_from", None) == "browser" for s in surfaces)
    if not homepage_blocked and not already_browser and strong < 2:
        print("[crawl] httpx discovery weak (likely JS-rendered) -> browser-fallback discovery")
        _, links, _ = render_homepage_links(start, timeout=args.timeout, headless=not args.headed,
                                            proxy=args.proxy, stealth=not args.no_stealth)
        root_host = urlparse(root_url(start)).netloc
        known = {s.url for s in surfaces}
        added = 0
        for link in links:
            if same_host(link, root_host) and link not in known:
                surfaces.append(Surface(url=link, category=categorize(link), depth=1,
                                        discovered_from="browser"))
                known.add(link)
                added += 1
        print(f"[crawl] browser-fallback added {added} surfaces")

    # GATE 2 — post-discovery reachability (only meaningful for httpx-fetched data;
    # browser-discovered surfaces are captured later, so don't false-abort on them). (D11)
    if not homepage_blocked and fetched > 0:
        reach = assess_reachability(surfaces)
        if reach["dead"]:
            print(f"[crawl] all {reach['fetched']} discovered pages are unreachable/error "
                  f"-> aborting capture (dead_site)")
            return _finalize(start, run_dir, robots, surfaces, [home_surface],
                             run_status="dead_site", blocked_reason=None,
                             started_at=started_at, delay=delay, args=args)

    # --- select + capture ---
    captured_surfaces = select_for_capture(surfaces)[: args.max_capture]
    if homepage_blocked:
        captured_surfaces = captured_surfaces[:1]  # homepage as proof of the gate only
    run_status = f"blocked:{homepage_blocked}" if homepage_blocked else "ok"
    return _finalize(start, run_dir, robots, surfaces, captured_surfaces,
                     run_status=run_status, blocked_reason=homepage_blocked,
                     started_at=started_at, delay=delay, args=args)


if __name__ == "__main__":
    raise SystemExit(main())
