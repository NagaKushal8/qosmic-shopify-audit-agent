"""Layer 3 — coverage (no LLM). The eval-side answer to the cross-pillar pain point:
for each high-value surface TYPE the crawl captured, did some experiment engage it in
a pillar that plausibly applies (per the preset map)? Captured-but-unengaged = a flag."""
from __future__ import annotations

from qcrawl.pillars import pillars_for

HIGH_VALUE = {"home", "product", "collection", "cart", "checkout", "page", "blog", "search"}


def _exp_category(exp: dict, pages: list) -> str | None:
    """Which captured surface does this experiment cite? Match by evidence path dir,
    then by URL, else fall back to categorizing the experiment's URL."""
    ev, url = str(exp.get("evidence", "")), str(exp.get("url", "")).rstrip("/")
    for p in pages:
        pdir = p.get("dir") or ""
        if pdir and ev.startswith(pdir):
            return p.get("category")
        if url and url in (str(p.get("url", "")).rstrip("/"), str(p.get("final_url", "")).rstrip("/")):
            return p.get("category")
    if url:
        from qcrawl.discovery import categorize
        return categorize(url)
    return None


def evaluate(run: dict) -> dict:
    pages = run["manifest"].get("pages", [])
    exps = run["experiments"]
    cats_present = sorted({p.get("category") for p in pages if p.get("category") in HIGH_VALUE})

    engaged, flagged = [], []
    for cat in cats_present:
        plausible = set(pillars_for(cat))
        cited_pillars = {e["pillar"] for e in exps
                         if _exp_category(e, pages) == cat and e.get("pillar")}
        if plausible & cited_pillars:
            engaged.append(cat)
        else:
            flagged.append({"category": cat, "plausible_pillars": sorted(plausible),
                            "cited_pillars": sorted(cited_pillars)})

    coverage = round(len(engaged) / len(cats_present), 3) if cats_present else 1.0
    return {
        "coverage": coverage,
        "categories_present": cats_present,
        "categories_engaged": engaged,
        "flagged_gaps": flagged,
    }
