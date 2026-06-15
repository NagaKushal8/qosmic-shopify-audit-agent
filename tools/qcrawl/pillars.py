"""Preset Shopify surface -> pillar map (decision D12).

Deterministic routing: each crawl surface category maps to its 1-3 most likely
CRO pillars. The digest writes these onto each page so the reason phase can route
pages to pillar agents WITHOUT an LLM. The map is intentionally approximate — the
two-pass self-correction (reason skill) lets an agent pull cross-relevant pages it
finds misrouted.
"""
from __future__ import annotations

PILLARS = ["Conversion", "AOV", "Retention", "Acquisition", "Performance"]

# category (from discovery.categorize) -> likely pillars
SURFACE_PILLARS: dict[str, list[str]] = {
    "home":       ["Conversion", "Acquisition"],
    "product":    ["Conversion", "AOV"],
    "collection": ["Conversion", "AOV"],
    "cart":       ["Conversion", "AOV", "Performance"],
    "checkout":   ["Conversion", "Performance"],
    "search":     ["Conversion", "Acquisition"],
    "account":    ["Retention"],
    "policy":     ["Retention", "Conversion"],
    "blog":       ["Acquisition", "Retention"],
    "page":       ["Conversion", "Acquisition"],
    "other":      ["Conversion"],
}


def pillars_for(category: str) -> list[str]:
    """Pillars a given surface category is routed to (defaults to Conversion)."""
    return SURFACE_PILLARS.get(category, ["Conversion"])


def pillar_slug(pillar: str) -> str:
    return pillar.lower()
