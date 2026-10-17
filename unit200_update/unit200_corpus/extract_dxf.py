#!/usr/bin/env python3
"""Extract a plant graph from the Unit 200 DXF drawings. No access to the ground-truth JSON.

usage:
  python3 extract_dxf.py extract <REV>            graph as of that revision -> stdout (JSON)
  python3 extract_dxf.py diff <REV_A> <REV_B>     what changed between two revisions
  python3 extract_dxf.py eval                     score extraction against versions/rev_*.json

What it does:
  1. symbols   : INSERT entities -> tag, type (from block name), description (attribute)
  2. pipes     : polylines on the process/utility/relief/signal/impulse layers; each end is
                 snapped to the nearest symbol boundary (flow direction = vertex order)
  3. line nos  : text on LINENUM assigned to the nearest pipe segment
  4. data table: TABLE layer rows -> node attributes
  5. off-page  : OFFPAGE_REF symbols resolve to the tag on the other sheet
  6. revisions : REVTABLE and title block -> revision history
"""
import glob
import json
import math
import os
import re
import sys
from collections import defaultdict

import ezdxf

from dxf_common import BLOCK_BBOX, BLOCK_TO_TYPE, LAYER_KIND, META_KEYS, REF_BLOCK, REV_ORDER, SHEETS


def _core(attrs):
    return {k: v for k, v in attrs.items() if k not in META_KEYS}

HERE = os.path.dirname(os.path.abspath(__file__))
DXF_DIR = os.path.join(HERE, "dxf")
SNAP_TOL = 2.0


def rect_dist(p, r):
    dx = max(r[0] - p[0], 0, p[0] - r[2])
    dy = max(r[1] - p[1], 0, p[1] - r[3])
    return math.hypot(dx, dy)


def seg_dist(p, a, b):
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(p[0] - ax, p[1] - ay)
    t = max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def cast(s):
    for f in (int, float):
        try:
            return f(s)
        except ValueError:
            pass
    return s


def group_rows(texts, ytol=1.5):
    """texts: list of (x, y, str). Returns list of rows (sorted by x), top to bottom."""
    rows = defaultdict(list)
    for x, y, s in texts:
        key = None
        for k in rows:
            if abs(k - y) <= ytol:
                key = k
                break
        rows[y if key is None else key].append((x, s))
    return [sorted(v) for _, v in sorted(rows.items(), key=lambda kv: -kv[0])]


def read_sheet(path):
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    out = {"symbols": [], "pipes": [], "linenums": [], "table": [], "revtable": [], "title": {}}

    for e in msp.query("INSERT"):
        name = e.dxf.name
        if name not in BLOCK_BBOX:
            continue
        att = {a.dxf.tag: a.dxf.text for a in e.attribs}
        x0, y0, x1, y1 = BLOCK_BBOX[name]
        ix, iy = e.dxf.insert.x, e.dxf.insert.y
        out["symbols"].append({"block": name, "pos": (ix, iy), "attrs": att,
                               "rect": (ix + x0, iy + y0, ix + x1, iy + y1)})

    for e in msp.query("LWPOLYLINE"):
        layer = e.dxf.layer
        if layer in LAYER_KIND:
            pts = [(p[0], p[1]) for p in e.get_points("xy")]
            out["pipes"].append({"kind": LAYER_KIND[layer], "pts": pts})

    table_txt, rev_txt, title_txt = [], [], []
    for e in msp.query("TEXT"):
        x, y = e.dxf.insert.x, e.dxf.insert.y
        # alignment point is the real anchor for aligned text
        if e.dxf.halign or e.dxf.valign:
            x, y = e.dxf.align_point.x, e.dxf.align_point.y
        layer, s = e.dxf.layer, e.dxf.text
        if layer == "LINENUM":
            out["linenums"].append((x, y, s))
        elif layer == "TABLE":
            table_txt.append((x, y, s))
        elif layer == "REVTABLE":
            rev_txt.append((x, y, s))
        elif layer == "TITLE":
            title_txt.append(s)

    # data table: rows with exactly 3 cells, skipping the header
    for row in group_rows(table_txt):
        cells = [s for _, s in row]
        if len(cells) == 3 and cells != ["TAG", "ITEM", "VALUE"]:
            out["table"].append(tuple(cells))

    # revision table: a row starts at a line that has a REV cell (x == 745)
    cur = None
    for row in group_rows(rev_txt):
        by_col = {}
        for x, s in row:
            col = 0 if x < 760 else 1 if x < 800 else 2 if x < 920 else 3
            by_col[col] = s
        if 0 in by_col and by_col[0] not in ("REV", "REVISIONS"):
            cur = {"revision": by_col[0], "date": by_col.get(1, ""), "description": by_col.get(2, ""),
                   "moc": by_col.get(3, "-")}
            out["revtable"].append(cur)
        elif cur is not None and 2 in by_col:
            cur["description"] += " " + by_col[2]
    for r in out["revtable"]:
        r["moc"] = None if r["moc"] == "-" else r["moc"]

    for s in title_txt:
        m = re.match(r"(DWG NO|REV|DATE|DRAWN|MOC|TITLE): (.*)", s)
        if m:
            out["title"][m.group(1)] = m.group(2)
    return out


def extract_sheet(path):
    sh = read_sheet(path)
    sheet_id = sh["title"].get("DWG NO", "?")

    # symbol ids
    syms = []
    for s in sh["symbols"]:
        if s["block"] == REF_BLOCK[0]:
            sid = None
            ref = s["attrs"].get("REF_TAG")
            syms.append({**s, "id": "REF:" + ref, "ref": ref, "is_ref": True})
        else:
            syms.append({**s, "id": s["attrs"]["TAG"], "is_ref": False})

    nodes = {}
    for s in syms:
        if s["is_ref"]:
            continue
        nodes[s["id"]] = {"id": s["id"], "type": BLOCK_TO_TYPE[s["block"]], "label": s["attrs"].get("DESC", ""),
                          "diagram": sheet_id, "attrs": {}}

    # node attributes from the data table
    for tag, item, val in sh["table"]:
        if tag in nodes:
            nodes[tag]["attrs"][item.lower().replace(" ", "_")] = cast(val)

    # pipes -> edges
    edges, issues = [], []
    for p in sh["pipes"]:
        ends = []
        for pt in (p["pts"][0], p["pts"][-1]):
            best = min(syms, key=lambda s: rect_dist(pt, s["rect"]))
            d = rect_dist(pt, best["rect"])
            if d > SNAP_TOL:
                issues.append("dangling pipe end at (%.0f,%.0f), nearest %s at %.1f" % (pt[0], pt[1], best["id"], d))
                ends.append(None)
            else:
                ends.append(best["ref"] if best["is_ref"] else best["id"])
        if None in ends:
            continue
        edges.append({"from": ends[0], "to": ends[1], "kind": p["kind"], "pts": p["pts"], "line": None})

    # line numbers -> nearest pipe segment of a process/utility/relief pipe
    for x, y, s in sh["linenums"]:
        cands = []
        for e in edges:
            if e["kind"] in ("process", "utility", "relief"):
                d = min(seg_dist((x, y), a, b) for a, b in zip(e["pts"][:-1], e["pts"][1:]))
                cands.append((d, e))
        if cands:
            d, e = min(cands, key=lambda t: t[0])
            if d <= 8 and e["line"] is None:
                e["line"] = s
            elif d <= 8:
                issues.append("two line numbers on one pipe: %s / %s" % (e["line"], s))
        else:
            issues.append("orphan line number " + s)
    for e in edges:
        del e["pts"]
    return {"sheet": sheet_id, "rev": sh["title"].get("REV"), "nodes": list(nodes.values()), "edges": edges,
            "revisions": sh["revtable"], "title": sh["title"], "issues": issues}


def files_for_rev(rev):
    """For each sheet, the latest DXF whose revision is <= rev."""
    chosen = {}
    for sheet in SHEETS:
        best = None
        for r in REV_ORDER:
            if REV_ORDER.index(r) > REV_ORDER.index(rev):
                break
            p = os.path.join(DXF_DIR, "%s_Rev%s.dxf" % (sheet, r))
            if os.path.exists(p):
                best = p
        if best:
            chosen[sheet] = best
    return chosen


def extract_plant(rev):
    nodes, edges, issues, revisions = {}, [], [], {}
    for sheet, path in files_for_rev(rev).items():
        g = extract_sheet(path)
        issues += ["%s: %s" % (sheet, i) for i in g["issues"]]
        for n in g["nodes"]:
            nodes[n["id"]] = n
        for e in g["edges"]:
            e["sheet"] = sheet
            edges.append(e)
        for r in g["revisions"]:
            revisions[(sheet, r["revision"])] = {**r, "sheet": sheet}
    for e in edges:
        for end in ("from", "to"):
            if e[end] not in nodes:
                issues.append("edge %s -> %s references unknown tag %s" % (e["from"], e["to"], e[end]))
    return {"rev": rev, "nodes": sorted(nodes.values(), key=lambda n: n["id"]), "edges": edges,
            "revisions": sorted(revisions.values(), key=lambda r: (REV_ORDER.index(r["revision"]), r["sheet"])),
            "issues": issues}


# ------------------------------------------------------------------ diff
def edge_key(e):
    return (e["from"], e["to"], e["kind"], e.get("line") if e["kind"] in ("process", "utility", "relief") else None)


def diff(a, b):
    na = {n["id"]: n for n in a["nodes"]}; nb = {n["id"]: n for n in b["nodes"]}
    ea = {edge_key(e) for e in a["edges"]}; eb = {edge_key(e) for e in b["edges"]}
    changed = []
    for k in sorted(set(na) & set(nb)):
        for attr in sorted(set(na[k]["attrs"]) | set(nb[k]["attrs"])):
            va, vb = na[k]["attrs"].get(attr), nb[k]["attrs"].get(attr)
            if va != vb:
                changed.append({"node": k, "attr": attr, "from": va, "to": vb})
    return {"added_nodes": sorted(set(nb) - set(na)), "removed_nodes": sorted(set(na) - set(nb)),
            "added_edges": sorted(eb - ea, key=str), "removed_edges": sorted(ea - eb, key=str),
            "changed_attrs": changed}


# ------------------------------------------------------------------ evaluation
def truth_graph(rev):
    return json.load(open(os.path.join(HERE, "versions", "rev_%s.json" % rev)))


def evaluate():
    all_ok = True
    print("%-4s %6s %6s %8s %8s %9s %8s" % ("rev", "nodes", "edges", "node_ok", "attr_ok", "edge_P/R", "issues"))
    for rev in REV_ORDER:
        got = extract_plant(rev)
        tru = truth_graph(rev)
        tn = {n["id"]: n for n in tru["nodes"]}
        gn = {n["id"]: n for n in got["nodes"]}
        node_ok = sum(1 for k, n in tn.items() if k in gn and gn[k]["type"] == n["type"]
                      and gn[k]["label"] == n["label"] and gn[k]["diagram"] == n["diagram"])
        attr_ok = sum(1 for k, n in tn.items() if k in gn and gn[k]["attrs"] == _core(n["attrs"]))
        te = {edge_key(e) for e in tru["edges"]}
        ge = {edge_key(e) for e in got["edges"]}
        tp = len(te & ge)
        prec = tp / len(ge) if ge else 1.0
        rec = tp / len(te) if te else 1.0
        print("%-4s %3d/%-3d %3d/%-3d %5d/%-3d %5d/%-3d %4.2f/%4.2f %8d" % (
            rev, len(gn), len(tn), len(te & ge), len(te), node_ok, len(tn), attr_ok, len(tn), prec, rec,
            len(got["issues"])))
        if node_ok != len(tn) or attr_ok != len(tn) or te != ge or got["issues"]:
            all_ok = False
            for k in sorted(set(tn) - set(gn)):
                print("   missing node", k)
            for k in sorted(set(gn) - set(tn)):
                print("   extra node", k)
            for k in tn:
                if k in gn and gn[k]["attrs"] != _core(tn[k]["attrs"]):
                    print("   attr mismatch", k, gn[k]["attrs"], "!=", _core(tn[k]["attrs"]))
                if k in gn and (gn[k]["type"], gn[k]["label"]) != (tn[k]["type"], tn[k]["label"]):
                    print("   type/label mismatch", k, gn[k]["type"], gn[k]["label"])
            for k in sorted(te - ge, key=str):
                print("   missing edge", k)
            for k in sorted(ge - te, key=str):
                print("   extra edge", k)
            for i in got["issues"]:
                print("   issue:", i)
    print("ALL PERFECT" if all_ok else "MISMATCHES FOUND")
    return 0 if all_ok else 1


def main(argv):
    if len(argv) >= 3 and argv[1] == "extract":
        json.dump(extract_plant(argv[2]), sys.stdout, indent=2)
        return 0
    if len(argv) >= 4 and argv[1] == "diff":
        json.dump(diff(extract_plant(argv[2]), extract_plant(argv[3])), sys.stdout, indent=2)
        return 0
    if len(argv) >= 2 and argv[1] == "eval":
        return evaluate()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
