#!/usr/bin/env python3
"""Eval CLI — score an audit run (no golden answer needed).

    python tools/eval.py evidence/<run>                 # score one run -> eval/results/<run>.json
    python tools/eval.py evidence/<run> --compare evidence/<other>   # relative diff
    python tools/eval.py evidence/<run> --validate      # meta-validate (real > sabotaged)

Deterministic layers (structural, citation-existence, coverage) always run. The LLM
judge (grounding/genericness) runs only if anthropic + ANTHROPIC_API_KEY are present;
otherwise those dims are reported as unavailable (honest, never faked).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

from eval import compare as cmp  # noqa: E402
from eval import coverage, grounding, judge, score, structural, validate_eval  # noqa: E402
from eval.judge import build_tasks  # noqa: E402
from eval.loader import load_run  # noqa: E402


def evaluate_run(run_dir, judge_path=None) -> dict:
    run = load_run(run_dir)
    if judge_path and Path(judge_path).exists():
        judge_result = judge.from_agent_verdicts(json.loads(Path(judge_path).read_text(encoding="utf-8")))
    else:
        judge_result = judge.evaluate(run)  # scripted API path, or 'unavailable'
    ev = {
        "run": Path(run_dir).name,
        "n_experiments": len(run["experiments"]),
        "structural": structural.evaluate(run),
        "citations": grounding.evaluate(run),
        "coverage": coverage.evaluate(run),
        "judge": judge_result,
    }
    ev["score"] = score.score(ev)
    # machine-readable failures (the feedback the loop consumes)
    ev["failures"] = (
        [{"type": "structural", "detail": f} for f in ev["structural"]["fails"]]
        + [{"type": "hallucinated_citation", "detail": f} for f in ev["citations"]["fails"]]
        + [{"type": "coverage_gap", "detail": g} for g in ev["coverage"]["flagged_gaps"]]
    )
    return ev


def _print(ev: dict) -> None:
    sc = ev["score"]
    print(f"\n=== eval: {ev['run']} ===")
    print(f"status: {sc['status']}   scalar: {sc['score']}"
          + ("   (partial — no LLM judge)" if sc["partial_no_llm"] else ""))
    print("vector:")
    for k, v in sc["vector"].items():
        print(f"  {k:22} {v}")
    if sc["gates"]:
        print("GATES (capped):")
        for g in sc["gates"]:
            print(f"  ! {g}")
    if ev["failures"]:
        print(f"failures ({len(ev['failures'])}):")
        for f in ev["failures"][:12]:
            print(f"  - {f['type']}: {f['detail']}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Evaluate a Qosmic audit run.")
    ap.add_argument("run_dir")
    ap.add_argument("--judge", default=None,
                    help="agent-produced verdicts JSON (the `eval` skill writes this)")
    ap.add_argument("--compare", default=None, help="second run dir to diff against")
    ap.add_argument("--validate", action="store_true", help="meta-validate vs a sabotaged copy")
    args = ap.parse_args(argv)

    if not (Path(args.run_dir) / "manifest.json").exists():
        print(f"[eval] no manifest.json in {args.run_dir}", file=sys.stderr)
        return 2

    ev = evaluate_run(args.run_dir, judge_path=args.judge)
    _print(ev)

    results_dir = ROOT / "eval" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out = results_dir / f"{ev['run']}.json"
    out.write_text(json.dumps(ev, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[eval] wrote {out}")

    # If the agent hasn't judged yet, emit the caged tasks for the `eval` skill to do.
    if not args.judge and ev["judge"].get("status") in ("unavailable",):
        tasks = build_tasks(load_run(args.run_dir))
        tasks_out = results_dir / f"{ev['run']}.judge_tasks.json"
        tasks_out.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[eval] judge pending -> agent should judge {tasks_out} "
              f"then re-run with --judge eval/results/{ev['run']}.judge.json")

    if args.validate:
        v = validate_eval.validate(load_run(args.run_dir))
        print(f"\n[meta-validation] {v['message']} (good={v['good_score']} vs bad={v['bad_score']})")
        if not v["passed"]:
            return 1

    if args.compare:
        other = evaluate_run(args.compare)
        diff = cmp.compare(ev, other)
        print(f"\n=== compare: {ev['run']}  ->  {other['run']} ===")
        print(json.dumps(diff, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
