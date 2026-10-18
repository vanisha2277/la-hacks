"""Drawings: DXF -> sheets, components, links, offpage, via the corpus's own extract_dxf.py (vector CAD, exact).
Only this file changes if drawings arrive another way (e.g. CV output for scanned PDFs)."""
import re
import subprocess
import sys
from pathlib import Path

import config
from core.tags import decode

# drawing edge kind -> (our relation, reverse?). impulse/relief edges point equipment -> instrument; we store
# "instrument measures equipment" and "PSV protects equipment".
RELATION = {"process": ("flows_to", False), "signal": ("signal", False), "utility": ("utility", False),
            "impulse": ("measures", True), "relief": ("protects", True)}


def page_box(rect, page_w, page_h, sheet_w, sheet_h):
    """DXF rect (y up) -> page-point box (y down), as matplotlib laid it out: equal aspect, centred."""
    k = min(page_w / sheet_w, page_h / sheet_h)
    ox, oy = (page_w - sheet_w * k) / 2, (page_h - sheet_h * k) / 2
    x0, y0, x1, y1 = rect
    return [round(ox + x0 * k, 2), round(oy + (sheet_h - y1) * k, 2), round(ox + x1 * k, 2), round(oy + (sheet_h - y0) * k, 2)]


def extractor():
    """Import the teammate's extract_dxf, warning if their repo moved off the pinned commit."""
    try:
        head = subprocess.run(["git", "-C", str(config.CORPUS_DIR), "rev-parse", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
        if head and head != config.CORPUS_COMMIT:
            print(f"WARNING: corpus at {head[:7]}, pinned {config.CORPUS_COMMIT[:7]}. Re-check extract_dxf before trusting the build.")
    except FileNotFoundError:
        pass
    if str(config.CORPUS_DIR) not in sys.path:
        sys.path.insert(0, str(config.CORPUS_DIR))
    import extract_dxf
    return extract_dxf


def ingest(kb):
    x = extractor()
    g = x.extract_plant(x.REV_ORDER[-1])
    if g["issues"]:
        print("extractor issues:", *g["issues"], sep="\n  ")
    current = {}
    for r in g["revisions"]:
        current[r["sheet"]] = r  # sorted by rev order, so last wins
    for sheet, title in x.SHEETS.items():
        rev = current.get(sheet, {})
        kb["sheets"][sheet] = {"id": sheet, "title": title, "rev": rev.get("revision"), "rev_date": rev.get("date")}

    # page geometry: the corpus renders each DXF to SVG/PDF; boxes go in page points, origin top-left
    import dxf_common  # corpus module, on sys.path via extractor()
    files = x.files_for_rev(x.REV_ORDER[-1])
    boxes = {}
    for sheet, path in files.items():
        svg = config.CORPUS_DIR / "drawings" / Path(path).with_suffix(".svg").name
        if svg.exists():
            w, h = map(float, re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg.read_text()[:2000]).groups())
            kb["sheets"][sheet] |= {"svg": str(svg), "pdf": str(svg.with_suffix(".pdf")), "page_size": [w, h]}
            for sym in x.read_sheet(path)["symbols"]:
                if "TAG" in sym["attrs"]:
                    boxes[sym["attrs"]["TAG"]] = page_box(sym["rect"], w, h, dxf_common.SHEET_W, dxf_common.SHEET_H)

    nodes = {n["id"]: n for n in g["nodes"]}
    for n in g["nodes"]:
        if n["type"] != "offpage":
            kb["components"][n["id"]] = {"tag": n["id"], "kind": n["type"], "desc": n["label"], "sheet": n["diagram"],
                                         "attrs": n["attrs"], "decoded": decode(n["id"]), "bbox": boxes.get(n["id"])}

    for e in g["edges"]:
        a, b = nodes[e["from"]], nodes[e["to"]]
        if "offpage" in (a["type"], b["type"]):
            op, real = (a, b) if a["type"] == "offpage" else (b, a)
            m = re.search(r"PID-\d+", op["label"])
            kb["offpage"].append({"from": real["id"], "from_sheet": real["diagram"], "to": op["id"],
                                  "to_sheet": m.group(0) if m else None, "label": op["label"], "line": e["line"],
                                  "direction": "out" if real is a else "in"})
            continue
        rel, rev = RELATION[e["kind"]]
        f, t = (e["to"], e["from"]) if rev else (e["from"], e["to"])
        kb["links"].append({"from": f, "to": t, "relation": rel, "status": "seen", "line": e["line"],
                            "source": f"drawing:{e['sheet']}"})
        if a["diagram"] != b["diagram"]:
            kb["offpage"].append({"from": e["from"], "from_sheet": a["diagram"], "to": e["to"],
                                  "to_sheet": b["diagram"], "label": e["line"], "line": e["line"], "direction": "out"})
