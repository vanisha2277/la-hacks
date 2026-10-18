"""Runs tests/questions.json through ask() and scores it. Expected sources come from the corpus facts ledger,
read here only (never ingested). Usage: python scripts/eval.py [-k Q04] [-j 4]"""
import argparse
import copy
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from agents.conversation import ask
from core import kb as kbm

ROOT = Path(__file__).resolve().parent.parent
NOT_RECORDED = ("not recorded", "no record", "isn't recorded", "is not recorded", "no documented", "not documented")


def prefixes(ledger_sources):
    """Ledger source names -> citation ID prefixes ('slack:unit200-eng' -> 'slack-unit200-eng-')."""
    out = []
    for s in ledger_sources:
        kind, _, name = s.partition(":")
        if kind == "slack":
            out.append(f"slack-{name}-")
        elif kind in ("drive", "meeting"):
            out.append(f"drive-{name.replace('_stale', '').split('_datasheet')[0]}")
        elif kind == "drawing":
            out.append(f"rev:PID-")  # any drawing revision entry
    return out


def score(case, kb, facts):
    if case.get("inject"):
        kb = copy.deepcopy(kb)
        i = case["inject"]
        kb["sources"][i["id"]] = {"id": i["id"], "kind": "slack", "text": i["text"], "author": i["author"],
                                  "date": i["date"], "title": "#unit200-eng", "link": None, "context": i["id"]}
        kb["contexts"][i["id"]] = {"id": i["id"], "kind": "slack", "title": "injected", "sources": [i["id"]], "tags": [i["tag"]]}
        kb["mentions"].append({"source_id": i["id"], "tag": i["tag"], "type": "change", "by": "regex",
                               "evidence": i["tag"], "anchor": i["id"]})
    r = ask(case["q"], kb=kb)
    text = (r["answer"] + " " + " ".join(r["gaps"])).lower()
    cited = r["check"]["cited"]
    fails = []
    if not r["check"]["ok"]:
        fails.append(f"bad citations {r['check']['unknown']}")
    want = case.get("cite_any") or prefixes(s for f in case.get("ledger", []) for s in facts[f]["sources"])
    if want and not any(c.startswith(w) for c in cited for w in want):
        fails.append(f"cites none of {want}")
    fails += [f"missing '{m}'" for m in case.get("mention", []) if m.lower() not in text]
    if case.get("mention_any") and not any(m.lower() in text for m in case["mention_any"]):
        fails.append(f"mentions none of {case['mention_any']}")
    if case.get("not_recorded") and not any(p in text for p in NOT_RECORDED):
        fails.append("did not say 'not recorded'")
    flagged = any(w in text for w in case.get("flag_words", []))
    fails += [f"repeats '{f}' without flagging it" for f in case.get("forbid_unflagged", []) if f.lower() in text and not flagged]
    return case, fails, len(r["trace"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-k", default="", help="only cases whose id or question contains this")
    ap.add_argument("-j", type=int, default=4)
    a = ap.parse_args()
    ledger = json.loads((config.CORPUS_DIR / "facts_ledger.json").read_text())
    facts = {f["id"]: f for f in ledger["facts"]}
    cases = [c for c in json.loads((ROOT / "tests" / "questions.json").read_text())["cases"]
             if a.k.lower() in (c["id"] + " " + c["q"]).lower()]
    kb = kbm.load()
    with ThreadPoolExecutor(a.j) as ex:
        results = list(ex.map(lambda c: score(c, kb, facts), cases))
    for c, fails, n in results:
        print(f"{'PASS' if not fails else 'FAIL'}  {c['id']:4} {c['kind']:18} ({n:2} calls) {c['q']}"
              + "".join(f"\n        - {f}" for f in fails))
    passed = sum(not f for _, f, _ in results)
    print(f"\n{passed}/{len(results)} passed")
    sys.exit(passed != len(results))
