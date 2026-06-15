"""Layers 2b + 4 — the only LLM in the eval, caged into single-question JSON calls.

  - grounded: claim + ONE screenshot -> supported | contradicted | not_visible
  - genericness: experiment -> is this generic best-practice (slop) or store-specific?

Graceful degradation (honesty rule): if `anthropic` isn't installed or
ANTHROPIC_API_KEY isn't set, the judge returns status='unavailable' and the scorer
runs the deterministic layers only — it never fakes a grounding number.
"""
from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path

DEFAULT_MODEL = os.environ.get("EVAL_MODEL", "claude-haiku-4-5-20251001")


def _client():
    try:
        import anthropic
    except ImportError:
        return None
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    return anthropic.Anthropic()


def call_model(prompt: str, image_path=None, model: str = DEFAULT_MODEL, max_tokens: int = 200):
    client = _client()
    if client is None:
        return None
    content = [{"type": "text", "text": prompt}]
    if image_path and Path(image_path).exists():
        data = base64.standard_b64encode(Path(image_path).read_bytes()).decode()
        content.insert(0, {"type": "image",
                           "source": {"type": "base64", "media_type": "image/png", "data": data}})
    msg = client.messages.create(model=model, max_tokens=max_tokens,
                                 messages=[{"role": "user", "content": content}])
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def _json(text):
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.DOTALL)
    try:
        return json.loads(m.group(0)) if m else None
    except json.JSONDecodeError:
        return None


def grounding_check(claim: str, image_path) -> dict | None:
    prompt = ("You are verifying ONE claim against ONE screenshot. Does the image "
              "support the claim? Respond ONLY with JSON: "
              '{"verdict":"supported|contradicted|not_visible","reason":"<=10 words"}'
              f"\n\nClaim: {claim}")
    return _json(call_model(prompt, image_path=image_path))


def genericness(exp: dict):
    masked = {k: exp.get(k) for k in ("hypothesis", "primary_change", "primary_kpi", "decision_rule")}
    prompt = ("Here is a CRO experiment. Could this EXACT experiment apply unchanged to "
              "almost ANY ecommerce store (generic best-practice), or is it specific to "
              "observed evidence on THIS store? Respond ONLY JSON: {\"generic\": true|false}"
              f"\n\n{json.dumps(masked)}")
    r = _json(call_model(prompt))
    return r.get("generic") if r else None


def build_tasks(run: dict) -> dict:
    """Emit the caged judgments for the AGENT to perform (skill path — no API).
    Each grounding task = one claim + one screenshot; each genericness task = one
    masked experiment. The agent writes verdicts; `from_agent_verdicts` folds them in."""
    run_dir = Path(run["run_dir"])
    grounding_tasks, generic_tasks = [], []
    for e in run["experiments"]:
        ev = str(e.get("evidence", ""))
        shot = ev if (ev.endswith(".png") and not ev.startswith("http")) else None
        grounding_tasks.append({
            "exp_id": e.get("exp_id"), "claim": e.get("hypothesis", ""),
            "screenshot": shot, "exists": bool(shot and (run_dir / shot).exists()),
        })
        generic_tasks.append({
            "exp_id": e.get("exp_id"),
            "experiment": {k: e.get(k) for k in ("hypothesis", "primary_change",
                                                 "primary_kpi", "decision_rule")},
        })
    return {"grounding": grounding_tasks, "genericness": generic_tasks}


def from_agent_verdicts(data: dict) -> dict:
    """Compute grounding_precision + specificity from agent-produced verdicts
    (the skill path). Shape: {"verdicts":[{exp_id,verdict}], "generic":[{exp_id,generic}]}."""
    verdicts = [v.get("verdict") for v in data.get("verdicts", []) if v.get("verdict")]
    gens = [bool(g.get("generic")) for g in data.get("generic", []) if g.get("generic") is not None]
    gp = round(sum(v == "supported" for v in verdicts) / len(verdicts), 3) if verdicts else None
    sp = round(1 - sum(gens) / len(gens), 3) if gens else None
    return {"status": "agent", "grounding_precision": gp, "specificity": sp,
            "verdicts": verdicts, "n_grounded": len(verdicts)}


def evaluate(run: dict) -> dict:
    """Optional scripted API path (only if anthropic + key present). The default eval
    path uses the `eval` skill + build_tasks/from_agent_verdicts instead."""
    if _client() is None:
        return {"status": "unavailable", "grounding_precision": None, "specificity": None,
                "note": "Judge is agent-driven via the `eval` skill "
                        "(or install anthropic + set ANTHROPIC_API_KEY for the scripted path)."}
    run_dir = Path(run["run_dir"])
    verdicts, generic_flags = [], []
    for e in run["experiments"]:
        ev = str(e.get("evidence", ""))
        if ev and not ev.startswith("http") and ev.endswith(".png") and (run_dir / ev).exists():
            v = grounding_check(e.get("hypothesis", ""), run_dir / ev)
            if v and v.get("verdict"):
                verdicts.append(v["verdict"])
        g = genericness(e)
        if g is not None:
            generic_flags.append(bool(g))

    grounding_precision = (round(sum(v == "supported" for v in verdicts) / len(verdicts), 3)
                           if verdicts else None)
    specificity = (round(1 - sum(generic_flags) / len(generic_flags), 3)
                   if generic_flags else None)
    return {"status": "ok", "grounding_precision": grounding_precision,
            "specificity": specificity, "verdicts": verdicts, "n_grounded": len(verdicts)}
