---
name: crawl
description: >-
  Crawl a Shopify storefront into a reproducible evidence folder (screenshots,
  rendered HTML, metadata) and build a routed, signal-rich digest. Use this as
  the FIRST phase of a Qosmic audit, before reasoning. Input: one storefront URL.
---

# Crawl & digest a storefront

You are running the **Crawl** phase of a Qosmic audit. Goal: turn one URL into a
folder of cited evidence + a digest the reason phase can route to pillar agents.

## Step 0 — ensure the environment (mandatory)
The crawl tools are deterministic Python with pinned deps. Run the idempotent
bootstrap first; it only does work the first time:

```bash
python tools/setup_env.py            # creates .venv, installs pins + Chromium
```

Use the venv interpreter for everything below:
- Windows: `./.venv/Scripts/python.exe`
- macOS/Linux: `./.venv/bin/python`

## Step 1 — crawl
```bash
./.venv/Scripts/python.exe tools/crawl.py <URL>
```
What it does (you don't reimplement this — the Python owns it):
- fetches robots.txt (politeness only — never a crawl gate);
- **health gate**: if the homepage is unreachable / 5xx / 404, or every page is dead,
  it aborts early with `status=dead:*` / `dead_site` — STOP and report that to the user;
- BFS-discovers same-host surfaces (seeded with homepage + functional routes);
- captures up to 30 surfaces: desktop + mobile screenshots, rendered HTML, `meta.json`;
- writes `evidence/<domain>_<timestamp>/manifest.json` (the citation backbone).

Read the printed summary + `manifest.json`. Note the run folder path — you need it next.

## Step 2 — digest
```bash
./.venv/Scripts/python.exe tools/digest.py evidence/<run_dir>
```
This reads the raw evidence (never mutates it) and writes `evidence/<run_dir>/digest/`:
- `digest.json` — per-page CRO signals + routed pillars (authoritative);
- `conversion.md` / `aov.md` / `retention.md` / `acquisition.md` / `performance.md`
  — per-pillar routing indexes (this is what each pillar agent reads);
- `summary.md` — store-level facts.

## Output of this phase
- the run folder path, and
- `status` (`ok` / `blocked:*` / `dead:*` / `dead_site`).

If `status` is anything other than `ok`/`blocked:*` with real pages, tell the user the
store could not be audited and why — do not fabricate findings. Otherwise, hand off to
the **reason** skill with the run folder path.

## Notes / limits
Known limitations live in `wherewefail.md` (sampling caps, no interaction-gated
content, no auth/checkout completion, etc.). Cite only what's in the evidence.
