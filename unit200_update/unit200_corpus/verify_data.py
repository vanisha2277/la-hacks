#!/usr/bin/env python3
"""Smoke test for the Unit 200 data. Standard library only, works on Python 3.6+.

    python3 verify_data.py

Checks that every data source is present (including KKS tags and the valve list) and that each of the 12 seed eval questions is
answerable (or correctly NOT answerable) from the data. It does not call any model.
Run it from inside the unit200_corpus folder.
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  (" + detail + ")") if detail else ""))


def need(path):
    p = os.path.join(HERE, path)
    if not os.path.exists(p):
        print("MISSING: %s\nRun this from inside the unit200_corpus folder, and make sure all zips are unzipped there." % path)
        sys.exit(2)
    return p


# ----------------------------------------------------------------------------- load
slack = [json.loads(l) for l in open(need("slack_export/all_messages.jsonl"))]
drive_index = json.load(open(need("drive_export/drive_index.json")))
drive = {}
for m in drive_index:
    drive[m["slug"]] = open(os.path.join(HERE, m["path"])).read().lower()
events = json.load(open(need("calendar_export/events.json")))
graph = json.load(open(need("versions/plant_graph_current.json")))
revs = json.load(open(need("versions/versions_api.json")))["data"]
dxfs = glob.glob(os.path.join(HERE, "dxf", "*.dxf"))
ledger = json.load(open(need("facts_ledger.json")))

slack_text = [m["text"].lower() for m in slack]
drive_lines = [(slug, line) for slug, t in drive.items() for line in t.split("\n")]
nodes = {n["id"] for n in graph["nodes"]}


def in_slack(*tokens):
    return any(all(t in s for t in tokens) for s in slack_text)


def in_drive(slug, *tokens):
    return all(t in drive[slug] for t in tokens)


def anywhere(token):
    return in_slack(token) or any(token in t for t in drive.values())


# ----------------------------------------------------------------------------- inventory
print("== INVENTORY ==")
check("Slack messages", len(slack) >= 200, "%d messages, %s to %s" % (len(slack), slack[0]["date"][:10], slack[-1]["date"][:10]))
check("Slack channels", len(json.load(open(need("slack_export/channels.json")))) == 3)
check("Drive docs + meeting notes", len(drive_index) == 24, "%d files" % len(drive_index))
check("Calendar events", len(events) == 18, "%d events" % len(events))
check("Drawing revisions", len(revs) == 7, "%d revisions, A through 5" % len(revs))
check("DXF drawing files", len(dxfs) == 8, "%d files" % len(dxfs))
check("Current plant graph", len(graph["nodes"]) == 36 and len(graph["edges"]) == 45,
      "%d nodes, %d edges" % (len(graph["nodes"]), len(graph["edges"])))
cross = [e["id"] for e in graph["edges"] if e["attrs"].get("crosses_to")]
check("Cross-diagram links", len(cross) == 3, ", ".join(cross))
check("Calendar notes links resolve",
      all(e["notesFileId"] in {m["fileId"] for m in drive_index} for e in events if e["notesFileId"]))

# ----------------------------------------------------------------------------- seed questions
print("\n== CAN EACH SEED QUESTION BE ANSWERED FROM THE DATA? ==")
q = {x["id"]: x["question"] for x in ledger["seed_eval_questions"]}

check("Q01 " + q["Q01"], in_slack("dry running") and in_slack("20lfc20ap001", "seal") and in_drive("incident_report_2019", "dry running"))
check("Q02 " + q["Q02"], in_drive("moc_2019_021", "20lfc20cl101", "20lfc20aa011", "20lfc20cf101") and in_slack("20lfc20cl101", "20lfc20cf101"))
check("Q03 " + q["Q03"], in_slack("40%", "20lfc20cf002", "manual") and in_drive("handover_notes_dana", "40%"))

# contradictions: both values exist, in DIFFERENT sources
c1 = in_drive("psv_201_datasheet", "17.2") and in_slack("16.5", "20lfc10aa191") and not any("16.5" in t for t in drive.values())
check("Q04 " + q["Q04"] + "  [CONTRADICTION: datasheet 17.2 vs Slack 16.5]", c1)
c2 = (in_drive("moc_2024_031", "fail-closed", "complete 2024-10-21") and in_slack("wo-88213") and in_slack("20lfc20aa102", "fail-open")
      and not any("wo-88213" in t for t in drive.values()))
check("Q05 " + q["Q05"] + "  [CONTRADICTION: MOC says done vs Slack WO-88213]", c2)

check("Q06 " + q["Q06"], in_slack("20lfd10ct101", "55") and in_drive("handover_notes_dana", "20lfd10ct101", "20lfb20aa001") and "20LFB20AA001" in nodes)
check("Q07 " + q["Q07"], in_drive("moc_2023_009", "tray 32", "81") and in_slack("tray 32"))
check("Q08 " + q["Q08"], in_slack("wo-71120") and in_slack("misalign") and in_slack("20lfc20ap002", "preferred") and in_drive("handover_notes_dana", "20lfc20ap002", "30%"))

print("\n== GAPS (agent must say 'no record') ==")
check("Q09 20LFB10AP002 has NO history anywhere in text, only on the drawing",
      not anywhere("20lfb10ap002") and "20LFB10AP002" in nodes)
psv_approval = in_slack("psv", "approv") or in_slack("psv", "moc") or any("20lfc10aa191" in l and "moc" in l for s, l in drive_lines if s != "drawing_register")
check("Q10 No approval/MOC record for the 20LFC10AA191 re-rating", not psv_approval)
near = re.compile(r"20lfc20aa102.{0,15}bypass|bypass.{0,15}20lfc20aa102|bypass line|2 inch|2-inch")
lv_bypass = any(near.search(t) for t in slack_text) or any(near.search(l) for _, l in drive_lines)
check("Q11 Nothing explains the 20LFC20AA102 bypass line", not lv_bypass)
check("Q12 No heat duty figure for 20LFC30AC001 (or any exchanger)",
      not any(re.search(r"\d\s?(kw|mw|btu|gj)", t) for t in slack_text + list(drive.values())))

print("\n== LEDGER TAGS ==")
off_sheet = []
for f in ledger["facts"]:
    for t in f["tags"]:
        if t not in nodes:
            off_sheet.append(t)
check("Every ledger tag is a node in the graph (except off-sheet tags)", set(off_sheet) <= {"20LFD10CT101"},
      "off-sheet: " + ", ".join(sorted(set(off_sheet))) if off_sheet else "")

print("\n== KKS TAGS AND VALVE LIST ==")
kks_re = re.compile(r"\d\d[A-Z]{3}\d\d[A-Z]{2}\d{3}")
real = [n for n in nodes if not n.startswith("OP-")]
check("Every graph node id is a KKS tag (UU+SSS+NN+II+NNN)", all(kks_re.fullmatch(n) for n in real), "%d tags" % len(real))
valves = json.load(open(need("valve_list/unit200_valve_list.json")))
vt = {v["KKS TAG"]: v for v in valves}
check("Valve list tags all exist in the graph", set(vt) <= nodes, "%d valves" % len(vt))
psv = [v for v in valves if v["TYPE"] == "PSV"][0]
lv = [v for v in valves if v["TYPE"] == "LCV"][0]
check("Valve list holds the OFFICIAL values (PSV 17.2, LCV fail close), not the Slack ones",
      psv["Set Pressure (BARG)"] == 17.2 and lv["Fail Position"] == "Fail Close")

passed = sum(results)
print("\n%d of %d checks passed" % (passed, len(results)))
sys.exit(0 if passed == len(results) else 1)
