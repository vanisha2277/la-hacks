"""Shared constants for the Unit 200 DXF drawer and extractor."""

SHEET_W, SHEET_H = 1000, 760
REV_ORDER = ["A", "0", "1", "2", "3", "4", "5"]
SHEETS = {"PID-100": "Feed and Preheat", "PID-200": "Column and Overhead"}

# node type -> (block name, bbox x0, y0, x1, y1 relative to insertion point)
SYMBOLS = {
    "pump":           ("PUMP",           (-15, -15, 15, 15)),
    "vessel":         ("VESSEL",         (-35, -22, 35, 22)),
    "column":         ("COLUMN",         (-20, -130, 20, 130)),
    "heat_exchanger": ("HEATEX",         (-25, -12, 25, 12)),
    "control_valve":  ("CTRLVALVE",      (-12, -8, 12, 22)),
    "manual_valve":   ("MANVALVE",       (-12, -8, 12, 8)),
    "check_valve":    ("CHECKVALVE",     (-10, -10, 10, 10)),
    "relief_valve":   ("RELIEFVALVE",    (-10, -10, 10, 10)),
    "transmitter":    ("INSTR_XMTR",     (-14, -14, 14, 14)),
    "controller":     ("INSTR_CTRL",     (-14, -14, 14, 14)),
    "switch":         ("INSTR_SWITCH",   (-14, -14, 14, 14)),
    "alarm":          ("INSTR_ALARM",    (-14, -14, 14, 14)),
    "offpage":        ("OFFPAGE",        (-30, -12, 30, 12)),
}
REF_BLOCK = ("OFFPAGE_REF", (-30, -12, 30, 12))

BLOCK_TO_TYPE = {v[0]: k for k, v in SYMBOLS.items()}
BLOCK_BBOX = {v[0]: v[1] for v in SYMBOLS.values()}
BLOCK_BBOX[REF_BLOCK[0]] = REF_BLOCK[1]

# layer per edge kind
KIND_LAYER = {"process": "PROCESS", "utility": "UTILITY", "relief": "RELIEF",
              "signal": "SIGNAL", "impulse": "IMPULSE"}
LAYER_KIND = {v: k for k, v in KIND_LAYER.items()}

# data table columns (x offsets inside the table)
TABLE_X = 750
TABLE_COLS = (TABLE_X, TABLE_X + 65, TABLE_X + 175)
