"""CV runs (base.json + source.pdf from the CV pipeline) -> detections per sheet, when the run's PDF is the
sheet's current drawing. Used only for the overlay; CV reads are never plant facts (the DXF is)."""
import difflib
import hashlib
import json

from pathlib import Path

import config


def _md5(path):
    return hashlib.md5(path.read_bytes()).hexdigest()


def ingest(kb):
    by_pdf = {}
    for sheet, s in kb["sheets"].items():
        if s.get("pdf"):
            try:
                by_pdf[_md5(Path(s["pdf"]))] = sheet
            except FileNotFoundError:
                pass
    tags = list(kb["components"])
    for run in config.CV_RUNS:
        pdf, base = run / "source.pdf", run / "base.json"
        if not (pdf.exists() and base.exists()) or _md5(pdf) not in by_pdf:
            continue
        sheet = by_pdf[_md5(pdf)]
        dets = []
        for o in json.loads(base.read_text())["objects"]:
            known = o["tag"] in kb["components"]
            near = None if known else (difflib.get_close_matches(o["tag"], tags, n=1, cutoff=0.8) or [None])[0]
            dets.append({"tag": o["tag"], "category": o["category"], "bbox": o["bbox"], "confidence": o["confidence"],
                         "in_kb": known, "suggest": near})
        kb["cv"][sheet] = {"run": run.name, "detections": dets}
