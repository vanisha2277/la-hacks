#!/usr/bin/env python3
"""Generate the synthetic P&ID revision history for Harbor Unit 200.

Output (in ./versions):
  rev_<ID>.json        full graph snapshot at that revision (both diagrams)
  versions_api.json    revision list shaped like a document-versions API response
  plant_graph_current.json   latest snapshot
  changelog.json       per-revision diff (added/changed nodes and edges)

The 2021 20LFC10AA191 re-rating is intentionally NOT a revision, so the drawing keeps
set_pressure_barg = 17.2 while Slack says 16.5 (contradiction C01).
20LFC20AA102 is set to FC in Rev 5, while Slack says the field is still FO (contradiction C02).
"""
import copy
import json
import os
import sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "versions")

# ---------------------------------------------------------------- base graph (Rev A)
import kks

_REG = {r["kks"]: r for r in kks.REGISTER}


def n(id, type, label, diagram, **attrs):
    r = _REG.get(id)
    if r:  # KKS metadata, same fields as the valve-list columns
        attrs = dict(attrs, isa_type=r["type"], system_code=r["system_code"], system_seq=r["system_seq"],
                     item_code=r["item_code"], first_seq=r["first_seq"], legacy_tag=r["legacy"])
    return {"id": id, "type": type, "label": label, "diagram": diagram, "attrs": attrs}

def e(id, src, dst, kind, line, diagram, **attrs):
    return {"id": id, "from": src, "to": dst, "kind": kind, "line": line,
            "diagram": diagram, "attrs": attrs}

BASE_NODES = [
    # PID-100 Feed and Preheat
    n("OP-FEED-IN", "offpage", "Feed from battery limit", "PID-100"),
    n("20LFB10BB001", "vessel", "Feed Surge Drum", "PID-100", service="C3/C4 mixed feed"),
    n("20LFB10AP001", "pump", "Feed Pump A", "PID-100", duty="running"),
    n("20LFB10AP002", "pump", "Feed Pump B", "PID-100", duty="standby"),
    n("20LFB10CF001", "transmitter", "Feed Flow Transmitter", "PID-100"),
    n("20LFB10CF002", "controller", "Feed Flow Controller", "PID-100"),
    n("20LFB10AA101", "control_valve", "Feed Flow Control Valve", "PID-100", fail_position="FC"),
    n("20LFB10CL001", "transmitter", "20LFB10BB001 Level Transmitter", "PID-100"),
    n("20LFB20AC001", "heat_exchanger", "Feed/Bottoms Exchanger", "PID-100"),
    # PID-200 Column and Overhead
    n("20LFC10AT001", "column", "C3/C4 Splitter", "PID-200", trays=55),
    n("20LFC20AC001", "heat_exchanger", "Overhead Condenser", "PID-200", utility="cooling water"),
    n("20LFC20BB001", "vessel", "Reflux Drum", "PID-200"),
    n("20LFC20AP001", "pump", "Reflux Pump A", "PID-200", duty="running"),
    n("20LFC20AP002", "pump", "Reflux Pump B", "PID-200", duty="standby"),
    n("20LFC30AC001", "heat_exchanger", "Reboiler", "PID-200", utility="steam"),
    n("20LFC20CF001", "transmitter", "Reflux Flow Transmitter", "PID-200"),
    n("20LFC20CF002", "controller", "Reflux Flow Controller", "PID-200"),
    n("20LFC20AA101", "control_valve", "Reflux Control Valve", "PID-200", cv=45, fail_position="FC"),
    n("20LFC30CT001", "transmitter", "Column Temperature Transmitter", "PID-200", tray=28),
    n("20LFC30CT002", "controller", "Column Temperature Controller", "PID-200", setpoint_c=78),
    n("20LFC30AA101", "control_valve", "Reboiler Steam Valve", "PID-200", fail_position="FC"),
    n("20LFC10CP001", "transmitter", "Column Pressure Transmitter", "PID-200"),
    n("20LFC10CP002", "controller", "Column Pressure Controller", "PID-200"),
    n("20LFC10AA101", "control_valve", "Condenser Cooling Water Valve", "PID-200", fail_position="FO"),
    n("20LFC20CL001", "transmitter", "20LFC20BB001 Level Transmitter", "PID-200"),
    n("20LFC20CL002", "controller", "20LFC20BB001 Level Controller", "PID-200"),
    n("20LFC20AA102", "control_valve", "20LFC20BB001 Product Level Valve", "PID-200", fail_position="FO"),
    n("20LFC10AA191", "relief_valve", "Column Relief Valve", "PID-200", set_pressure_barg=17.2),
    n("OP-C3-PRODUCT", "offpage", "Propane product", "PID-200"),
    n("OP-STORAGE", "offpage", "Butane to storage (PID-300)", "PID-100"),
]

BASE_EDGES = [
    # process, PID-100
    e("L1001", "OP-FEED-IN", "20LFB10BB001", "process", '6"-C3C4-1001', "PID-100"),
    e("L1002A", "20LFB10BB001", "20LFB10AP001", "process", '6"-C3C4-1002', "PID-100"),
    e("L1002B", "20LFB10BB001", "20LFB10AP002", "process", '6"-C3C4-1002', "PID-100"),
    e("L1003A", "20LFB10AP001", "20LFB10AA101", "process", '4"-C3C4-1003', "PID-100"),
    e("L1003B", "20LFB10AP002", "20LFB10AA101", "process", '4"-C3C4-1003', "PID-100"),
    e("L1004", "20LFB10AA101", "20LFB20AC001", "process", '4"-C3C4-1004', "PID-100"),
    # cross-diagram: 20LFB20AC001 to column feed, and bottoms back through 20LFB20AC001
    e("L1005", "20LFB20AC001", "20LFC10AT001", "process", '4"-C3C4-1005', "PID-100", crosses_to="PID-200"),
    e("L1042", "20LFC10AT001", "20LFB20AC001", "process", '4"-C4-1042', "PID-200", crosses_to="PID-100"),
    e("L1043", "20LFB20AC001", "OP-STORAGE", "process", '4"-C4-1043', "PID-100"),
    # process, PID-200
    e("L2001", "20LFC10AT001", "20LFC20AC001", "process", '12"-C3-2001', "PID-200"),
    e("L2002", "20LFC20AC001", "20LFC20BB001", "process", '10"-C3-2002', "PID-200"),
    e("L2003A", "20LFC20BB001", "20LFC20AP001", "process", '4"-C3-2003', "PID-200"),
    e("L2003B", "20LFC20BB001", "20LFC20AP002", "process", '4"-C3-2003', "PID-200"),
    e("L2004A", "20LFC20AP001", "20LFC20AA101", "process", '3"-C3-2004', "PID-200"),
    e("L2004B", "20LFC20AP002", "20LFC20AA101", "process", '3"-C3-2004', "PID-200"),
    e("L2005", "20LFC20AA101", "20LFC10AT001", "process", '3"-C3-2005', "PID-200"),
    e("L2006", "20LFC20BB001", "20LFC20AA102", "process", '2"-C3-2006', "PID-200"),
    e("L2007", "20LFC20AA102", "OP-C3-PRODUCT", "process", '2"-C3-2007', "PID-200"),
    e("L2008", "20LFC10AT001", "20LFC30AC001", "process", '10"-C4-2008', "PID-200"),
    e("L2009", "20LFC30AC001", "20LFC10AT001", "process", '10"-C4-2009', "PID-200"),
    e("L2010", "20LFC10AT001", "20LFC10AA191", "relief", '6"-REL-2010', "PID-200"),
    # utilities
    e("U2001", "20LFC30AA101", "20LFC30AC001", "utility", '3"-STM-2011', "PID-200"),
    e("U2002", "20LFC10AA101", "20LFC20AC001", "utility", '6"-CW-2012', "PID-200"),
    # impulse (sensing) lines
    e("I1001", "20LFB10BB001", "20LFB10CL001", "impulse", "impulse 20LFB10BB001 to 20LFB10CL001", "PID-100"),
    e("I2001", "20LFC20BB001", "20LFC20CL001", "impulse", "impulse 20LFC20BB001 to 20LFC20CL001", "PID-200"),
    e("I2002", "20LFC10AT001", "20LFC30CT001", "impulse", "impulse 20LFC10AT001 to 20LFC30CT001", "PID-200"),
    e("I2003", "20LFC10AT001", "20LFC10CP001", "impulse", "impulse 20LFC10AT001 to 20LFC10CP001", "PID-200"),
    # signals, PID-100
    e("S1001", "20LFB10CF001", "20LFB10CF002", "signal", "20LFB10CF001 to 20LFB10CF002", "PID-100"),
    e("S1002", "20LFB10CF002", "20LFB10AA101", "signal", "20LFB10CF002 to 20LFB10AA101", "PID-100"),
    # signals, PID-200
    e("S2001", "20LFC20CF001", "20LFC20CF002", "signal", "20LFC20CF001 to 20LFC20CF002", "PID-200"),
    e("S2002", "20LFC20CF002", "20LFC20AA101", "signal", "20LFC20CF002 to 20LFC20AA101", "PID-200"),
    e("S2003", "20LFC30CT001", "20LFC30CT002", "signal", "20LFC30CT001 to 20LFC30CT002", "PID-200"),
    e("S2004", "20LFC30CT002", "20LFC30AA101", "signal", "20LFC30CT002 to 20LFC30AA101", "PID-200"),
    e("S2005", "20LFC10CP001", "20LFC10CP002", "signal", "20LFC10CP001 to 20LFC10CP002", "PID-200"),
    e("S2006", "20LFC10CP002", "20LFC10AA101", "signal", "20LFC10CP002 to 20LFC10AA101", "PID-200"),
    e("S2007", "20LFC20CL001", "20LFC20CL002", "signal", "20LFC20CL001 to 20LFC20CL002", "PID-200"),
    e("S2008", "20LFC20CL002", "20LFC20AA102", "signal", "20LFC20CL002 to 20LFC20AA102", "PID-200"),
]

# ---------------------------------------------------------------- revisions
# ops: ("add_node", node) | ("add_edge", edge) | ("remove_edge", edge_id) | ("set_attr", node_id, key, value)
REVISIONS = [
    {"rev": "A", "date": "2017-09-12", "author": "Dana Okafor", "moc": None,
     "comment": "Issued for design", "diagrams": ["PID-100", "PID-200"], "ops": []},
    {"rev": "0", "date": "2018-06-20", "author": "Dana Okafor", "moc": None,
     "comment": "As-built after commissioning. Added 20LFB10CP101 auto-start for standby feed pump.",
     "diagrams": ["PID-100"],
     "ops": [
         ("add_node", n("20LFB10CP101", "switch", "Feed Pump Low Discharge Pressure Switch", "PID-100")),
         ("add_edge", e("S1003", "20LFB10CP101", "20LFB10AP002", "signal", "20LFB10CP101 auto-start 20LFB10AP002", "PID-100")),
     ]},
    {"rev": "1", "date": "2019-12-02", "author": "Dana Okafor", "moc": "MOC-2019-021",
     "comment": "Post-incident corrective actions: reflux pump low-low level trip, discharge check valves, reflux low-flow alarm.",
     "diagrams": ["PID-200"],
     "ops": [
         ("add_node", n("20LFC20CL101", "switch", "20LFC20BB001 Low-Low Level Trip", "PID-200", trips="20LFC20AP001, 20LFC20AP002")),
         ("add_node", n("20LFC20AA011", "check_valve", "20LFC20AP001 Discharge Check Valve", "PID-200")),
         ("add_node", n("20LFC20AA012", "check_valve", "20LFC20AP002 Discharge Check Valve", "PID-200")),
         ("add_node", n("20LFC20CF101", "alarm", "Reflux Low Flow Alarm", "PID-200")),
         ("add_edge", e("S2009", "20LFC20CL101", "20LFC20AP001", "signal", "20LFC20CL101 trip 20LFC20AP001", "PID-200")),
         ("add_edge", e("S2010", "20LFC20CL101", "20LFC20AP002", "signal", "20LFC20CL101 trip 20LFC20AP002", "PID-200")),
         ("add_edge", e("S2011", "20LFC20CF001", "20LFC20CF101", "signal", "20LFC20CF001 to 20LFC20CF101", "PID-200")),
         ("remove_edge", "L2004A"),
         ("remove_edge", "L2004B"),
         ("add_edge", e("L2004A1", "20LFC20AP001", "20LFC20AA011", "process", '3"-C3-2004', "PID-200")),
         ("add_edge", e("L2004A2", "20LFC20AA011", "20LFC20AA101", "process", '3"-C3-2004', "PID-200")),
         ("add_edge", e("L2004B1", "20LFC20AP002", "20LFC20AA012", "process", '3"-C3-2004', "PID-200")),
         ("add_edge", e("L2004B2", "20LFC20AA012", "20LFC20AA101", "process", '3"-C3-2004', "PID-200")),
         ("set_attr", "20LFC20AP001", "check_valve", "20LFC20AA011"),
         ("set_attr", "20LFC20AP002", "check_valve", "20LFC20AA012"),
     ]},
    {"rev": "2", "date": "2020-08-18", "author": "Dana Okafor", "moc": "MOC-2020-014",
     "comment": "20LFC20AA101 trim upsized for higher feed rate.",
     "diagrams": ["PID-200"],
     "ops": [("set_attr", "20LFC20AA101", "cv", 75)]},
    {"rev": "3", "date": "2022-03-09", "author": "Dana Okafor", "moc": "MOC-2022-007",
     "comment": "Added bypass 20LFB20AA001 around 20LFB20AC001 to maintain feed temperature during fouling.",
     "diagrams": ["PID-100"],
     "ops": [
         ("add_node", n("20LFB20AA001", "manual_valve", "20LFB20AC001 Bypass Valve", "PID-100")),
         ("add_edge", e("L1004B", "20LFB10AA101", "20LFB20AA001", "process", '4"-C3C4-1004B', "PID-100")),
         ("add_edge", e("L1005B", "20LFB20AA001", "20LFC10AT001", "process", '4"-C3C4-1005B', "PID-100", crosses_to="PID-200")),
     ]},
    {"rev": "4", "date": "2023-05-22", "author": "Priya Raman", "moc": "MOC-2023-009",
     "comment": "20LFC30CT001 relocated from tray 28 to tray 32. 20LFC30CT002 setpoint updated.",
     "diagrams": ["PID-200"],
     "ops": [
         ("set_attr", "20LFC30CT001", "tray", 32),
         ("set_attr", "20LFC30CT002", "setpoint_c", 81),
     ]},
    {"rev": "5", "date": "2024-10-14", "author": "Dana Okafor", "moc": "MOC-2024-031",
     "comment": "20LFC20AA102 fail position changed from FO to FC after 20LFC20BB001 overfill near-miss.",
     "diagrams": ["PID-200"],
     "ops": [("set_attr", "20LFC20AA102", "fail_position", "FC")]},
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
