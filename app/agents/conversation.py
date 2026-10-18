"""Conversation agent ("the senior engineer"). One entry point: ask()."""
import json
from datetime import date

from agents.prompts import CONVERSATION_PROMPT, JUNIOR_RULES, SENIOR_RULES
from core import kb as kbm
from core.checks import check_citations
from core.llm import chat, parse_json, run_tools
from core.tools import Tools, schemas


def _parse(text):
    try:
        out = parse_json(text)
        if isinstance(out, dict) and "answer" in out:
            return {"answer": str(out["answer"]), "gaps": list(out.get("gaps") or []),
                    "highlight": list(out.get("highlight") or []), "confidence": out.get("confidence", "low")}
    except (ValueError, json.JSONDecodeError):
        pass
    return {"answer": text, "gaps": [], "highlight": [], "confidence": "low"}


def ask(question, history=None, mode="junior", kb=None, on_step=None):
    """-> {answer, gaps, highlight, confidence, trace, check, not_recorded}"""
    kb = kb or kbm.load()
    tools = Tools(kb, mode)
    system = CONVERSATION_PROMPT.format(mode_rules=SENIOR_RULES if mode == "senior" else JUNIOR_RULES,
                                        today=date.today().isoformat())
    messages = [{"role": "system", "content": system}, *(history or []), {"role": "user", "content": question}]
    text, trace, messages = run_tools(messages, schemas(mode), tools.dispatch, on_step=on_step)
    allowed = {c for t in trace for c in t["result"].get("citations", [])}
    out = _parse(text)
    check = check_citations(out["answer"], allowed)

    if not check["ok"]:  # regenerate once, no new tools
        fix = (f"These citations never appeared in a tool result: {check['unknown']}. Valid IDs: {sorted(allowed)}. "
               "Rewrite the same JSON using only valid IDs, [general] or [inference]; drop claims you cannot cite.")
        retry = _parse(chat(messages + [{"role": "assistant", "content": text}, {"role": "user", "content": fix}]).content or "")
        retry_check = check_citations(retry["answer"], allowed)
        if len(retry_check["unknown"]) < len(check["unknown"]):
            out, check = retry, retry_check
        check["regenerated"] = True

    hl = out["highlight"] + [t for s in trace if s["tool"] == "highlight" for t in s["result"]["data"]["highlighted"]]
    not_recorded = [f"{s['tool']}({_args(s['args'])})" for s in trace if s["result"].get("empty") and s["tool"] != "highlight"]
    return out | {"highlight": [t for t in dict.fromkeys(hl) if t in kb["components"]],
                  "trace": trace, "check": check, "not_recorded": not_recorded}


def _args(a):
    return ", ".join(f"{k}={v!r}" for k, v in a.items()) if isinstance(a, dict) else str(a)


def format_text(r):
    """Plain-text rendering for CLI and ASI:One: answer -> how I found this -> gaps -> check."""
    lines = [r["answer"], "", "How I found this:"]
    for s in r["trace"]:
        res = s["result"]
        got = "nothing recorded" if res.get("empty") else ", ".join(res.get("citations", [])) or "ok"
        lines.append(f"  {s['step']}. {s['tool']}({_args(s['args'])}) -> {got}")
    if not r["trace"]:
        lines.append("  (no tool calls)")
    if r["gaps"]:
        lines += ["", "Gaps:"] + [f"  - {g}" for g in r["gaps"]]
    c = r["check"]
    lines += ["", f"Citation check: {'PASS' if c['ok'] else 'FAIL, unverified IDs: ' + ', '.join(c['unknown'])}"
              f" | confidence: {r['confidence']}"]
    return "\n".join(lines)
