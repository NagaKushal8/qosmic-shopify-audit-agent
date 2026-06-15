"""qcrawl — the deterministic crawl toolkit for the Qosmic audit harness.

Modules:
  robots     — fetch + parse robots.txt (Crawl-delay + presence only; D7)
  discovery  — BFS surface discovery, no sitemap dependency (D6)
  capture    — Playwright screenshots + rendered DOM + metadata (later)
  tech_checks— ~15 deterministic storefront checks (later)
  manifest   — assemble + write manifest.json, the citation backbone (later)
"""

__all__ = ["robots", "discovery", "capture", "manifest", "health",
           "pillars", "digest", "experiments", "tech_checks", "synth", "assemble"]
