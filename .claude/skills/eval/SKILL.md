---
name: eval
description: >-
  Score a finished audit run with no golden answer — deterministic layers (Python)
  plus agent-judged grounding + genericness. Use it as "evaluate evidence/<run>".
  Output: a per-dimension vector + gates + scalar + machine-readable failures.
---

# Evaluate an audit run

You are the eval harness. Input: a completed run folder (`evidence/<run>/` with
`report/experiments.json` + `manifest.json` + screenshots). The deterministic layers
are Python; **you personally perform the two caged LLM judgments** (no API key needed).

## Step 1 — deterministic layers + get the judge tasks
```
./.venv/Scripts/python.exe tools/eval.py evidence/<run>
```
This runs structural / citation-existence / coverage + gates, writes
`eval/results/<run>.json`, and — because the judge is pending — writes
`eval/results/<run>.judge_tasks.json` listing what you must judge.

## Step 2 — do the caged judgments YOURSELF (this is the skill replacing the API)
Read `eval/results/<run>.judge_tasks.json`. Two narrow jobs — keep each to ONE
question, never vibe-score the whole report:

- **Grounding** — for each grounding task: open the `screenshot`, and decide whether it
  supports the `claim`. Verdict ∈ `supported | contradicted | not_visible`. If you
  can't see it, say `not_visible` — never invent support.
- **Genericness** — for each genericness task: could this EXACT experiment apply
  unchanged to almost any ecommerce store (generic best-practice = slop), or is it
  specific to observed evidence? `generic ∈ true | false`.

Write `eval/results/<run>.judge.json`:
```json
{
  "verdicts": [{"exp_id": "exp-…", "verdict": "supported"}, ...],
  "generic":  [{"exp_id": "exp-…", "generic": false}, ...]
}
```

## Step 3 — fold judgments in for the final score
```
./.venv/Scripts/python.exe tools/eval.py evidence/<run> --judge eval/results/<run>.judge.json
```
Now the vector includes `grounding_precision` + `specificity`, and the weighted scalar
is complete. Report the **vector** (that's the real output), the gates, and the failures.

## Optional
- `--validate` — meta-validation: a real run must out-score a sabotaged copy. Run this
  before trusting the eval on a new store.
- `--compare evidence/<other>` — relative scoring (v1 vs v2 / store vs store) — the
  self-improvement engine; absolute scores are meaningless without a golden answer.

## Rules
- The vector is the deliverable, not the scalar. Gates (hallucinated citation / missing
  pillar / ≠10) cap the score — fabricated evidence can't be averaged away.
- Be honest: `not_visible` over guessed `supported`; the eval's value is that it
  catches slop, including your own.
