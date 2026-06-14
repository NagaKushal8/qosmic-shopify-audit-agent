"""robots.txt fetch + parse.

Per decision **D7 (polite-only)**: robots.txt is parsed ONLY to
  (a) honor `Crawl-delay`, and
  (b) report "robots.txt present" as a technical check.
We deliberately do NOT use `Disallow` rules to prune discovery, because Shopify's
default robots.txt disallows /cart, /checkout, /account, /search — the exact
CRO-critical surfaces an audit must inspect. Disallow rules are still captured
(for reporting/transparency), just never enforced as a crawl gate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx


@dataclass
class RobotsInfo:
    present: bool
    status_code: Optional[int] = None
    crawl_delay: Optional[float] = None
    sitemaps: list[str] = field(default_factory=list)
    disallows: list[str] = field(default_factory=list)  # recorded, NOT enforced (D7)
    raw: str = ""


def root_url(url: str) -> str:
    """scheme://netloc for any input (adds https:// if scheme missing)."""
    parsed = urlparse(url if "//" in url else "https://" + url)
    return f"{parsed.scheme}://{parsed.netloc}"


def parse_robots(text: str, user_agent: str = "*") -> dict:
    """Pure, network-free parser.

    Returns {'crawl_delay', 'disallows', 'sitemaps'} for the matching user-agent
    group (exact match preferred, falling back to '*'). Sitemaps are global per
    the robots spec (not user-agent scoped).
    """
    groups: dict[str, dict] = {}
    sitemaps: list[str] = []
    current_agents: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        name, _, value = line.partition(":")
        name = name.strip().lower()
        value = value.strip()

        if name == "user-agent":
            ua = value.lower()
            current_agents = [ua]
            groups.setdefault(ua, {"crawl_delay": None, "disallows": []})
        elif name == "sitemap":
            if value:
                sitemaps.append(value)
        elif name in ("disallow", "crawl-delay"):
            for ua in current_agents or ["*"]:
                grp = groups.setdefault(ua, {"crawl_delay": None, "disallows": []})
                if name == "disallow" and value:
                    grp["disallows"].append(value)
                elif name == "crawl-delay":
                    try:
                        grp["crawl_delay"] = float(value)
                    except ValueError:
                        pass

    chosen = (
        groups.get(user_agent.lower())
        or groups.get("*")
        or {"crawl_delay": None, "disallows": []}
    )
    return {
        "crawl_delay": chosen["crawl_delay"],
        "disallows": chosen["disallows"],
        "sitemaps": sitemaps,
    }


def fetch_robots(base_url: str, client: httpx.Client, user_agent: str = "*") -> RobotsInfo:
    """Fetch + parse /robots.txt. Never raises — absence/error => present=False."""
    robots_url = urljoin(root_url(base_url) + "/", "robots.txt")
    try:
        resp = client.get(robots_url)
    except httpx.HTTPError:
        return RobotsInfo(present=False)

    if resp.status_code != 200 or not resp.text.strip():
        return RobotsInfo(present=False, status_code=resp.status_code)

    parsed = parse_robots(resp.text, user_agent)
    return RobotsInfo(
        present=True,
        status_code=resp.status_code,
        crawl_delay=parsed["crawl_delay"],
        sitemaps=parsed["sitemaps"],
        disallows=parsed["disallows"],
        raw=resp.text,
    )
