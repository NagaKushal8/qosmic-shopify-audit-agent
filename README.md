# Qosmic — Runtime Audit Harness + Eval System

A runtime harness that turns any coding agent (Claude Code / Codex) into the Qosmic
CRO audit agent: **point it at a Shopify URL → a cited audit report**. Plus a
**separate eval harness** that scores any audit report with no golden answer.

Two independent commands, never chained:
- `audit <url>` → produces the report.
- `evaluate evidence/<run>` → scores a finished report.

## Recordings
- **Walkthrough (zenrojas.com):** 

https://github.com/user-attachments/assets/5d1f7d30-ceb2-41ba-80d4-cbc49a999ca9





- **Audit  (zenrojas.com):** <img width="1727" height="530" alt="image" src="https://github.com/user-attachments/assets/56e75d9c-2086-467c-8690-1cda153a54d6" />

- **Eval  (zenrojas.com):** <img width="1546" height="462" alt="Screenshot 2026-06-14 222916" src="https://github.com/user-attachments/assets/effe16e9-25b4-4bcc-a5e8-8bd1186a10c1" />

## Sample output (zenrojas.com — real run)
- Audit report → [`sample_output/zenrojas.com.md`](sample_output/zenrojas.com.md)
- Eval scorecard → [`sample_output/zenrojas.com.eval.json`](sample_output/zenrojas.com.eval.json)
  (judge verdicts: [`…eval-verdicts.json`](sample_output/zenrojas.com.eval-verdicts.json))

---

## 1. The problem & what got done

Build (a) a runtime harness that makes a coding agent act as the Qosmic audit agent
for *any* Shopify store, and (b) an eval system around it. Done in a single
**~4h 45m** session (under the 5h ceiling — see [AGENT_LOG.md](AGENT_LOG.md)).

**On gingerpeople.com (the calibration target):** the store was **down for ~2 days**
and is back up now — but its **Cloudflare is now blocking all automated browsers**. I
tried multiple approaches (realistic UA, Playwright stealth + automation-flag patches,
httpx→browser gate-escalation, a `--proxy` hook) and **could not get past their managed
challenge**, so the harness can't produce a result for gingerpeople.com to compare
against the provided `target_report.md`. The harness reports this honestly
(`status: blocked:challenge`) rather than fabricating.

**So I ran the full pipeline on zenrojas.com instead** — audit + eval, both attached
above. The eval (real numbers): **overall 0.788**, grounding 0.80, specificity 0.90,
structural 1.0, pillar-balance 0.875, **0 hallucinated citations, 0 gates** — and it
flagged real **coverage gaps** (checkout/search/page surfaces captured but not engaged),
which is exactly the actionable signal the self-improvement loop runs on.

## 2. Approach (design, main points)

- **Hybrid harness:** Claude Code **skills** drive reasoning/writing; **deterministic
  Python** (`tools/`) does crawl, digest, tech-checks, assembly. Skill = the manual,
  Python = the machine, agent = the operator.
- **Crawl → evidence:** BFS discovery (no sitemap dependency), robots **polite-only**
  (never a gate — Shopify disallows `/cart` etc.), a **health gate** (abort on
  dead/blocked sites), **stealth + browser escalation** for Cloudflare, and
  **interaction capture** (add-to-cart → cart drawer, popup) so we don't falsely call
  a feature "missing." Every run → `evidence/<domain>_<ts>/` + a `manifest.json`
  citation backbone.
- **Reason:** a deterministic **digest** pre-extracts CRO signals + routes each surface
  to pillars; **5 specialist playbooks** (Conversion/AOV/Retention/Acquisition/
  Performance), each research-backed (Baymard, NN/g, web.dev…), generate experiments
  as **structured JSON**; a coverage-floor + confidence selection picks the final 10.
- **Write = assembly, not an LLM writer:** Python stitches the structured artifacts
  into `report.md`. The LLM only generates *data* — executive summary + competitor
  analysis (web-search-grounded, **honest "unavailable" if no web search**, never
  fabricated). Tech checks are fully deterministic.
- **Structured outputs everywhere** until the final deterministic assembly — prose is
  rendered only at the last step, so the report structure can't drift.
- **Evidence-honest:** tri-state signals (`present`/`absent`/`unverified`); the agent
  may never claim a "missing X" from an unverified signal. Limitations tracked in
  [wherewefail.md](wherewefail.md).

## 3. Evaluation (separate harness)

Scores a report for a store it's never seen, with **no golden answer** — so it's
layered and mostly *not* an LLM:

- **Deterministic (trustworthy floor):** structural (schema/sections/pillar-balance),
  **citation existence** (catches hallucinated evidence), **coverage** (high-value
  surfaces × plausibly-applicable pillars).
- **Caged agent judge:** two narrow single-question verdicts — *does this screenshot
  support this claim* (grounding) and *is this experiment generic slop* (specificity).
- **Gates → vector → scalar:** hallucinated citation / missing pillar / ≠10 **cap** the
  score (no laundering fabricated evidence). The real output is the **vector**; the
  scalar exists only for **ranking**.
- **Relative scoring** (`--compare`) is the improvement engine; **meta-validation**
  (`--validate`) makes a real run out-score a sabotaged copy before you trust it.
- Emits **machine-readable failures** that feed the self-improving loop. Autonomy plan:
  `EVAL_LOOP.md`.

## 4. Key files

| File / dir | What it is |
|---|---|
| [CLAUDE.md](CLAUDE.md) / `AGENTS.md` | Entry point — the audit pipeline + quality bars |
| [decision.md](decision.md) | Every decision + the reasoning behind it (D1–D25) |
| [task.md](task.md) | Task tracker (with the change-trail) |
| [wherewefail.md](wherewefail.md) | Honest known limitations, per phase |
| [AGENT_LOG.md](AGENT_LOG.md) | Time per part, prompts fed, agent-drove-vs-took-the-wheel |
| `EVAL_LOOP.md` | Eval autonomy + self-learning plan |
| `tools/` | Deterministic Python: `crawl` `digest` `tech_checks` `assemble` `select` `eval` (+ `qcrawl/`) |
| `.claude/skills/` | `crawl`, `reason` (+ `playbooks/`), `synthesize`, `eval` |
| `eval/` | The eval harness (layers + scorer + comparator + meta-validation) |
| `schema/` | Structured-output contracts (experiment/summary/competitors) |
| `sample_output/` | The zenrojas.com audit + eval scorecard |

## Run

```powershell
python tools/setup_env.py                 # one-time: pinned venv + Chromium

# deterministic pass (one command)
.\.venv\Scripts\python.exe tools/audit.py https://store.com

# full audit (agent-driven) — say to a coding agent:
#   audit https://store.com
# evaluate a finished run — say:
#   evaluate evidence/<run>

.\.venv\Scripts\python.exe -m pytest      # all test suites
```
