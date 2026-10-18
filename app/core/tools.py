"""Tools: the only way into the knowledge base. Every tool returns {data, citations, empty}."""
import re

from core import kb as kbm
from core.gaps import stated_values
from core.tags import loop_of

VALUE_RE = re.compile(r"\d+(\.\d+)?\s*(%|c\b|barg|bar\b|m3/h|cv\b)|\b(fail[- ]?(open|clos\w*)|FO|FC)\b|\btray\s*\d+|\bcv\s*\d+", re.I)
VALVE_FIELDS = {"Rev", "REVISION NOTE", "TYPE", "Description", "Fluid", "Set Pressure (BARG)", "Fail Position",
                "ACTUATOR TYPE", "VALVE TYPE", "SIZE(DN)", "VALVE RATING", "Line Size", "P&ID"}
STOP = {"the", "a", "an", "of", "on", "in", "is", "for", "to", "which", "what", "and", "or", "it", "that", "this", "does", "do", "why", "how"}


def env(data, citations=(), empty=False):
    return {"data": data, "citations": list(dict.fromkeys(citations)), "empty": empty}


def words(text):
    return {w.rstrip("s") for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP}


def _snip(text, n=240):
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + "…"


class Tools:
    def __init__(self, kb, mode="junior"):
        self.kb, self.mode = kb, mode

    def _comp(self, tag):
        t = (tag or "").strip().upper()
        if t not in self.kb["components"]:  # accept legacy ISA tags (LV-202) via the register
            t = next((k for k, r in self.kb["records"].items() if r.get("legacy") == t), t)
        return self.kb["components"].get(t)

    def _drawing(self, tag):
        return f"drawing:{self.kb['components'][tag]['sheet']}"

    def _mentions(self, tag):
        return [m for m in self.kb["mentions"] if m["tag"] == tag]

    # ---- read tools ----
    def get_component(self, tag):
        c = self._comp(tag)
        if not c:
            return env({"tag": tag, "found": False, "hint": "try find_component with a description"}, empty=True)
        t, rec = c["tag"], self.kb["records"].get(c["tag"])
        data = c | {"register": rec and {k: rec[k] for k in ("legacy", "type", "description", "system")},
                    "counts": {"links": sum(t in (l["from"], l["to"]) for l in self.kb["links"]),
                               "mentions": len(self._mentions(t)),
                               "notes": sum(n["target"] == t for n in self.kb["notes"]),
                               "gaps": sum(t in g["tags"] for g in self.kb["gaps"])}}
        return env(data, [self._drawing(t)] + self._record_cites(t))

    def _record_cites(self, t):
        rec = self.kb["records"].get(t)
        return ([f"register:{t}"] if rec else []) + ([f"valvelist:{t}"] if rec and rec.get("valve_list") else [])

    def find_component(self, description):
        q = words(description)
        hits = []
        for t, c in self.kb["components"].items():
            rec = self.kb["records"].get(t, {})
            if t.lower() in description.lower() or (rec.get("legacy") and re.search(rf"\b{re.escape(rec['legacy'])}\b", description, re.I)):
                hits.append((99, t, "exact tag" + (f" (legacy {rec['legacy']})" if rec.get("legacy") else "")))
                continue
            common = q & words(f"{c['desc']} {rec.get('description', '')} {c['kind'].replace('_', ' ')} "
                               f"{c['decoded'].get('component', '')} {c['decoded'].get('variable', '')}")
            if common:
                hits.append((len(common), t, "matched words: " + ", ".join(sorted(common))))
        hits.sort(key=lambda h: -h[0])
        cands = [{"tag": t, "desc": self.kb["components"][t]["desc"], "reason": r} for _, t, r in hits[:6]]
        return env(cands, [self._drawing(c["tag"]) for c in cands], empty=not cands)

    def get_loop(self, tag):
        t = (tag or "").strip().upper()
        loop = loop_of(t, self.kb["components"], self.kb["links"])
        if not loop:
            return env({"tag": t, "in_loop": False}, empty=True)
        num = loop["loop"]
        members = [{"tag": t, "role": r, "desc": self.kb["components"][t]["desc"]} for t, r in loop["members"].items()]
        return env({"loop": num, "members": members, "missing_roles": loop["missing"]},
                   [self._drawing(m["tag"]) for m in members])

    def get_sheet(self, sheet):
        s = self.kb["sheets"].get(sheet.strip().upper())
        if not s:
            return env({"sheet": sheet, "found": False}, empty=True)
        comps = [{"tag": t, "desc": c["desc"], "kind": c["kind"]} for t, c in self.kb["components"].items() if c["sheet"] == s["id"]]
        off = [o for o in self.kb["offpage"] if s["id"] in (o["from_sheet"], o["to_sheet"])]
        return env({"sheet": s, "components": comps, "offpage": off}, [f"drawing:{s['id']}"])

    def get_neighbors(self, tag):
        c = self._comp(tag)
        if not c:
            return env({"tag": tag, "found": False}, empty=True)
        t, cites, links = c["tag"], [], []
        for l in self.kb["links"]:
            if t in (l["from"], l["to"]):
                fixes = [x for x in self.kb["corrections"] if (x["from"], x["to"]) == (l["from"], l["to"])]
                links.append(l | ({"senior_corrections": fixes} if fixes else {}))
                cites += [l["source"]] + [x["id"] for x in fixes]
        off = [o for o in self.kb["offpage"] if t in (o["from"], o["to"])]
        cites += [f"drawing:{o['from_sheet']}" for o in off]
        return env({"tag": t, "links": links, "offpage": off}, cites, empty=not (links or off))

    def get_protection(self, tag):
        c = self._comp(tag)
        if not c:
            return env({"tag": tag, "found": False}, empty=True)
        t = c["tag"]
        relief = [l["from"] for l in self.kb["links"] if l["to"] == t and l["relation"] == "protects"]
        measuring = [l["from"] for l in self.kb["links"] if l["to"] == t and l["relation"] == "measures"]
        trips = [l["from"] for l in self.kb["links"] if l["to"] == t and l["relation"] == "signal"
                 and self.kb["components"][l["from"]]["kind"] in ("switch", "alarm")]
        alarms = trips + [m for m in measuring if self.kb["components"][m]["kind"] in ("switch", "alarm")]
        data = {"tag": t, "relief_valves": relief, "alarms_switches": alarms,
                "instruments_measuring_it": measuring}
        return env(data, [self._drawing(t)] + [self._drawing(r) for r in relief], empty=not (relief or alarms))

    def search_sources(self, query="", tag=None, kind=None, limit=5):
        q, tag = words(query or ""), (tag or "").strip().upper() or None
        tagged = {m["source_id"] for m in self.kb["mentions"] if m["tag"] == tag} if tag else set()
        in_ctx = {sid for c in self.kb["contexts"].values() if tag in c.get("tags", []) for sid in c["sources"]} if tag else set()
        scored = []
        for sid, s in self.kb["sources"].items():
            if kind and s["kind"] != kind:
                continue
            if tag and not query and sid not in tagged | in_ctx:
                continue
            score = len(q & words(s["text"] + " " + s["title"])) + (3 if sid in tagged else 1 if sid in in_ctx else 0)
            if score:
                scored.append((score, s["date"], sid))
        scored.sort(reverse=True)
        hits = []
        for _, _, sid in scored[:int(limit)]:
            s = self.kb["sources"][sid]
            hits.append({"id": sid, "kind": s["kind"], "author": s["author"], "date": s["date"], "title": s["title"],
                         "snippet": _snip(s["text"]), "context": s.get("context"),
                         "linked_tags": sorted({m["tag"] for m in self.kb["mentions"] if m["source_id"] == sid})})
        return env(hits, [h["id"] for h in hits], empty=not hits)

    def get_source(self, id):
        id = id.strip()
        if id in self.kb["sources"]:
            s = self.kb["sources"][id]
            ctx = self.kb["contexts"].get(s.get("context"), {"sources": [id]})
            items = [{"id": x, "author": self.kb["sources"][x]["author"], "date": self.kb["sources"][x]["date"],
                      "text": self.kb["sources"][x]["text"], "this": x == id} for x in ctx["sources"]]
            links = [{k: m[k] for k in ("tag", "type", "evidence", "anchor", "by")}
                     for m in self.kb["mentions"] if m["source_id"] == id]
            data = s | {"context_title": ctx.get("title"), "context": items, "links": links}
            return env(data, [x["id"] for x in items])
        kind, _, tag = id.partition(":")
        rec = self.kb["records"].get(tag)
        if kind == "register" and rec:
            return env(rec["register"], [id])
        if kind == "valvelist" and rec and rec.get("valve_list"):
            return env({k: v for k, v in rec["valve_list"].items() if v not in ("N/A", "LATER", "")}, [id])
        rev = next((r for r in self.kb["revisions"] + self.kb["gaps"] if r["id"] == id), None)
        if rev:
            return env(rev, [id])
        return env({"id": id, "found": False}, empty=True)

    def get_history(self, tag):
        c = self._comp(tag)
        if not c:
            return env({"tag": tag, "found": False}, empty=True)
        t, events = c["tag"], []
        for m in self._mentions(t):
            if m["type"] in ("change", "decision", "issue", "question"):
                s = self.kb["sources"][m["source_id"]]
                events.append({"date": s["date"], "id": s["id"], "type": m["type"], "author": s["author"],
                               "evidence": m["evidence"], "snippet": _snip(s["text"]),
                               **({"refers_back_to": m["anchor"]} if m.get("anchor") not in (None, s["id"]) else {})})
        for r in self.kb["revisions"]:
            if t in r["tags"]:
                events.append({"date": r["date"], "id": r["id"], "type": "drawing revision", "author": r["author"],
                               "moc": r.get("moc"), "snippet": r["description"],
                               "changes": [c for c in r.get("changes", []) if t in c]})
        events.sort(key=lambda e: e["date"])
        return env({"tag": t, "events": events}, [e["id"] for e in events], empty=not events)

    def compare_records(self, tag):
        """Drawing attrs vs tag register vs valve list, plus sources that state values for this tag."""
        t = (tag or "").strip().upper()
        c, rec = self.kb["components"].get(t), self.kb["records"].get(t)
        if not (c or rec):
            return env({"tag": t, "found": False}, empty=True)
        diffs = []
        if c and not rec:
            diffs.append("on the drawing but not in the tag register")
        if rec and not c:
            diffs.append("in the tag register but on no drawing in the knowledge base")
        if c and rec and rec.get("sheet") and rec["sheet"] != c["sheet"]:
            diffs.append(f"sheet: drawing says {c['sheet']}, valve list says {rec['sheet']}")
        vl = rec and rec.get("valve_list")
        values = [{"id": m["source_id"], "date": self.kb["sources"][m["source_id"]]["date"],
                   "snippet": _snip(self.kb["sources"][m["source_id"]]["text"])}
                  for m in self._mentions(t) if VALUE_RE.search(self.kb["sources"][m["source_id"]]["text"])]
        data = {"tag": t, "drawing": c and {"sheet": c["sheet"], "desc": c["desc"], "attrs": c.get("attrs", {})},
                "register": rec and {k: rec[k] for k in ("legacy", "type", "description")},
                "valve_list": vl and {k: v for k, v in vl.items() if k in VALVE_FIELDS and v not in ("N/A", "LATER", "")},
                "disagreements": diffs, "sources_with_values": values,
                "stated_values": stated_values(self.kb, t) if c else []}
        cites = ([self._drawing(t)] if c else []) + self._record_cites(t) + [v["id"] for v in values]
        return env(data, cites)

    def get_gaps(self, tag=None, sheet=None):
        tag, sheet = (tag or "").strip().upper() or None, (sheet or "").strip().upper() or None
        out = [g for g in self.kb["gaps"]
               if (not tag or tag in g["tags"]) and
               (not sheet or any(self.kb["components"].get(t, {}).get("sheet") == sheet for t in g["tags"]))]
        return env(out, [x for g in out for x in [g["id"], *g["sources"]]], empty=not out)

    def get_notes(self, tag):
        t = (tag or "").strip().upper()
        out = [n for n in self.kb["notes"] if n["target"] == t]
        return env(out, [n["id"] for n in out], empty=not out)

    def highlight(self, tags):
        valid = [t for t in tags if t in self.kb["components"]]
        return env({"highlighted": valid, "unknown": [t for t in tags if t not in valid]})

    # ---- write tools (senior mode only) ----
    def add_note(self, tag, text, author="senior engineer"):
        if not self._comp(tag):
            return env({"error": f"unknown tag {tag}"}, empty=True)
        n = kbm.append_state("notes", {"target": self._comp(tag)["tag"], "author": author, "text": text})
        self.kb["notes"].append(n)
        return env(n, [n["id"]])

    def record_correction(self, from_tag, to_tag, fix, author="senior engineer"):
        f, t = (from_tag or "").upper(), (to_tag or "").upper()
        if not any((l["from"], l["to"]) == (f, t) for l in self.kb["links"]):
            return env({"error": f"no link {f} -> {t}"}, empty=True)
        x = kbm.append_state("corrections", {"from": f, "to": t, "fix": fix, "author": author})
        self.kb["corrections"].append(x)
        return env(x, [x["id"]])

    def flag_issue(self, tags, description, author="senior engineer"):
        bad = [t for t in tags if t not in self.kb["components"]]
        if bad:
            return env({"error": f"unknown tags {bad}"}, empty=True)
        f = kbm.append_state("flags", {"tags": tags, "description": description, "author": author})
        self.kb["gaps"].append(kbm.flag_to_gap(f))
        return env(f, [f["id"]])

    def dispatch(self, name, args):
        if name not in self.allowed():
            raise ValueError(f"tool {name} not available in {self.mode} mode")
        return getattr(self, name)(**args)

    def allowed(self):
        return READ + (WRITE if self.mode == "senior" else [])


def _fn(name, desc, props=None, required=()):
    return {"type": "function", "function": {"name": name, "description": desc, "parameters": {
        "type": "object", "properties": props or {}, "required": list(required)}}}


S = {"type": "string"}
SCHEMAS = [
    _fn("get_component", "Look up a component by exact tag (e.g. V-200, LIC-201): decoded tag, sheet, index record, counts.", {"tag": S}, ["tag"]),
    _fn("find_component", "Find candidate tags for an informal name like 'flash drum', 'spare feed pump', 'sight glass'.", {"description": S}, ["description"]),
    _fn("get_loop", "The control loop a tag belongs to (from signal lines on the drawing): members with roles (sensor/controller/final_element/trip) and missing roles.", {"tag": S}, ["tag"]),
    _fn("get_sheet", "Everything on a P&ID sheet plus off-page connectors.", {"sheet": S}, ["sheet"]),
    _fn("get_neighbors", "Drawing links (flows_to, measures, signal, protects, bypasses) and off-page connectors for a tag, with status and senior corrections.", {"tag": S}, ["tag"]),
    _fn("get_protection", "Relief valves, and trips/alarms (switches signalling it, e.g. low-low level trips) linked to a piece of equipment.", {"tag": S}, ["tag"]),
    _fn("search_sources", "Keyword search over Slack messages, Drive passages and calendar events. With a tag, also returns messages from conversations about that tag even if they don't name it.",
        {"query": S, "tag": S, "kind": {"type": "string", "enum": ["slack", "drive", "calendar"]}, "limit": {"type": "integer"}}),
    _fn("get_source", "Full original text of a source ID (slack-…, drive-…, cal-…, register:…, valvelist:…, rev:…). For Slack/Drive it also returns the whole conversation/document around it, so implicit references ('it', 'that valve') can be read in context.", {"id": S}, ["id"]),
    _fn("get_history", "Dated timeline for a tag: changes, decisions, issues, questions from sources, plus drawing revisions.", {"tag": S}, ["tag"]),
    _fn("compare_records", "Compare drawing attributes vs tag register vs valve list (official values) for a tag, plus sources that state values (set pressure, fail position, setpoint, tray, Cv). Use it to spot conflicts.", {"tag": S}, ["tag"]),
    _fn("get_gaps", "Known gaps/conflicts (missing relief, incomplete loops, record mismatches, unreflected changes). Filter by tag or sheet.", {"tag": S, "sheet": S}),
    _fn("get_notes", "Senior engineer notes for a tag.", {"tag": S}, ["tag"]),
    _fn("highlight", "Highlight these component tags in the UI.", {"tags": {"type": "array", "items": S}}, ["tags"]),
    _fn("add_note", "SENIOR MODE: save a senior engineer note on a tag.", {"tag": S, "text": S}, ["tag", "text"]),
    _fn("record_correction", "SENIOR MODE: record a correction to a drawing link from_tag -> to_tag.", {"from_tag": S, "to_tag": S, "fix": S}, ["from_tag", "to_tag", "fix"]),
    _fn("flag_issue", "SENIOR MODE: flag an issue on tags; it becomes a gap.", {"tags": {"type": "array", "items": S}, "description": S}, ["tags", "description"]),
]
WRITE = ["add_note", "record_correction", "flag_issue"]
READ = [s["function"]["name"] for s in SCHEMAS if s["function"]["name"] not in WRITE]


def schemas(mode="junior"):
    names = READ + (WRITE if mode == "senior" else [])
    return [s for s in SCHEMAS if s["function"]["name"] in names]
