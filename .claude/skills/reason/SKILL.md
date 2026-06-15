---
name: reason
description: >-
  Generate 10 evidence-grounded CRO experiments across 5 pillars (Conversion, AOV,
  Retention, Acquisition, Performance) from a crawl digest. Use this as the SECOND
  phase of a Qosmic audit, after crawl+digest. Every claim must cite an artifact.
---

# Reason: turn a digest into 10 experiments

You are running the **Reason** phase. Input: a run folder with a built `digest/`
(from the crawl skill). Output: exactly **10 experiments spanning all 5 pillars**,
each grounded in a real evidence artifact.

## The pillar agents
Run **five pillar passes** — Conversion, AOV, Retention, Acquisition, Performance.
Each pass is a **specialist, not a loop iteration**: before it starts, **load its
playbook** `.claude/skills/reason/playbooks/<pillar>.md` and use it as the lens for
that vertical (its leak patterns, KPIs, which digest signals to weight, and
hypothesis / decision-rule templates). The playbook is what makes each pass
specialized. (Filenames are **lowercase**: `conversion.md`, `aov.md`, `retention.md`,
`acquisition.md`, `performance.md` — matters on case-sensitive OSes / Codex.)

Each pass then reads ONLY its routed slice first:
`evidence/<run>/digest/<pillar>.md` + `digest/summary.md`.

> Capability-agnostic: if you can spawn subagents (e.g. Claude Code Task tool), run
> the 5 passes as parallel subagents, one per pillar — give each subagent its
> playbook + routed slice. If not, do 5 focused sequential passes. Either way, keep
> each pass scoped to its pillar.

### Each pillar pass — Pass 1 (generate)
For its routed pages, the pillar agent:
1. **Absorb the playbook's lens** — its diagnostic questions are your interrogation
   checklist; its leak patterns are hypotheses to *test against the evidence*, never
   a list to assume.
2. For each routed page: read the `one_line` + `signals`, then **look at the
   screenshot** to confirm the leak visually. Pull `html_path` (Read tool) **only if**
   you need detail beyond screenshot + signals (HTML on demand — not by default).
3. Propose **as many strong candidates as the evidence supports, HARD CEILING 4**
   (open-ended, not a quota — D15). Cite the exact artifact path each claim rests on.

**Reasoning discipline (this is what separates us from a generic LLM search):**
- **Evidence-first, not template-first.** Start from what THIS store's screenshot/
  signals actually show, then reach for the matching playbook pattern — not the
  reverse. If the evidence shows a clean PDP (price + add-to-cart + reviews present),
  do NOT manufacture a leak to fill a quota.
- **No overfit.** Never import findings from other audits or assume a vertical's
  clichés. The leak must be visible in this run's artifacts.
- **Benchmark-anchored confidence.** Calibrate `confidence` and `expected_lift` from
  the playbook's benchmarks AND evidence strength: authoritative benchmark + clearly
  visible leak → high confidence; rule-of-thumb benchmark or inferred leak → lower.
- **Honest absence.** A pillar with little evidence should propose fewer (or zero)
  experiments rather than weak ones — that's a finding, not a failure.
- **Unverified ≠ absent (critical).** Signals are tri-state: `present` / `absent` /
  `unverified`. `unverified` means we never observed the interaction-gated surface
  (e.g. add-to-cart wasn't triggered, so the cart drawer is unknown). **Never propose
  a "you're missing X" experiment from an `unverified` signal.** Either look at the
  interaction artifact when present (`drawer_screenshot`, `popup_screenshot`), or, if
  truly unverified, omit the claim or downgrade it to "appears missing — not confirmed
  via interaction" with capped confidence. Many Shopify features (cross-sell,
  free-shipping bar, email capture) live in a drawer/modal that a static page never shows.

**Structured output (required):** each pillar agent returns a **JSON array of
experiment objects** conforming to `schema/experiment.schema.json` — not prose.
`confidence` is a number 0–100 (this is what selection sorts on). If your runtime
supports tool use / structured outputs, enforce the schema via the tool input;
otherwise emit the JSON and rely on the validator below.

### Each pillar pass — Pass 2 (self-correct)
Then the agent skims the **full lightweight index** (`digest/summary.md` lists every
page + its routed pillars). If it spots a page that's misrouted or cross-relevant to
its pillar, it **pulls that specific page** (screenshot/html) and refines/adds a
candidate. This absorbs the preset map's approximation.

## Experiment schema (canonical — matches target_report.md)
Each experiment is an object with these fields:
`exp_id, title, pillar, surface, url, evidence, hypothesis, primary_change,
primary_kpi, decision_rule, expected_lift, confidence`.

- `evidence` MUST be an artifact path (`pages/.../screenshot.png` / `.../page.html`)
  or a URL — never prose.
- `expected_lift` is a range (e.g. `+8–14%`); `confidence` is a percent (0–100).
- `pillar` is exactly one of: Conversion, AOV, Retention, Acquisition, Performance.

## Reduce (final 10) — coverage-floor + confidence-greedy (D15)
1. **Dedupe** semantically first (two agents may both target the PDP — keep the
   stronger, drop the near-duplicate).
2. **Write all candidates** to `evidence/<run>/report/candidates.json` (a JSON array).
3. **Select + validate in one command** — do NOT hand-write inline `python -c`
   (it breaks on PowerShell quoting and the qcrawl import path). Use the CLI:
   ```
   ./.venv/Scripts/python.exe tools/select.py evidence/<run>/report/candidates.json
   ```
   It applies the coverage-floor selection, assigns `exp_id`s, writes
   `evidence/<run>/report/experiments.json` (next to candidates), prints the
   per-pillar breakdown, and validates — **exit 1 + printed errors** if the set is
   invalid (missing pillar, wrong count, bad evidence). Fix flagged candidates and
   re-run. A pillar that genuinely yielded nothing is a finding — note it rather than
   inventing a weak experiment.

## Hand-off
Pass the validated 10 experiments (+ the run folder, for evidence paths) to the
**write** phase, which renders the final report (executive summary, experiments,
competitor analysis, technical checks).

## Quality bars (non-negotiable)
- **Cite everything** — every claim ties to an artifact path or URL.
- **Diversify pillars** — all 5 represented.
- **Generalize** — reason from the evidence in THIS run; never bake in store-specific
  assumptions from other audits.
