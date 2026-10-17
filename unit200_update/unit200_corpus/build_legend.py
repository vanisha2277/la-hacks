#!/usr/bin/env python3
"""Draw the legend sheet for the Unit 200 P&IDs: legend/PID-000_Legend.dxf

Symbols and tag rules follow the project legend: instrument pills (function letters over the KKS tag),
valve typicals with a tag pill and leader, open/closed valve status, line types, fail positions,
and the KKS identification table with its number ranges.
"""
import os

import ezdxf
from ezdxf.enums import TextEntityAlignment as A

import build_dxf as B
from dxf_common import SHEET_H, SHEET_W  # noqa
import kks

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "legend")


def main():
    doc = ezdxf.new("R2010", setup=True)
    for name in ("SYMBOLS", "PROCESS", "UTILITY", "RELIEF", "SIGNAL", "IMPULSE", "FRAME", "ANNOT", "TITLE"):
        doc.layers.add(name, color=7)
    doc.layers.get("SIGNAL").dxf.linetype = "DASHED"; doc.layers.get("IMPULSE").dxf.linetype = "DASHED"
    B.make_blocks(doc)
    msp = doc.modelspace()
    B.draw_frame(msp)
    T = lambda s, x, y, h=3.0, layer="ANNOT", al=A.MIDDLE_LEFT: msp.add_text(s, height=h, dxfattribs={"layer": layer}).set_placement((x, y), align=al)

    def header(x0, x1, title):
        msp.add_line((x0, 700), (x1, 700), dxfattribs={"layer": "FRAME"})
        T(title, (x0 + x1) / 2, 712, 6, "ANNOT", A.MIDDLE_CENTER)

    def sym(block, x, y, **att):
        r = msp.add_blockref(block, (x, y), dxfattribs={"layer": "SYMBOLS"})
        r.add_auto_attribs(att)

    # column rules
    for x in (270, 520, 760):
        msp.add_line((x, 20), (x, 726), dxfattribs={"layer": "FRAME"})
    header(20, 270, "VALVES"); header(270, 520, "INSTRUMENTS"); header(520, 760, "EQUIPMENT"); header(760, 980, "LINES")

    # ---- valves
    T("OPEN", 60, 676, 2.6, al=A.MIDDLE_CENTER); T("CLOSED", 120, 676, 2.6, al=A.MIDDLE_CENTER)
    y = 650
    for x, closed in ((60, False), (120, True)):
        for sx in (-1, 1):
            pts = [(x + sx * 12, y + 8), (x, y), (x + sx * 12, y - 8)]
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "SYMBOLS"})
            if closed:
                h = msp.add_hatch(color=7, dxfattribs={"layer": "SYMBOLS"}); h.paths.add_polyline_path(pts, is_closed=True)
    T("GATE / GENERIC VALVE", 150, y, 2.8)
    y = 600
    sym("CTRLVALVE", 60, y, TAG="NNAAANNAANNN", ISA="FCV", DESC="")
    T("PNEUMATIC CONTROL VALVE", 150, y, 2.8); T("(DIAPHRAGM ACTUATOR)", 150, y - 8, 2.4)
    y = 540
    sym("MANVALVE", 60, y, TAG="NNAAANNAANNN", ISA="HV", DESC="")
    T("HAND VALVE, NORMALLY CLOSED", 150, y, 2.8)
    y = 480
    sym("CHECKVALVE", 60, y, TAG="NNAAANNAANNN", ISA="NRV", DESC="")
    T("CHECK VALVE (NRV)", 150, y, 2.8)
    y = 420
    sym("RELIEFVALVE", 60, y, TAG="NNAAANNAANNN", ISA="PSV", DESC="")
    T("PRESSURE SAFETY VALVE", 150, y, 2.8)
    y = 350
    for i, (code, txt) in enumerate((("F.O.", "FAIL OPEN"), ("F.C.", "FAIL CLOSE"), ("F.L.", "FAIL LAST (LOCK)"))):
        T(code, 40, y - i * 16, 2.8); T(txt, 80, y - i * 16, 2.8)
    T("SOLID = NORMALLY CLOSED", 40, 280, 2.6); T("HOLLOW = NORMALLY OPEN", 40, 268, 2.6)

    # ---- instruments
    y = 650
    sym("INSTR_XMTR", 330, y, TAG="NNAAANNAANNN", ISA="FT", DESC=""); T("FIELD (LOCAL) INSTRUMENT", 375, y, 2.8)
    y = 610
    sym("INSTR_CTRL", 330, y, TAG="NNAAANNAANNN", ISA="FIC", DESC=""); T("DCS FUNCTION (BAR ACROSS)", 375, y, 2.8)
    y = 570
    sym("INSTR_SWITCH", 330, y, TAG="NNAAANNAANNN", ISA="PSL", DESC=""); T("SWITCH / ALARM", 375, y, 2.8)
    T("ISA letters on top, KKS tag below.", 290, 535, 2.6)
    T("First letter: F flow, L level, P pressure,", 290, 522, 2.6)
    T("T temperature. Then: T transmitter,", 290, 510, 2.6)
    T("I indicator, C controller, S switch,", 290, 498, 2.6)
    T("AL alarm low, AH alarm high, LL low-low.", 290, 486, 2.6)
    T("KKS TAG: UU SSS NN AA NNN", 290, 440, 3.5)
    T("UU unit, SSS system code, NN system no,", 290, 426, 2.6)
    T("AA item code, NNN item no.", 290, 414, 2.6)
    T("Example: 20LFC20AA102 (LCV)", 290, 396, 2.8)
    T("ITEM CODES", 290, 372, 3.2)
    for i, line in enumerate(("AA valve", "AC heat exchanger", "AP pump", "AT column / separator", "BB vessel / drum",
                              "CF flow  CL level  CP pressure  CT temperature")):
        T(line, 290, 358 - i * 12, 2.6)
    T("NUMBER RANGES (AA valves)", 290, 270, 3.2)
    for i, line in enumerate(("001-100 valves in main pipes", "101-150 control valves", "151-190 pressure reducers",
                              "191-199 safety valves", "251-299 pneumatic shut-off valves",
                              "Instruments: 001-100 transmitter / controller", "101-199 switch / alarm")):
        T(line, 290, 256 - i * 12, 2.6)

    # ---- equipment
    for i, (blk_, isa, tg, txt) in enumerate((("PUMP", "", "20LFC20AP001", "CENTRIFUGAL PUMP"),
                                              ("VESSEL", "", "20LFC20BB001", "VESSEL / DRUM"),
                                              ("HEATEX", "", "20LFC20AC001", "HEAT EXCHANGER"),
                                              ("COLUMN", "", "20LFC10AT001", "COLUMN"))):
        yy = [650, 600, 548, 360][i]
        sym(blk_, 570, yy, TAG=tg, DESC="", ISA=isa)
        T(txt, 620, yy, 2.8)
    sym("OFFPAGE", 590, 120, TAG="PID-200", DESC="")
    T("CONNECTOR TO OTHER P&ID", 640, 120, 2.8)

    # ---- lines
    y = 650
    for layer, txt, ltype in (("PROCESS", "PROCESS LINE", None), ("UTILITY", "UTILITY LINE (STEAM, WATER)", None),
                              ("RELIEF", "RELIEF LINE", None), ("SIGNAL", "INSTRUMENT / ELECTRIC SIGNAL", "DASHED"),
                              ("IMPULSE", "IMPULSE (SENSING) LINE", "DASHED")):
        msp.add_line((780, y), (850, y), dxfattribs={"layer": layer})
        T(txt, 860, y, 2.6); y -= 24
    T("PIPE FLAG", 780, 500, 3.2)
    msp.add_lwpolyline([(790, 460), (830, 460), (830, 484), (790, 484)], close=True, dxfattribs={"layer": "ANNOT"})
    msp.add_line((790, 472), (830, 472), dxfattribs={"layer": "ANNOT"})
    T("20LFC20", 810, 478, 2.6, al=A.MIDDLE_CENTER); T("BR001", 810, 466, 2.6, al=A.MIDDLE_CENTER)
    T("DN 100 1C1", 810, 452, 2.6, al=A.MIDDLE_CENTER)
    T("system code / BR pipe no.", 840, 478, 2.4); T("nominal diameter, pipe class", 840, 452, 2.4)
    T("SYSTEM CODES (UNIT 20)", 780, 410, 3.2)
    for i, (k, v) in enumerate(kks.SYSTEMS.items()):
        T("%s  %s" % (k, v), 780, 394 - i * 13, 2.5)

    # title block
    B_title = ["MERIDIAN GAS PROCESSING - HARBOR TERMINAL", "SYNTHETIC DEMO DATA - NOT A REAL PLANT", "LEGEND FOR UNIT 200 P&IDs",
               "DWG NO: PID-000", "REV: 0"]
    msp.add_lwpolyline([(740, 16), (984, 16), (984, 78), (740, 78)], close=True, dxfattribs={"layer": "TITLE"})
    for i, line in enumerate(B_title):
        T(line, 746, 70 - i * 10.5, 3.4, "TITLE")
    os.makedirs(OUT, exist_ok=True)
    doc.saveas(os.path.join(OUT, "PID-000_Legend.dxf"))
    print("wrote legend/PID-000_Legend.dxf")


if __name__ == "__main__":
    main()
