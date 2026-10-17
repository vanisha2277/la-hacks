#!/usr/bin/env python3
"""Draw the Unit 200 P&IDs as real DXF files, one file per sheet per revision.

Reads versions/rev_<R>.json (made by pid_versions.py) and writes
dxf/<SHEET>_Rev<R>.dxf for every revision that touched that sheet.

What a CAD reader sees in each file:
  - symbols as block INSERTs with TAG and DESC attributes
  - pipes as polylines on layers PROCESS / UTILITY / RELIEF / SIGNAL / IMPULSE
  - line numbers as text on layer LINENUM
  - a data table (valve fail positions, set pressures, etc) on layer TABLE
  - a title block and revision table on layer TITLE / REVTABLE
Nothing in the drawing points back at the JSON graph.
"""
import json
import os
import re
import sys
import textwrap

import ezdxf
from ezdxf import const
from ezdxf.enums import TextEntityAlignment

from dxf_common import (BLOCK_BBOX, KIND_LAYER, REF_BLOCK, REV_ORDER, SHEET_H, SHEET_W,
                        SHEETS, SYMBOLS, TABLE_COLS, META_KEYS)

HERE = os.path.dirname(os.path.abspath(__file__))
VERS = os.path.join(HERE, "versions")
OUT = os.path.join(HERE, "dxf")

# ------------------------------------------------------------------ layout
POS = {
    "PID-100": {
        "OP-FEED-IN": (60, 400), "20LFB10BB001": (190, 400), "20LFB10AP001": (310, 450), "20LFB10AP002": (310, 350),
        "20LFB10AA101": (440, 400), "20LFB20AC001": (560, 400), "20LFB20AA001": (610, 300), "OP-STORAGE": (700, 180),
        "20LFB10CF001": (370, 500), "20LFB10CF002": (440, 500), "20LFB10CL001": (190, 520), "20LFB10CP101": (400, 290),
    },
    "PID-200": {
        "20LFC10AT001": (330, 400), "20LFC20AC001": (450, 590), "20LFC20BB001": (600, 590),
        "20LFC20AP001": (560, 490), "20LFC20AP002": (660, 490), "20LFC20AA011": (560, 440), "20LFC20AA012": (660, 440),
        "20LFC20AA101": (440, 380), "20LFC20CF002": (440, 440), "20LFC20CF001": (510, 440), "20LFC20CF101": (510, 520),
        "20LFC20CL101": (610, 470), "20LFC20AA102": (690, 590), "OP-C3-PRODUCT": (800, 590),
        "20LFC20CL001": (600, 650), "20LFC20CL002": (680, 650),
        "20LFC30AC001": (190, 230), "20LFC30AA101": (80, 230), "20LFC30CT001": (220, 440), "20LFC30CT002": (140, 440),
        "20LFC10CP001": (400, 525), "20LFC10CP002": (500, 690), "20LFC10AA101": (500, 640), "20LFC10AA191": (390, 490),
    },
}
# off-page reference symbols, keyed by edge id (drawn on the sheet that draws the edge)
REFS = {"L1005": (700, 400), "L1005B": (700, 300), "L1042": (500, 280)}

# sides: R, L, T, B ; offsets slide the port along that side
ROUTES = {
    # PID-100
    "L1001": ("R", 0, "L", 0), "L1002A": ("R", 0, "L", 0), "L1002B": ("R", 0, "L", 0),
    "L1003A": ("R", 0, "L", 0), "L1003B": ("R", 0, "L", 0), "L1004": ("R", 0, "L", 0),
    "L1004B": ("R", 0, "L", 0), "L1005": ("R", 0, "L", 0), "L1005B": ("R", 0, "L", 0),
    "L1043": ("B", 0, "L", 0), "I1001": ("T", 0, "B", 0),
    "S1001": ("R", 0, "L", 0), "S1002": ("B", 0, "T", 0), "S1003": ("L", 0, "B", 0),
    # PID-200
    "L2001": ("T", 0, "L", 0), "L2002": ("R", 0, "L", 0),
    "L2003A": ("B", 0, "T", 0), "L2003B": ("B", 0, "T", 0),
    "L2004A": ("B", 0, "R", 0), "L2004B": ("B", 0, "R", 0),
    "L2004A1": ("B", 0, "T", 0), "L2004B1": ("B", 0, "T", 0),
    "L2004A2": ("B", 0, "R", 0), "L2004B2": ("B", 0, "R", 0),
    "L2005": ("L", 0, "R", -20), "L2006": ("R", 0, "L", 0), "L2007": ("R", 0, "L", 0),
    "L2008": ("B", 0, "R", 0), "L2009": ("T", 0, "L", -110), "L2010": ("R", 90, "L", 0),
    "L1042": ("R", -120, "L", 0),
    "U2001": ("R", 0, "L", 0), "U2002": ("L", 0, "T", 0),
    "I2001": ("T", 0, "B", 0), "I2002": ("L", 0, "R", 0), "I2003": ("R", 125, "L", 0),
    "S2001": ("L", 0, "R", 0), "S2002": ("B", 0, "T", 0), "S2003": ("L", 0, "R", 0),
    "S2004": ("B", 0, "T", 0), "S2005": ("T", 0, "L", 0), "S2006": ("B", 0, "T", 0),
    "S2007": ("R", 0, "L", 0), "S2008": ("B", 0, "T", 0), "S2009": ("L", 0, "R", 0),
    "S2010": ("R", 0, "L", 0), "S2011": ("T", 0, "B", 0),
}
# the 20LFC30CT001 impulse tap follows the tray attribute (tray n sits at this y on the column)
COL_CY, COL_H, COL_TRAYS = 400.0, 260.0, 55


def tray_offset(tray):
    y = (COL_CY - COL_H / 2) + (tray - 0.5) * COL_H / COL_TRAYS
    return y - COL_CY


# ------------------------------------------------------------------ blocks
def make_blocks(doc):
    def blk(name):
        return doc.blocks.new(name=name)

    def tag(b, text_pos, h=3.0, name="TAG", invisible=False, prompt=None):
        a = b.add_attdef(name, text_pos, text=name, dxfattribs={"height": h, "layer": "SYMBOLS"})
        a.dxf.halign = const.CENTER
        a.dxf.valign = const.MIDDLE
        a.dxf.align_point = text_pos
        if invisible:
            a.dxf.flags |= const.ATTRIB_INVISIBLE
        return a

    L = {"layer": "SYMBOLS"}

    def valve_pill(b, cx=34, cy=-26):
        """Tag pill with a leader line to the valve, like the legend's valve typicals (ISA type over KKS tag)."""
        b.add_line((cx - 12, cy + 10), (cx + 12, cy + 10), dxfattribs=L); b.add_line((cx - 12, cy - 10), (cx + 12, cy - 10), dxfattribs=L)
        b.add_arc((cx - 12, cy), 10, 90, 270, dxfattribs=L); b.add_arc((cx + 12, cy), 10, 270, 90, dxfattribs=L)
        b.add_line((cx - 22, cy), (cx + 22, cy), dxfattribs=L)
        s = 1 if cy > 0 else -1
        b.add_line((4, 4 * s), (cx - 14, cy - 8.5 * s), dxfattribs=L)    # leader
        tag(b, (cx, cy + 4.4), h=2.8, name="ISA")
        tag(b, (cx, cy - 4.4), h=2.2)
        tag(b, (0, 0), invisible=True, name="DESC")

    b = blk("PUMP")
    b.add_circle((0, 0), 15, dxfattribs=L)
    b.add_line((0, 15), (15, 15), dxfattribs=L)                      # discharge nozzle (centrifugal pump)
    b.add_line((-10.6, -10.6), (10.6, 10.6), dxfattribs=L)           # casing chord
    tag(b, (0, -23)); tag(b, (0, 0), invisible=True, name="DESC")

    b = blk("VESSEL")
    b.add_line((-13, 22), (13, 22), dxfattribs=L); b.add_line((-13, -22), (13, -22), dxfattribs=L)
    b.add_arc((-13, 0), 22, 90, 270, dxfattribs=L); b.add_arc((13, 0), 22, 270, 90, dxfattribs=L)
    tag(b, (0, 0)); tag(b, (0, 0), invisible=True, name="DESC")

    b = blk("COLUMN")
    b.add_line((-20, -110), (-20, 110), dxfattribs=L); b.add_line((20, -110), (20, 110), dxfattribs=L)
    b.add_arc((0, 110), 20, 0, 180, dxfattribs=L); b.add_arc((0, -110), 20, 180, 360, dxfattribs=L)
    for i in range(1, 11):  # a few tray lines for looks
        y = -110 + i * 20
        b.add_line((-20, y), (20, y), dxfattribs={"layer": "SYMBOLS", "color": 8})
    tag(b, (0, 0), h=4); tag(b, (0, 0), invisible=True, name="DESC")

    b = blk("HEATEX")
    b.add_lwpolyline([(-25, -12), (25, -12), (25, 12), (-25, 12)], close=True, dxfattribs=L)
    b.add_lwpolyline([(-25, 0), (-15, 8), (-5, -8), (5, 8), (15, -8), (25, 0)], dxfattribs=L)
    tag(b, (0, -20)); tag(b, (0, 0), invisible=True, name="DESC")

    def bowtie(b, half=12, h=8):
        b.add_lwpolyline([(-half, h), (0, 0), (-half, -h)], close=True, dxfattribs=L)
        b.add_lwpolyline([(half, h), (0, 0), (half, -h)], close=True, dxfattribs=L)

    b = blk("CTRLVALVE")
    bowtie(b); b.add_line((0, 0), (0, 10), dxfattribs=L); b.add_arc((0, 10), 12, 0, 180, dxfattribs=L)
    valve_pill(b)

    b = blk("MANVALVE")
    bowtie(b)
    for sign in (-1, 1):  # solid fill = normally closed
        h = b.add_hatch(color=7, dxfattribs=L)
        h.paths.add_polyline_path([(sign * 12, 8), (0, 0), (sign * 12, -8)], is_closed=True)
    b.add_line((0, 0), (0, 12), dxfattribs=L); b.add_line((-5, 12), (5, 12), dxfattribs=L)   # hand actuator
    valve_pill(b)

    b = blk("CHECKVALVE")
    b.add_line((-10, 0), (10, 0), dxfattribs=L)
    b.add_line((-5, 0), (6, -7), dxfattribs=L)
    h = b.add_hatch(color=7, dxfattribs=L); h.paths.add_polyline_path(
        [(-6.5, 1.5), (-3.5, 1.5), (-3.5, -1.5), (-6.5, -1.5)], is_closed=True)
    valve_pill(b, 38, -28)

    b = blk("RELIEFVALVE")
    b.add_lwpolyline([(-10, -10), (-10, 10), (10, 0)], close=True, dxfattribs=L)
    b.add_line((-5, 0), (-5, 4), dxfattribs=L)
    b.add_lwpolyline([(-5, 4), (-8, 6), (-2, 8), (-8, 10), (-2, 12), (-5, 14)], dxfattribs=L)   # spring
    valve_pill(b, 38, -28)

    def pill(name, lines):
        b = blk(name)
        b.add_line((-12, 10), (12, 10), dxfattribs=L); b.add_line((-12, -10), (12, -10), dxfattribs=L)
        b.add_arc((-12, 0), 10, 90, 270, dxfattribs=L); b.add_arc((12, 0), 10, 270, 90, dxfattribs=L)
        for y in lines:                    # horizontal bars: DCS / hard-wired, same idea as the legend
            b.add_line((-22, y), (22, y), dxfattribs=L)
        tag(b, (0, 4.4), h=2.8, name="ISA")      # ISA function letters
        tag(b, (0, -4.4), h=2.2)                 # KKS tag
        tag(b, (0, 0), invisible=True, name="DESC")

    pill("INSTR_XMTR", [])
    pill("INSTR_CTRL", [0])
    pill("INSTR_SWITCH", [0])
    pill("INSTR_ALARM", [0])

    b = blk("OFFPAGE")
    b.add_lwpolyline([(-30, -12), (18, -12), (30, 0), (18, 12), (-30, 12)], close=True, dxfattribs=L)
    tag(b, (-4, -1.2), h=2.4); tag(b, (0, 0), invisible=True, name="DESC")

    b = blk("OFFPAGE_REF")
    b.add_lwpolyline([(-30, -12), (18, -12), (30, 0), (18, 12), (-30, 12)], close=True, dxfattribs=L)
    tag(b, (-4, 3.5), h=2.6, name="REF_TAG"); tag(b, (-4, -4.5), h=2.2, name="SHEET")


# ------------------------------------------------------------------ geometry helpers
def bbox_abs(block, pos):
    x0, y0, x1, y1 = BLOCK_BBOX[block]
    return (pos[0] + x0, pos[1] + y0, pos[0] + x1, pos[1] + y1)


def port(block, pos, side, off=0.0):
    x0, y0, x1, y1 = bbox_abs(block, pos)
    cx, cy = pos
    if side == "L":
        return (x0, cy + off)
    if side == "R":
        return (x1, cy + off)
    if side == "T":
        return (cx + off, y1)
    if side == "B":
        return (cx + off, y0)
    raise ValueError(side)


def route(p0, s0, p1, s1):
    h0, h1 = s0 in "LR", s1 in "LR"
    close = lambda a, b: abs(a - b) < 1e-6
    if h0 and h1:
        pts = [p0, p1] if close(p0[1], p1[1]) else [p0, ((p0[0] + p1[0]) / 2, p0[1]), ((p0[0] + p1[0]) / 2, p1[1]), p1]
    elif h0 and not h1:
        pts = [p0, (p1[0], p0[1]), p1]
    elif not h0 and h1:
        pts = [p0, (p0[0], p1[1]), p1]
    else:
        pts = [p0, p1] if close(p0[0], p1[0]) else [p0, (p0[0], (p0[1] + p1[1]) / 2), (p1[0], (p0[1] + p1[1]) / 2), p1]
    out = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - out[-1][0]) > 1e-6 or abs(p[1] - out[-1][1]) > 1e-6:
            out.append(p)
    return out


def seg_len(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def overlaps(a, b, c, d):
    """True if axis-aligned segments a-b and c-d are collinear and share length."""
    if abs(a[0] - b[0]) < 1e-6 and abs(c[0] - d[0]) < 1e-6 and abs(a[0] - c[0]) < 1e-6:
        lo1, hi1 = sorted((a[1], b[1])); lo2, hi2 = sorted((c[1], d[1]))
        return min(hi1, hi2) - max(lo1, lo2) > 1e-6
    if abs(a[1] - b[1]) < 1e-6 and abs(c[1] - d[1]) < 1e-6 and abs(a[1] - c[1]) < 1e-6:
        lo1, hi1 = sorted((a[0], b[0])); lo2, hi2 = sorted((c[0], d[0]))
        return min(hi1, hi2) - max(lo1, lo2) > 1e-6
    return False


# ------------------------------------------------------------------ drawing
def draw_frame(msp):
    """Double border with zone marks (columns 1-16, rows A-M) like the reference sheet."""
    F = {"layer": "FRAME"}
    msp.add_lwpolyline([(2, 2), (SHEET_W - 2, 2), (SHEET_W - 2, SHEET_H - 2), (2, SHEET_H - 2)], close=True, dxfattribs=F)
    msp.add_lwpolyline([(14, 14), (SHEET_W - 14, 14), (SHEET_W - 14, SHEET_H - 14), (14, SHEET_H - 14)], close=True, dxfattribs=F)
    cw, rh = (SHEET_W - 28) / 16.0, (SHEET_H - 28) / 13.0
    for i in range(16):
        x = 14 + cw * (i + 0.5)
        for y in (8, SHEET_H - 8):
            msp.add_text(str(i + 1), height=3, dxfattribs=F).set_placement((x, y), align=TextEntityAlignment.MIDDLE_CENTER)
        if i:
            for y0, y1 in ((2, 14), (SHEET_H - 14, SHEET_H - 2)):
                msp.add_line((14 + cw * i, y0), (14 + cw * i, y1), dxfattribs=F)
    for j in range(13):
        y = SHEET_H - 14 - rh * (j + 0.5)
        for x in (8, SHEET_W - 8):
            msp.add_text(chr(65 + j), height=3, dxfattribs=F).set_placement((x, y), align=TextEntityAlignment.MIDDLE_CENTER)
        if j:
            for x0, x1 in ((2, 14), (SHEET_W - 14, SHEET_W - 2)):
                msp.add_line((x0, SHEET_H - 14 - rh * j), (x1, SHEET_H - 14 - rh * j), dxfattribs=F)
    # rounded "not a real plant" box, same place and idea as the reference's confidentiality box
    x0, y0, x1, y1, r = 330, 26, 650, 62, 6
    msp.add_line((x0 + r, y0), (x1 - r, y0), dxfattribs=F); msp.add_line((x0 + r, y1), (x1 - r, y1), dxfattribs=F)
    msp.add_line((x0, y0 + r), (x0, y1 - r), dxfattribs=F); msp.add_line((x1, y0 + r), (x1, y1 - r), dxfattribs=F)
    for (cx, cy, a0, a1) in ((x0 + r, y0 + r, 180, 270), (x1 - r, y0 + r, 270, 360), (x1 - r, y1 - r, 0, 90), (x0 + r, y1 - r, 90, 180)):
        msp.add_arc((cx, cy), r, a0, a1, dxfattribs=F)
    msp.add_text("SYNTHETIC DEMO DATA", height=7, dxfattribs=F).set_placement((490, 47), align=TextEntityAlignment.MIDDLE_CENTER)
    msp.add_text("NOT A REAL PLANT", height=7, dxfattribs=F).set_placement((490, 33), align=TextEntityAlignment.MIDDLE_CENTER)


INCH_TO_DN = {2: 50, 3: 80, 4: 100, 6: 150, 8: 200, 10: 250, 12: 300}


def draw_sheet(rev, sheet, snap, revs_meta, warnings):
    doc = ezdxf.new("R2010", setup=True)
    doc.layers.add("SYMBOLS", color=7); doc.layers.add("PROCESS", color=7)
    doc.layers.add("UTILITY", color=3); doc.layers.add("RELIEF", color=1)
    doc.layers.add("SIGNAL", color=5, linetype="DASHED"); doc.layers.add("IMPULSE", color=4, linetype="DASHED")
    for name in ("LINENUM", "TABLE", "TITLE", "REVTABLE", "FRAME", "ANNOT"):
        doc.layers.add(name, color=8 if name == "FRAME" else 7)
    for name, lw in (("PROCESS", 50), ("UTILITY", 50), ("RELIEF", 50), ("SYMBOLS", 25), ("SIGNAL", 13), ("IMPULSE", 13)):
        doc.layers.get(name).dxf.lineweight = lw
    make_blocks(doc)
    msp = doc.modelspace()

    nodes = {n["id"]: n for n in snap["nodes"]}
    sheet_nodes = [n for n in snap["nodes"] if n["diagram"] == sheet]
    sheet_edges = [x for x in snap["edges"] if x["diagram"] == sheet]
    pos = POS[sheet]

    # frame
    draw_frame(msp)

    # symbols
    placed = {}  # key -> (block, pos)
    for n in sheet_nodes:
        block = SYMBOLS[n["type"]][0]
        if n["id"] not in pos:
            warnings.append("%s Rev%s: no layout position for %s" % (sheet, rev, n["id"]))
            continue
        p = pos[n["id"]]
        ref = msp.add_blockref(block, p, dxfattribs={"layer": "SYMBOLS"})
        ref.add_auto_attribs({"TAG": n["id"], "DESC": n["label"], "ISA": n["attrs"].get("isa_type", "")})
        placed[n["id"]] = (block, p)

    # off-page reference symbols for edges that leave this sheet
    edge_ends = {}  # edge id -> (src_key, dst_key)
    for ed in sheet_edges:
        ends = []
        for end in ("from", "to"):
            nid = ed[end]
            if nodes[nid]["diagram"] == sheet:
                ends.append(nid)
            else:
                key = "REF:%s:%s" % (ed["id"], end)
                p = REFS[ed["id"]]
                ref = msp.add_blockref(REF_BLOCK[0], p, dxfattribs={"layer": "SYMBOLS"})
                ref.add_auto_attribs({"REF_TAG": nid, "SHEET": "SH " + nodes[nid]["diagram"]})
                placed[key] = (REF_BLOCK[0], p)
                ends.append(key)
        edge_ends[ed["id"]] = tuple(ends)

    # pipes
    polylines = {}
    for ed in sheet_edges:
        rt = ROUTES.get(ed["id"])
        if rt is None:
            warnings.append("%s Rev%s: no route for edge %s" % (sheet, rev, ed["id"]))
            continue
        s0, o0, s1, o1 = rt
        sk, dk = edge_ends[ed["id"]]
        # special: 20LFC30CT001 tap follows the tray attribute
        if ed["id"] == "I2002":
            o0 = tray_offset(nodes["20LFC30CT001"]["attrs"]["tray"])
        b0, p0 = placed[sk]; b1, p1 = placed[dk]
        pts = route(port(b0, p0, s0, o0), s0, port(b1, p1, s1, o1), s1)
        msp.add_lwpolyline(pts, dxfattribs={"layer": KIND_LAYER[ed["kind"]]})
        polylines[ed["id"]] = pts

    # line number labels (process / utility / relief), on the longest segment no other pipe overlaps
    for ed in sheet_edges:
        if ed["kind"] not in ("process", "utility", "relief") or ed["id"] not in polylines:
            continue
        pts = polylines[ed["id"]]
        segs = list(zip(pts[:-1], pts[1:]))
        others = [(a, b) for k, p in polylines.items() if k != ed["id"] for a, b in zip(p[:-1], p[1:])]
        free = [s for s in segs if not any(overlaps(s[0], s[1], c, d) for c, d in others)]
        a, b = max(free or segs, key=lambda s: seg_len(*s))
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        if abs(a[1] - b[1]) < 1e-6:   # horizontal segment: label above
            t = msp.add_text(ed["line"], height=3, dxfattribs={"layer": "LINENUM"})
            t.set_placement((mx, my + 4), align=TextEntityAlignment.BOTTOM_CENTER)
        else:                          # vertical segment: label beside, rotated
            t = msp.add_text(ed["line"], height=3, dxfattribs={"layer": "LINENUM", "rotation": 90})
            t.set_placement((mx - 4, my), align=TextEntityAlignment.BOTTOM_CENTER)

    # pipe size and class under each process line (DN 100 1C1), fail position next to valves
    for ed in sheet_edges:
        if ed["kind"] not in ("process", "utility", "relief") or ed["id"] not in polylines:
            continue
        m = re.match(r'(\d+)"', ed["line"])
        if not m:
            continue
        pts = polylines[ed["id"]]
        a, bb = max(zip(pts[:-1], pts[1:]), key=lambda s: seg_len(*s))
        mx, my = (a[0] + bb[0]) / 2, (a[1] + bb[1]) / 2
        txt = "DN %d 1C1" % INCH_TO_DN[int(m.group(1))]
        if abs(a[1] - bb[1]) < 1e-6:
            t = msp.add_text(txt, height=2.6, dxfattribs={"layer": "ANNOT"})
            t.set_placement((mx, my - 4), align=TextEntityAlignment.TOP_CENTER)
        else:
            t = msp.add_text(txt, height=2.6, dxfattribs={"layer": "ANNOT", "rotation": 90})
            t.set_placement((mx + 4, my), align=TextEntityAlignment.TOP_CENTER)
    for n in sheet_nodes:
        fp = n["attrs"].get("fail_position")
        if fp and n["id"] in pos:
            t = msp.add_text({"FC": "F.C.", "FO": "F.O.", "FL": "F.L."}.get(fp, fp), height=2.8, dxfattribs={"layer": "ANNOT"})
            t.set_placement((pos[n["id"]][0] - 15, pos[n["id"]][1] - 11), align=TextEntityAlignment.MIDDLE_RIGHT)

    # data table
    rows = []
    for n in sorted(sheet_nodes, key=lambda n: n["id"]):
        for k, v in n["attrs"].items():
            if k in META_KEYS:
                continue
            rows.append((n["id"], k.upper().replace("_", " "), str(v)))
    x_tag, x_item, x_val = TABLE_COLS
    y = 548
    msp.add_text("EQUIPMENT AND INSTRUMENT DATA", height=4, dxfattribs={"layer": "TABLE"}).set_placement((x_tag, y))
    y -= 12
    for c, label in zip(TABLE_COLS, ("TAG", "ITEM", "VALUE")):
        msp.add_text(label, height=3, dxfattribs={"layer": "TABLE", "color": 8}).set_placement((c, y))
    y -= 11
    for tagname, item, val in rows:
        if y < 262:
            warnings.append("%s Rev%s: data table overflow" % (sheet, rev))
            break
        for c, text in zip(TABLE_COLS, (tagname, item, val)):
            msp.add_text(text, height=2.8, dxfattribs={"layer": "TABLE"}).set_placement((c, y))
        y -= 9

    # revision table (rows only for revisions that touched this sheet, up to this rev)
    top = 245
    msp.add_text("REVISIONS", height=3.5, dxfattribs={"layer": "REVTABLE"}).set_placement((745, top))
    y = top - 10
    cols = (745, 765, 810, 925)
    for c, label in zip(cols, ("REV", "DATE", "DESCRIPTION", "MOC")):
        msp.add_text(label, height=2.6, dxfattribs={"layer": "REVTABLE", "color": 8}).set_placement((c, y))
    y -= 9
    for m in revs_meta:
        lines = textwrap.wrap(m["comment"], width=34) or [""]
        msp.add_text(m["revision"], height=2.8, dxfattribs={"layer": "REVTABLE"}).set_placement((cols[0], y))
        msp.add_text(m["date"], height=2.8, dxfattribs={"layer": "REVTABLE"}).set_placement((cols[1], y))
        msp.add_text(m["moc"] or "-", height=2.8, dxfattribs={"layer": "REVTABLE"}).set_placement((cols[3], y))
        for ln in lines:
            msp.add_text(ln, height=2.6, dxfattribs={"layer": "REVTABLE"}).set_placement((cols[2], y))
            y -= 7
        y -= 2
    if y < 118:
        warnings.append("%s Rev%s: revision table overflow (y=%d)" % (sheet, rev, y))

    # title block
    msp.add_lwpolyline([(740, 16), (984, 16), (984, 112), (740, 112)], close=True, dxfattribs={"layer": "TITLE"})
    cur = revs_meta[-1]
    tb = ["MERIDIAN GAS PROCESSING - HARBOR TERMINAL",
          "SYNTHETIC DEMO DATA - NOT A REAL PLANT",
          "UNIT 200 C3/C4 SPLITTER",
          "TITLE: " + SHEETS[sheet],
          "DWG NO: " + sheet,
          "REV: " + cur["revision"],
          "DATE: " + cur["date"],
          "DRAWN: " + cur["author"],
          "MOC: " + (cur["moc"] or "-")]
    y = 102
    for i, line in enumerate(tb):
        msp.add_text(line, height=4 if i < 3 else 3.2, dxfattribs={"layer": "TITLE"}).set_placement((746, y))
        y -= 10.5 if i < 3 else 9.5

    # collision check: no pipe segment may pass through a symbol it does not connect to
    for ed in sheet_edges:
        pts = polylines.get(ed["id"])
        if not pts:
            continue
        own = set(edge_ends[ed["id"]])
        for key, (block, p) in placed.items():
            if key in own:
                continue
            x0, y0, x1, y1 = bbox_abs(block, p)
            x0 += 1; y0 += 1; x1 -= 1; y1 -= 1
            for a, b in zip(pts[:-1], pts[1:]):
                if max(a[0], b[0]) > x0 and min(a[0], b[0]) < x1 and max(a[1], b[1]) > y0 and min(a[1], b[1]) < y1:
                    warnings.append("%s Rev%s: pipe %s passes through %s" % (sheet, rev, ed["id"], key))
                    break

    return doc


def main():
    os.makedirs(OUT, exist_ok=True)
    api = json.load(open(os.path.join(VERS, "versions_api.json")))["data"]
    meta = {v["revision"]: v for v in api}
    warnings, written = [], []
    for v in api:
        rev = v["revision"]
        snap = json.load(open(os.path.join(VERS, "rev_%s.json" % rev)))
        for sheet in v["diagramsAffected"]:
            hist = [meta[r] for r in REV_ORDER if REV_ORDER.index(r) <= REV_ORDER.index(rev)
                    and sheet in meta[r]["diagramsAffected"]]
            revs_meta = [{"revision": m["revision"], "date": m["createTime"][:10], "comment": m["comment"],
                          "moc": m["moc"], "author": m["createUserName"]} for m in hist]
            doc = draw_sheet(rev, sheet, snap, revs_meta, warnings)
            path = os.path.join(OUT, "%s_Rev%s.dxf" % (sheet, rev))
            doc.saveas(path)
            written.append(path)
    print("wrote", len(written), "DXF files to", OUT)
    for w in warnings:
        print("WARNING:", w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
