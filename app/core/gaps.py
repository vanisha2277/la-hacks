"""Deterministic gap and conflict detection. Plain code, no AI."""
import re

from core.tags import group_loops

REMOVAL = re.compile(r"\b(removed|pulled out|taken out|demolished|decommissioned|ripped out|blinded off)\b", re.I)
VESSEL_KINDS = {"vessel", "column"}
EQUIPMENT_KINDS = {"vessel", "column", "pump", "heat_exchanger", "tank", "compressor"}
INSTRUMENT_KINDS = {"transmitter", "controller", "control_valve", "switch", "alarm", "relief_valve"}


# ponytail: regex per quantity; swap to LLM extraction if real phrasing defeats it
NUM = r"(\d+(?:\.\d+)?)"
QUANTITIES = {  # drawing attr -> (unit regex appended to a number, or None for word values)
    "set_pressure_barg": r"\s*barg\b",
    "setpoint_c": r"\s*(?:°\s*)?C\b",
    "tray": None, "cv": None, "fail_position": None,
}
PREFIX = {"tray": r"\btray\s*", "cv": r"\bcv\s*"}
FAIL = [(re.compile(r"\bfail(?:s|ed)?[- ]?open\b|\bFO\b|wide open on loss of air", re.I), "FO"),
        (re.compile(r"\bfail(?:s|ed)?[- ]?clos\w*|\bFC\b", re.I), "FC")]
TO = r"\s*(?:to|->|→)\s*"


def stated_value(attr, text):
    """The single value text states for attr, or None. 'from A to B' states B."""
    if attr == "fail_position":
        hits = sorted((m.start(), v) for rx, v in FAIL for m in rx.finditer(text))
        if not hits:
            return None
        vals = {v for _, v in hits}
        if len(vals) == 1:
            return vals.pop()
        return hits[-1][1] if re.search(r"(open|FO)\W*\s*(to|->)\s*\W*(fail|FC)", text, re.I) else None
    pre, unit = PREFIX.get(attr, ""), QUANTITIES[attr] or ""
    one = pre + NUM + unit
    m = re.search(pre + NUM + f"(?:{unit})?" + TO + "(?:" + pre.replace("\\b", "") + ")?" + NUM + unit, text, re.I)
    if m:
        return float(m.group(2))
    vals = {float(x) for x in re.findall(one, text, re.I)}
    return vals.pop() if len(vals) == 1 else None


def _relevant_text(kb, m):
    s = kb["sources"][m["source_id"]]
    if s["kind"] != "drive":
        return s["text"]  # short messages / events
    keys = [m["tag"], m.get("evidence") or m["tag"]]
    return "\n".join(l for l in s["text"].splitlines() if any(k.lower() in l.lower() for k in keys))


def effective_since(kb, tag, attr):
    """Date the drawing's current value of attr took effect: last revision that changed it, else first issue."""
    changed = [r["date"] for r in kb["revisions"] if any(c.startswith(f"{tag} {attr}:") for c in r.get("changes", []))]
    if changed:
        return max(changed)
    sheet = kb["components"][tag]["sheet"]
    return min(r["date"] for r in kb["revisions"] if r["sheet"] == sheet)


def stated_values(kb, tag):
    """Every value a linked source states for one of tag's drawing attributes."""
    attrs = {a: v for a, v in kb["components"][tag].get("attrs", {}).items() if a in QUANTITIES}
    out = []
    for m in kb["mentions"]:
        if m["tag"] != tag:
            continue
        text = _relevant_text(kb, m)
        for a, official in attrs.items():
            v = stated_value(a, text)
            if v is not None:
                agree = v == official or (isinstance(official, (int, float)) and abs(v - official) < 1e-9)
                out.append({"id": m["source_id"], "date": kb["sources"][m["source_id"]]["date"], "attr": a,
                            "value": v, "drawing_value": official, "agrees": agree})
    return out


def value_conflicts(kb):
    found = []
    for tag, c in kb["components"].items():
        for a in {v["attr"] for v in stated_values(kb, tag)}:
            since = effective_since(kb, tag, a)
            vals = [v for v in stated_values(kb, tag) if v["attr"] == a]
            newer_bad = [v for v in vals if not v["agrees"] and v["date"] > since]
            if newer_bad:
                agree = [v for v in vals if v["agrees"]]
                found.append((tag, a, c["attrs"][a], since, newer_bad, agree))
    return found


def run(kb):
    comps, gaps = kb["components"], []

    def gap(type_, severity, tags, issue, sources):
        gaps.append({"id": f"gap-{len(gaps) + 1:03d}", "type": type_, "severity": severity,
                     "tags": tags, "issue": issue, "sources": list(dict.fromkeys(sources))})

    drawing = lambda tag: f"drawing:{comps[tag]['sheet']}"

    for name, loop in group_loops(comps, kb["links"]).items():
        if loop["missing"]:
            members = list(loop["members"])
            gap("incomplete_loop", "high", members,
                f"Loop {name} ({', '.join(members)}) has no {' or '.join(loop['missing'])} on the drawing.",
                [drawing(t) for t in members])

    for tag, a, official, since, bad, agree in value_conflicts(kb):
        vl = kb["records"].get(tag, {}).get("valve_list")
        others = "; ".join(f"{v['id']} ({v['date'][:10]}) says {v['value']}" for v in bad)
        support = [v["id"] for v in agree]
        gap("value_conflict", "high", [tag],
            f"{tag} {a.replace('_', ' ')}: the drawing says {official} (current since {since[:10]})"
            + (", as does the valve list" if vl else "") + (f" and {len(support)} other source(s)" if support else "")
            + f"; but {others}. A newer source states a different value than the drawing.",
            [drawing(tag)] + ([f"valvelist:{tag}"] if vl else []) + [v["id"] for v in bad] + support[-2:])

    protected = {l["to"] for l in kb["links"] if l["relation"] == "protects"}
    for tag, c in comps.items():
        if c["kind"] in VESSEL_KINDS and tag not in protected:
            gap("unprotected_vessel", "medium", [tag],
                f"{tag} ({c['desc']}): no relief device shown on the drawing.", [drawing(tag)])

    by_source = {}
    for m in kb["mentions"]:
        by_source.setdefault(m["source_id"], []).append(m)
    for sid, ms in by_source.items():
        if REMOVAL.search(kb["sources"][sid]["text"]):
            for m in ms:
                if m["type"] == "change":
                    gap("change_not_reflected", "high", [m["tag"]],
                        f"{sid} reports removal/replacement of {m['tag']} (\"{m['evidence']}\"), "
                        f"but the drawing still shows it.", [sid, drawing(m["tag"])])

    for tag, r in kb["records"].items():
        if tag not in comps:
            gap("index_not_on_drawing", "medium", [tag],
                f"{tag} ({r['description'].lower()}) is in the tag register but on no drawing in the knowledge base.", [f"register:{tag}"])
        elif r.get("sheet") and r["sheet"] != comps[tag]["sheet"]:
            gap("index_sheet_mismatch", "medium", [tag],
                f"Valve list puts {tag} on {r['sheet']}; the drawing shows it on {comps[tag]['sheet']}.",
                [f"valvelist:{tag}", drawing(tag)])
    for tag, c in comps.items():
        if kb["records"] and c["kind"] in INSTRUMENT_KINDS and tag not in kb["records"]:
            gap("drawing_not_in_index", "medium", [tag],
                f"{tag} ({c['desc']}) is on the drawing but missing from the tag register.", [drawing(tag)])

    for o in kb["offpage"]:
        if o["to_sheet"] and o["to_sheet"] not in kb["sheets"]:
            gap("dangling_offpage", "medium", [o["from"]],
                f"Off-page connector from {o['from']} ({o['from_sheet']}) goes to {o['to_sheet']} ({o['label']}), "
                f"which is not in the knowledge base.", [f"drawing:{o['from_sheet']}"])

    for l in kb["links"]:
        if l["status"] == "inferred":
            gap("unverified_link", "low", [l["from"], l["to"]],
                f"Link {l['from']} {l['relation']} {l['to']} is inferred, not verified on the drawing.", [l["source"]])

    mentioned = {m["tag"] for m in kb["mentions"]}
    for tag, c in comps.items():
        # ponytail: equipment only, instruments would flood the list; widen if seniors want it
        if c["kind"] in EQUIPMENT_KINDS and tag not in mentioned:
            gap("undocumented", "low", [tag], f"No Slack/Drive source mentions {tag} ({c['desc']}).", [drawing(tag)])

    order = {"high": 0, "medium": 1, "low": 2}
    return sorted(gaps, key=lambda g: order[g["severity"]])
