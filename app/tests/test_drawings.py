"""Ingested drawing graph must match the corpus answer key (versions/plant_graph_current.json).
Run: .venv/bin/python tests/test_drawings.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from core import kb as kbm
from core.tags import group_loops
from ingest import drawings, revisions
from ingest.drawings import RELATION

truth = json.loads((config.CORPUS_DIR / "versions" / "plant_graph_current.json").read_text())
kb = kbm.empty()
drawings.ingest(kb)
revisions.ingest(kb)

META = {"isa_type", "system_code", "system_seq", "item_code", "first_seq", "legacy_tag"}
want = {n["id"]: n for n in truth["nodes"] if n["type"] != "offpage"}
assert set(kb["components"]) == set(want), set(kb["components"]) ^ set(want)
for t, n in want.items():
    c = kb["components"][t]
    assert (c["kind"], c["desc"], c["sheet"]) == (n["type"], n["label"], n["diagram"]), t
    assert c["attrs"] == {k: v for k, v in n["attrs"].items() if k not in META}, t

offp = {n["id"] for n in truth["nodes"] if n["type"] == "offpage"}
want_links = set()
for e in truth["edges"]:
    if e["from"] in offp or e["to"] in offp:
        continue
    rel, rev = RELATION[e["kind"]]
    want_links.add((e["to"], e["from"], rel) if rev else (e["from"], e["to"], rel))
got_links = {(l["from"], l["to"], l["relation"]) for l in kb["links"]}
assert got_links == want_links, got_links ^ want_links

loops = group_loops(kb["components"], kb["links"])
assert loops["20LFC20CL002"]["members"] == {"20LFC20AA102": "final_element", "20LFC20CL001": "sensor", "20LFC20CL002": "controller"}
assert not [l for l in loops.values() if l["missing"]], "Unit 200 has no incomplete loops"

r5 = next(r for r in kb["revisions"] if r["id"] == "rev:PID-200-5")
assert r5["changes"] == ["20LFC20AA102 fail_position: FO -> FC"] and r5["moc"] == "MOC-2024-031", r5
assert kb["sheets"]["PID-200"]["rev"] == "5" and kb["sheets"]["PID-100"]["rev"] == "3"
# page boxes: every component has one inside its page; CV text boxes (independent OCR of the same PDF) land inside
w, h = kb["sheets"]["PID-100"]["page_size"]
assert all(c["bbox"] and 0 <= c["bbox"][0] < c["bbox"][2] <= w and 0 <= c["bbox"][1] < c["bbox"][3] <= h
           for c in kb["components"].values())
from ingest import cv
cv.ingest(kb)
if "PID-100" in kb["cv"]:
    inside = lambda p, b: b[0] - 3 <= p[0] <= b[2] + 3 and b[1] - 3 <= p[1] <= b[3] + 3
    for tag in ("20LFB10BB001", "20LFB10CF002", "20LFB10CL001"):
        centers = [((d["bbox"][0] + d["bbox"][2]) / 2, (d["bbox"][1] + d["bbox"][3]) / 2) for d in kb["cv"]["PID-100"]["detections"] if d["tag"] == tag]
        assert any(inside(c, kb["components"][tag]["bbox"]) for c in centers), (tag, centers, kb["components"][tag]["bbox"])
    assert {d["suggest"] for d in kb["cv"]["PID-100"]["detections"] if not d["in_kb"]} == {"20LFB10AP002", "20LFB20AA001"}

print(f"drawings ok: {len(kb['components'])} components, {len(kb['links'])} links, {len(loops)} loops, "
      f"{len(kb['revisions'])} revisions")
