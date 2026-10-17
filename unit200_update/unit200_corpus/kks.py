#!/usr/bin/env python3
"""KKS tag register for Unit 200 (single source of truth).

Tag structure copied from the example valve list:

    20 LFC 20 AA 102
    |  |   |  |  |
    |  |   |  |  +-- first sequence number (valves: 001-100 main-pipe valves, 101-150 control valves, 151-190 PRV, 191-199 safety valves,
    |  |   |  |                      251-299 pneumatic shut-off; instruments: 001-100 transmitter/controller, 101-199 switch/alarm)
    |  |   |  +----- item code   (AA valve, AP pump, AC heat exchanger, BB vessel, AT column,
    |  |   |                      CF flow, CL level, CP pressure, CT temperature)
    |  |   +-------- system sequence number (sub-system or train)
    |  +------------ system code (3 letters)
    +--------------- unit number

The TYPE column is the ISA instrument/valve type (FCV, LCV, PSV, FIC ...), like the example sheet.
The system codes below are INVENTED for this fictional plant. They are not a real KKS catalogue.

Old tags (V-102, LV-202 ...) are kept as `legacy` so people and the agent can still resolve them.
"""
import json
import os
import re

UNIT = "20"

SYSTEMS = {
    "LFB10": "FEED SURGE AND FEED PUMPS",
    "LFB20": "FEED PREHEAT",
    "LFC10": "SPLITTER COLUMN AND PRESSURE CONTROL",
    "LFC20": "OVERHEAD CONDENSING AND REFLUX",
    "LFC30": "REBOILER AND TEMPERATURE CONTROL",
    "LFD10": "BOTTOMS TO STORAGE",
}

ITEM_CODES = {
    "AA": "valve", "AP": "pump", "AC": "heat exchanger", "BB": "vessel / drum", "AT": "column / separator",
    "CF": "flow measurement", "CL": "level measurement", "CP": "pressure measurement", "CT": "temperature measurement",
}

# legacy tag -> (kks suffix after UNIT, ISA TYPE, DESCRIPTION in the valve-list style, node type, diagram)
_R = [
    ("V-101",   "LFB10BB001", "VESSEL",  "FEED SURGE DRUM"),
    ("P-101A",  "LFB10AP001", "PUMP",    "FEED PUMP A"),
    ("P-101B",  "LFB10AP002", "PUMP",    "FEED PUMP B"),
    ("FV-101",  "LFB10AA101", "FCV",     "FEED FLOW CONTROL VALVE"),
    ("FT-101",  "LFB10CF001", "FT",      "FEED FLOW TRANSMITTER"),
    ("FIC-101", "LFB10CF002", "FIC",     "FEED FLOW CONTROLLER"),
    ("LT-101",  "LFB10CL001", "LT",      "FEED SURGE DRUM LEVEL TRANSMITTER"),
    ("PSL-101", "LFB10CP101", "PSL",     "FEED PUMP LOW DISCHARGE PRESSURE SWITCH"),
    ("E-101",   "LFB20AC001", "HX",      "FEED/BOTTOMS EXCHANGER"),
    ("BV-101",  "LFB20AA001", "HV",      "FEED PREHEAT BYPASS"),
    ("C-101",   "LFC10AT001", "COLUMN",  "C3/C4 SPLITTER COLUMN"),
    ("PT-201",  "LFC10CP001", "PT",      "COLUMN PRESSURE TRANSMITTER"),
    ("PIC-201", "LFC10CP002", "PIC",     "COLUMN PRESSURE CONTROLLER"),
    ("PV-201",  "LFC10AA101", "PCV",     "CONDENSER COOLING WATER VALVE"),
    ("PSV-201", "LFC10AA191", "PSV",     "COLUMN RELIEF VALVE"),
    ("E-102",   "LFC20AC001", "HX",      "OVERHEAD CONDENSER"),
    ("V-102",   "LFC20BB001", "VESSEL",  "REFLUX DRUM"),
    ("P-102A",  "LFC20AP001", "PUMP",    "REFLUX PUMP A"),
    ("P-102B",  "LFC20AP002", "PUMP",    "REFLUX PUMP B"),
    ("CV-102A", "LFC20AA011", "NRV",     "REFLUX PUMP A DISCHARGE CHECK VALVE"),
    ("CV-102B", "LFC20AA012", "NRV",     "REFLUX PUMP B DISCHARGE CHECK VALVE"),
    ("FT-201",  "LFC20CF001", "FT",      "REFLUX FLOW TRANSMITTER"),
    ("FIC-201", "LFC20CF002", "FIC",     "REFLUX FLOW CONTROLLER"),
    ("FAL-201", "LFC20CF101", "FAL",     "REFLUX LOW FLOW ALARM"),
    ("FV-201",  "LFC20AA101", "FCV",     "REFLUX FLOW CONTROL VALVE"),
    ("LT-202",  "LFC20CL001", "LT",      "REFLUX DRUM LEVEL TRANSMITTER"),
    ("LIC-202", "LFC20CL002", "LIC",     "REFLUX DRUM LEVEL CONTROLLER"),
    ("LSLL-202", "LFC20CL101", "LSLL",   "REFLUX DRUM LOW-LOW LEVEL TRIP"),
    ("LV-202",  "LFC20AA102", "LCV",     "REFLUX DRUM PRODUCT LEVEL CONTROL VALVE"),
    ("E-103",   "LFC30AC001", "HX",      "REBOILER"),
    ("TT-203",  "LFC30CT001", "TT",      "COLUMN TEMPERATURE TRANSMITTER"),
    ("TIC-203", "LFC30CT002", "TIC",     "COLUMN TEMPERATURE CONTROLLER"),
    ("TV-203",  "LFC30AA101", "TCV",     "REBOILER STEAM CONTROL VALVE"),
    ("TAH-301", "LFD10CT101", "TAH",     "STORAGE FEED HIGH TEMPERATURE ALARM"),
]

REGISTER = []
LEGACY_TO_KKS = {}
KKS_TO_LEGACY = {}
for legacy, suffix, isa, desc in _R:
    kks = UNIT + suffix
    m = re.fullmatch(r"(\d\d)([A-Z]{3})(\d\d)([A-Z]{2})(\d{3})", kks)
    assert m, kks
    REGISTER.append({
        "kks": kks, "legacy": legacy, "type": isa, "description": desc,
        "unit_no": m.group(1), "system_code": m.group(2), "system_seq": int(m.group(3)),
        "item_code": m.group(4), "first_seq": int(m.group(5)),
        "system": SYSTEMS[m.group(2) + m.group(3)],
    })
    LEGACY_TO_KKS[legacy] = kks
    KKS_TO_LEGACY[kks] = legacy
assert len(set(LEGACY_TO_KKS.values())) == len(LEGACY_TO_KKS)

_PAT = re.compile(r"(?<![A-Za-z0-9\-])(%s)(?![A-Za-z0-9])" %
                  "|".join(sorted((re.escape(k) for k in LEGACY_TO_KKS), key=len, reverse=True)), re.I)


def relabel(text):
    """Replace legacy tags with KKS tags, keeping lower/upper case of the original."""
    def sub(m):
        k = LEGACY_TO_KKS[m.group(1).upper()]
        return k.lower() if m.group(1).islower() or (m.group(1).lower() == m.group(1)) else k
    return _PAT.sub(sub, text)


def write_register(path):
    json.dump(REGISTER, open(path, "w"), indent=2)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    write_register(os.path.join(here, "tag_register.json"))
    print("wrote tag_register.json with %d tags" % len(REGISTER))
