"""Links sources to component tags. Never rewrites content.
1. rules (no AI): explicit KKS tags, legacy ISA tags (via the register), unique description aliases.
2. LLM per context (Slack conversation, Drive doc, calendar event): finds implicit references ("dont fight it")
   and must name an anchor: this item, or an earlier item in the same context that names the component.
   Code keeps a link only if the evidence is verbatim in the item and the anchor checks out."""
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor

import config
from core.kb import ROOT
from core.tags import find_tags

GENERIC = {"valve", "pump", "transmitter", "controller", "indicator", "gauge", "glass", "tank"}
TYPES = ("change", "decision", "issue", "question", "mention")
TYPE_RULES = [  # first match wins; plain heuristics
    ("question", re.compile(r"\?\s*$")),
    ("change", re.compile(r"\b(removed|pulled out|taken out|demolished|decommissioned|replaced|(?<!never )installed?|"
                          r"adding|added|bumped|changed|relocated|moved|rerouted|upgraded|upsized|re-?rated)\b", re.I)),
    ("decision", re.compile(r"\b(approved|decided|agreed|remains|preferred|do not|dont|never)\b", re.I)),
    ("issue", re.compile(r"\b(fouls?|fouled|fouling|sticks?|stuck|fail\w*|leak\w*|passing|trip\w*|hunt\w*|"
                         r"reading (high|low)|out for|broken|never installed|indication only|overfill\w*)\b", re.I)),
]
CACHE = ROOT / "out" / "cache" / "link"
PROMPT_VERSION = "ctx-v1"


def classify(text):
    return next((t for t, rx in TYPE_RULES if rx.search(text)), "mention")


def aliases(kb):
    """alias phrase (lowercase) -> tag, from drawing labels and register descriptions; only unambiguous ones."""
    seen = {}
    for tag, c in kb["components"].items():
        descs = {c["desc"]} | ({kb["records"][tag]["description"]} if tag in kb["records"] else set())
        for d in descs:
            words = re.sub(r"\(.*?\)", "", d).lower().split()
            cands = {" ".join(words)}
            if len(words) >= 3 and words[-1] in GENERIC:
                cands.add(" ".join(words[:-1]))
            for a in cands:
                if find_tags(a.upper()) or (len(a.split()) == 1 and len(a) < 6):
                    continue  # skip labels that embed a tag, and short single words
                seen.setdefault(a, set()).add(tag)
    return {a: next(iter(t)) for a, t in seen.items() if len(t) == 1}


def legacy_map(kb):
    return {r["legacy"]: t for t, r in kb["records"].items() if r.get("legacy")}


def names_in(text, tag, kb, alias_map, legacy):
    """Does text explicitly name tag (KKS, legacy tag, or unique alias)?"""
    if tag in text or any(l in text for l, t in legacy.items() if t == tag):
        return True
    return any(t == tag and re.search(r"\b" + re.escape(a) + r"\b", text, re.I) for a, t in alias_map.items())


def verbatim(evidence, text):
    norm = lambda s: " ".join(s.lower().split())
    return bool(evidence.strip()) and norm(evidence) in norm(text)


def _have(kb):
    return {(m["source_id"], m["tag"]) for m in kb["mentions"]}


def link_rules(kb):
    alias_map, legacy, have = aliases(kb), legacy_map(kb), _have(kb)

    def add(sid, tag, by, evidence):
        if (sid, tag) not in have:
            have.add((sid, tag))
            kb["mentions"].append({"source_id": sid, "tag": tag, "type": classify(kb["sources"][sid]["text"]),
                                   "by": by, "evidence": evidence, "anchor": sid})

    for sid, s in kb["sources"].items():
        for tag in find_tags(s["text"]):
            if tag in kb["components"]:
                add(sid, tag, "regex", tag)
            elif tag in legacy and legacy[tag] in kb["components"]:
                add(sid, legacy[tag], "legacy", tag)
        for a, tag in alias_map.items():
            if m := re.search(r"\b" + re.escape(a) + r"\b", s["text"], re.I):
                add(sid, tag, "alias", m.group(0))


def _ask(kb, ctx, tags_text):
    from agents.prompts import LINKER_PROMPT
    from core.llm import chat_json
    items = [{"id": sid, "author": kb["sources"][sid]["author"], "text": kb["sources"][sid]["text"]} for sid in ctx["sources"]]
    payload = json.dumps({"title": ctx["title"], "items": items})
    key = hashlib.sha256(f"{PROMPT_VERSION}|{config.MODEL_HEAVY}|{tags_text}|{payload}".encode()).hexdigest()[:24]
    path = CACHE / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text()), True
    out = chat_json([{"role": "system", "content": LINKER_PROMPT.format(tags=tags_text)},
                     {"role": "user", "content": payload}], model=config.MODEL_HEAVY)
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out))
    return out, False


def link_llm(kb, workers=4):
    """One LLM call per context (cached by content hash). Returns stats."""
    alias_map, legacy = aliases(kb), legacy_map(kb)
    tags_text = "\n".join(f"{t}: {c['desc']}" + (f" (legacy {kb['records'][t]['legacy']}; {kb['records'][t]['description'].lower()})"
                                                  if t in kb["records"] else "") for t, c in kb["components"].items())
    stats = {"calls": 0, "cached": 0, "failed": 0, "added": 0, "context_links": 0, "rejected": 0}

    def run(ctx):
        try:
            return ctx, *_ask(kb, ctx, tags_text)
        except Exception as e:
            print(f"  linker {ctx['id']} failed: {e}")
            return ctx, None, False

    have = _have(kb)
    with ThreadPoolExecutor(workers) as ex:
        for ctx, out, cached in ex.map(run, kb["contexts"].values()):
            if out is None:
                stats["failed"] += 1
                continue
            stats["cached" if cached else "calls"] += 1
            order = {sid: i for i, sid in enumerate(ctx["sources"])}
            for l in out if isinstance(out, list) else []:
                sid, tag, ev, anchor = l.get("id"), l.get("tag"), l.get("evidence", ""), l.get("anchor") or l.get("id")
                ok = (sid in order and tag in kb["components"] and anchor in order and order[anchor] <= order[sid]
                      and verbatim(ev, kb["sources"][sid]["text"])
                      and (anchor == sid or names_in(kb["sources"][anchor]["text"], tag, kb, alias_map, legacy)))
                if not ok:
                    stats["rejected"] += 1
                    continue
                if (sid, tag) in have:
                    continue
                have.add((sid, tag))
                by = "llm" if anchor == sid else "llm-context"
                kb["mentions"].append({"source_id": sid, "tag": tag, "by": by, "evidence": ev, "anchor": anchor,
                                       "type": l.get("type") if l.get("type") in TYPES else "mention"})
                stats["added"] += 1
                stats["context_links"] += by == "llm-context"
    return stats


def tag_contexts(kb):
    """Retrieval layer: a context is tagged with every tag linked anywhere in it."""
    by_source = {}
    for m in kb["mentions"]:
        by_source.setdefault(m["source_id"], set()).add(m["tag"])
    for ctx in kb["contexts"].values():
        ctx["tags"] = sorted(set().union(*(by_source.get(s, set()) for s in ctx["sources"])))


if __name__ == "__main__":
    kb = {"components": {"20LFC20AP001": {"desc": "Reflux Pump A"}, "20LFC20AP002": {"desc": "Reflux Pump B"},
                         "20LFC20BB001": {"desc": "Reflux Drum"}, "20LFC30AC001": {"desc": "Reboiler"},
                         "20LFC20AA102": {"desc": "20LFC20BB001 Product Level Valve"}},
          "records": {"20LFC20AA102": {"legacy": "LV-202", "description": "REFLUX DRUM PRODUCT LEVEL CONTROL VALVE"}}}
    a = aliases(kb)
    assert a["reflux drum"] == "20LFC20BB001" and a["reboiler"] == "20LFC30AC001", a
    assert a["reflux drum product level control"] == "20LFC20AA102" and "20lfc20bb001 product level valve" not in a
    assert names_in("LV-202 went wide open", "20LFC20AA102", kb, a, legacy_map(kb))
    assert not names_in("dont fight it", "20LFC20AA102", kb, a, legacy_map(kb))
    assert classify("we pulled out the bypass") == "change" and classify("is it hunting?") == "question"
    assert verbatim("dont  fight it", "yes. intentional. Dont fight it") and not verbatim("", "x")
    print("linker ok")
