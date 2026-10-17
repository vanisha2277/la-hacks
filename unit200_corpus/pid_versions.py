#!/usr/bin/env python3
"""Generate the synthetic P&ID revision history for Harbor Unit 200.

Output (in ./versions):
  rev_<ID>.json        full graph snapshot at that revision (both diagrams)
  versions_api.json    revision list shaped like a document-versions API response
  plant_graph_current.json   latest snapshot
  changelog.json       per-revision diff (added/changed nodes and edges)

The 2021 PSV-201 re-rating is intentionally NOT a revision, so the drawing keeps
set_pressure_barg = 17.2 while Slack says 16.5 (contradiction C01).
LV-202 is set to FC in Rev 5, while Slack says the field is still FO (contradiction C02).
"""
import copy
import json
import os
import sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "versions")

# ---------------------------------------------------------------- base graph (Rev A)
def n(id, type, label, diagram, **attrs):
    return {"id": id, "type": type, "label": label, "diagram": diagram, "attrs": attrs}

def e(id, src, dst, kind, line, diagram, **attrs):
    return {"id": id, "from": src, "to": dst, "kind": kind, "line": line,
            "diagram": diagram, "attrs": attrs}

BASE_NODES = [
    # PID-100 Feed and Preheat
    n("OP-FEED-IN", "offpage", "Feed from battery limit", "PID-100"),
    n("V-101", "vessel", "Feed Surge Drum", "PID-100", service="C3/C4 mixed feed"),
    n("P-101A", "pump", "Feed Pump A", "PID-100", duty="running"),
    n("P-101B", "pump", "Feed Pump B", "PID-100", duty="standby"),
    n("FT-101", "transmitter", "Feed Flow Transmitter", "PID-100"),
    n("FIC-101", "controller", "Feed Flow Controller", "PID-100"),
    n("FV-101", "control_valve", "Feed Flow Control Valve", "PID-100", fail_position="FC"),
    n("LT-101", "transmitter", "V-101 Level Transmitter", "PID-100"),
    n("E-101", "heat_exchanger", "Feed/Bottoms Exchanger", "PID-100"),
    # PID-200 Column and Overhead
    n("C-101", "column", "C3/C4 Splitter", "PID-200", trays=55),
    n("E-102", "heat_exchanger", "Overhead Condenser", "PID-200", utility="cooling water"),
    n("V-102", "vessel", "Reflux Drum", "PID-200"),
    n("P-102A", "pump", "Reflux Pump A", "PID-200", duty="running"),
    n("P-102B", "pump", "Reflux Pump B", "PID-200", duty="standby"),
    n("E-103", "heat_exchanger", "Reboiler", "PID-200", utility="steam"),
    n("FT-201", "transmitter", "Reflux Flow Transmitter", "PID-200"),
    n("FIC-201", "controller", "Reflux Flow Controller", "PID-200"),
    n("FV-201", "control_valve", "Reflux Control Valve", "PID-200", cv=45, fail_position="FC"),
    n("TT-203", "transmitter", "Column Temperature Transmitter", "PID-200", tray=28),
    n("TIC-203", "controller", "Column Temperature Controller", "PID-200", setpoint_c=78),
    n("TV-203", "control_valve", "Reboiler Steam Valve", "PID-200", fail_position="FC"),
    n("PT-201", "transmitter", "Column Pressure Transmitter", "PID-200"),
    n("PIC-201", "controller", "Column Pressure Controller", "PID-200"),
    n("PV-201", "control_valve", "Condenser Cooling Water Valve", "PID-200", fail_position="FO"),
    n("LT-202", "transmitter", "V-102 Level Transmitter", "PID-200"),
    n("LIC-202", "controller", "V-102 Level Controller", "PID-200"),
    n("LV-202", "control_valve", "V-102 Product Level Valve", "PID-200", fail_position="FO"),
    n("PSV-201", "relief_valve", "Column Relief Valve", "PID-200", set_pressure_barg=17.2),
    n("OP-C3-PRODUCT", "offpage", "Propane product", "PID-200"),
    n("OP-STORAGE", "offpage", "Butane to storage (PID-300)", "PID-100"),
]

BASE_EDGES = [
    # process, PID-100
    e("L1001", "OP-FEED-IN", "V-101", "process", '6"-C3C4-1001', "PID-100"),
    e("L1002A", "V-101", "P-101A", "process", '6"-C3C4-1002', "PID-100"),
    e("L1002B", "V-101", "P-101B", "process", '6"-C3C4-1002', "PID-100"),
    e("L1003A", "P-101A", "FV-101", "process", '4"-C3C4-1003', "PID-100"),
    e("L1003B", "P-101B", "FV-101", "process", '4"-C3C4-1003', "PID-100"),
    e("L1004", "FV-101", "E-101", "process", '4"-C3C4-1004', "PID-100"),
    # cross-diagram: E-101 to column feed, and bottoms back through E-101
    e("L1005", "E-101", "C-101", "process", '4"-C3C4-1005', "PID-100", crosses_to="PID-200"),
    e("L1042", "C-101", "E-101", "process", '4"-C4-1042', "PID-200", crosses_to="PID-100"),
    e("L1043", "E-101", "OP-STORAGE", "process", '4"-C4-1043', "PID-100"),
    # process, PID-200
    e("L2001", "C-101", "E-102", "process", '12"-C3-2001', "PID-200"),
    e("L2002", "E-102", "V-102", "process", '10"-C3-2002', "PID-200"),
    e("L2003A", "V-102", "P-102A", "process", '4"-C3-2003', "PID-200"),
    e("L2003B", "V-102", "P-102B", "process", '4"-C3-2003', "PID-200"),
    e("L2004A", "P-102A", "FV-201", "process", '3"-C3-2004', "PID-200"),
    e("L2004B", "P-102B", "FV-201", "process", '3"-C3-2004', "PID-200"),
    e("L2005", "FV-201", "C-101", "process", '3"-C3-2005', "PID-200"),
    e("L2006", "V-102", "LV-202", "process", '2"-C3-2006', "PID-200"),
    e("L2007", "LV-202", "OP-C3-PRODUCT", "process", '2"-C3-2007', "PID-200"),
    e("L2008", "C-101", "E-103", "process", '10"-C4-2008', "PID-200"),
    e("L2009", "E-103", "C-101", "process", '10"-C4-2009', "PID-200"),
    e("L2010", "C-101", "PSV-201", "relief", '6"-REL-2010', "PID-200"),
    # utilities
    e("U2001", "TV-203", "E-103", "utility", '3"-STM-2011', "PID-200"),
    e("U2002", "PV-201", "E-102", "utility", '6"-CW-2012', "PID-200"),
    # impulse (sensing) lines
    e("I1001", "V-101", "LT-101", "impulse", "impulse V-101 to LT-101", "PID-100"),
    e("I2001", "V-102", "LT-202", "impulse", "impulse V-102 to LT-202", "PID-200"),
    e("I2002", "C-101", "TT-203", "impulse", "impulse C-101 to TT-203", "PID-200"),
    e("I2003", "C-101", "PT-201", "impulse", "impulse C-101 to PT-201", "PID-200"),
    # signals, PID-100
    e("S1001", "FT-101", "FIC-101", "signal", "FT-101 to FIC-101", "PID-100"),
    e("S1002", "FIC-101", "FV-101", "signal", "FIC-101 to FV-101", "PID-100"),
    # signals, PID-200
    e("S2001", "FT-201", "FIC-201", "signal", "FT-201 to FIC-201", "PID-200"),
    e("S2002", "FIC-201", "FV-201", "signal", "FIC-201 to FV-201", "PID-200"),
    e("S2003", "TT-203", "TIC-203", "signal", "TT-203 to TIC-203", "PID-200"),
    e("S2004", "TIC-203", "TV-203", "signal", "TIC-203 to TV-203", "PID-200"),
    e("S2005", "PT-201", "PIC-201", "signal", "PT-201 to PIC-201", "PID-200"),
    e("S2006", "PIC-201", "PV-201", "signal", "PIC-201 to PV-201", "PID-200"),
    e("S2007", "LT-202", "LIC-202", "signal", "LT-202 to LIC-202", "PID-200"),
    e("S2008", "LIC-202", "LV-202", "signal", "LIC-202 to LV-202", "PID-200"),
]

# ---------------------------------------------------------------- revisions
# ops: ("add_node", node) | ("add_edge", edge) | ("remove_edge", edge_id) | ("set_attr", node_id, key, value)
REVISIONS = [
    {"rev": "A", "date": "2017-09-12", "author": "Dana Okafor", "moc": None,
     "comment": "Issued for design", "diagrams": ["PID-100", "PID-200"], "ops": []},
    {"rev": "0", "date": "2018-06-20", "author": "Dana Okafor", "moc": None,
     "comment": "As-built after commissioning. Added PSL-101 auto-start for standby feed pump.",
     "diagrams": ["PID-100"],
     "ops": [
         ("add_node", n("PSL-101", "switch", "Feed Pump Low Discharge Pressure Switch", "PID-100")),
         ("add_edge", e("S1003", "PSL-101", "P-101B", "signal", "PSL-101 auto-start P-101B", "PID-100")),
     ]},
    {"rev": "1", "date": "2019-12-02", "author": "Dana Okafor", "moc": "MOC-2019-021",
     "comment": "Post-incident corrective actions: reflux pump low-low level trip, discharge check valves, reflux low-flow alarm.",
     "diagrams": ["PID-200"],
     "ops": [
         ("add_node", n("LSLL-202", "switch", "V-102 Low-Low Level Trip", "PID-200", trips="P-102A, P-102B")),
         ("add_node", n("CV-102A", "check_valve", "P-102A Discharge Check Valve", "PID-200")),
         ("add_node", n("CV-102B", "check_valve", "P-102B Discharge Check Valve", "PID-200")),
         ("add_node", n("FAL-201", "alarm", "Reflux Low Flow Alarm", "PID-200")),
         ("add_edge", e("S2009", "LSLL-202", "P-102A", "signal", "LSLL-202 trip P-102A", "PID-200")),
         ("add_edge", e("S2010", "LSLL-202", "P-102B", "signal", "LSLL-202 trip P-102B", "PID-200")),
         ("add_edge", e("S2011", "FT-201", "FAL-201", "signal", "FT-201 to FAL-201", "PID-200")),
         ("remove_edge", "L2004A"),
         ("remove_edge", "L2004B"),
         ("add_edge", e("L2004A1", "P-102A", "CV-102A", "process", '3"-C3-2004', "PID-200")),
         ("add_edge", e("L2004A2", "CV-102A", "FV-201", "process", '3"-C3-2004', "PID-200")),
         ("add_edge", e("L2004B1", "P-102B", "CV-102B", "process", '3"-C3-2004', "PID-200")),
         ("add_edge", e("L2004B2", "CV-102B", "FV-201", "process", '3"-C3-2004', "PID-200")),
         ("set_attr", "P-102A", "check_valve", "CV-102A"),
         ("set_attr", "P-102B", "check_valve", "CV-102B"),
     ]},
    {"rev": "2", "date": "2020-08-18", "author": "Dana Okafor", "moc": "MOC-2020-014",
     "comment": "FV-201 trim upsized for higher feed rate.",
     "diagrams": ["PID-200"],
     "ops": [("set_attr", "FV-201", "cv", 75)]},
    {"rev": "3", "date": "2022-03-09", "author": "Dana Okafor", "moc": "MOC-2022-007",
     "comment": "Added bypass BV-101 around E-101 to maintain feed temperature during fouling.",
     "diagrams": ["PID-100"],
     "ops": [
         ("add_node", n("BV-101", "manual_valve", "E-101 Bypass Valve", "PID-100")),
         ("add_edge", e("L1004B", "FV-101", "BV-101", "process", '4"-C3C4-1004B', "PID-100")),
         ("add_edge", e("L1005B", "BV-101", "C-101", "process", '4"-C3C4-1005B', "PID-100", crosses_to="PID-200")),
     ]},
    {"rev": "4", "date": "2023-05-22", "author": "Priya Raman", "moc": "MOC-2023-009",
     "comment": "TT-203 relocated from tray 28 to tray 32. TIC-203 setpoint updated.",
     "diagrams": ["PID-200"],
     "ops": [
         ("set_attr", "TT-203", "tray", 32),
         ("set_attr", "TIC-203", "setpoint_c", 81),
     ]},
    {"rev": "5", "date": "2024-10-14", "author": "Dana Okafor", "moc": "MOC-2024-031",
     "comment": "LV-202 fail position changed from FO to FC after V-102 overfill near-miss.",
     "diagrams": ["PID-200"],
     "ops": [("set_attr", "LV-202", "fail_position", "FC")]},
]

# ---------------------------------------------------------------- engine
def apply_ops(graph, ops):
    changes = {"added_nodes": [], "added_edges": [], "removed_edges": [], "changed_attrs": []}
    nodes = {x["id"]: x for x in graph["nodes"]}
    edges = {x["id"]: x for x in graph["edges"]}
    for op in ops:
        kind = op[0]
        if kind == "add_node":
            node = copy.deepcopy(op[1])
            assert node["id"] not in nodes, "duplicate node " + node["id"]
            graph["nodes"].append(node)
            nodes[node["id"]] = node
            changes["added_nodes"].append(node["id"])
        elif kind == "add_edge":
            edge = copy.deepcopy(op[1])
            assert edge["id"] not in edges, "duplicate edge " + edge["id"]
            assert edge["from"] in nodes and edge["to"] in nodes, "dangling edge " + edge["id"]
            graph["edges"].append(edge)
            edges[edge["id"]] = edge
            changes["added_edges"].append(edge["id"])
        elif kind == "remove_edge":
            eid = op[1]
            assert eid in edges, "unknown edge " + eid
            graph["edges"] = [x for x in graph["edges"] if x["id"] != eid]
            del edges[eid]
            changes["removed_edges"].append(eid)
        elif kind == "set_attr":
            _, node_id, key, value = op
            assert node_id in nodes, "unknown node " + node_id
            old = nodes[node_id]["attrs"].get(key)
            nodes[node_id]["attrs"][key] = value
            changes["changed_attrs"].append(
                {"node": node_id, "attr": key, "from": old, "to": value})
        else:
            raise ValueError(kind)
    return changes


def main():
    os.makedirs(OUT, exist_ok=True)
    graph = {"nodes": copy.deepcopy(BASE_NODES), "edges": copy.deepcopy(BASE_EDGES)}
    versions, changelog = [], []

    for i, r in enumerate(REVISIONS, start=1):
        changes = apply_ops(graph, r["ops"])
        snap = {
            "revision": r["rev"], "date": r["date"], "author": r["author"],
            "moc": r["moc"], "comment": r["comment"],
            "nodes": copy.deepcopy(graph["nodes"]), "edges": copy.deepcopy(graph["edges"]),
        }
        with open(os.path.join(OUT, "rev_%s.json" % r["rev"]), "w") as f:
            json.dump(snap, f, indent=2)
        versions.append({
            "versionNumber": i,
            "revision": r["rev"],
            "fileNames": ["%s_Rev%s.dxf" % (d, r["rev"]) for d in r["diagrams"]],
            "createTime": r["date"] + "T09:00:00Z",
            "createUserName": r["author"],
            "comment": r["comment"],
            "moc": r["moc"],
            "diagramsAffected": r["diagrams"],
            "snapshot": "versions/rev_%s.json" % r["rev"],
        })
        changelog.append({"revision": r["rev"], "date": r["date"], "moc": r["moc"], **changes})

    with open(os.path.join(OUT, "versions_api.json"), "w") as f:
        json.dump({"data": versions}, f, indent=2)
    with open(os.path.join(OUT, "changelog.json"), "w") as f:
        json.dump(changelog, f, indent=2)
    with open(os.path.join(OUT, "plant_graph_current.json"), "w") as f:
        json.dump(graph, f, indent=2)

    print("wrote %d revisions to %s" % (len(versions), OUT))
    print("final graph: %d nodes, %d edges" % (len(graph["nodes"]), len(graph["edges"])))


if __name__ == "__main__":
    sys.exit(main())
