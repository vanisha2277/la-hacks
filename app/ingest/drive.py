"""Drive export: markdown files with front matter (listed in drive_index.json) -> one passage per '## ' section.
Meeting notes have no sections, so they are one passage."""
import json
import re

FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def front_matter(text):
    m = FRONT.match(text)
    meta = {}
    for line in (m.group(1).splitlines() if m else []):
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip().strip('"')
    return meta, text[m.end():] if m else text


def ingest(root, kb):
    for d in json.loads((root / "drive_export" / "drive_index.json").read_text()):
        meta, body = front_matter((root / d["path"]).read_text())
        cid = f"drive-{d['slug']}"
        kb["contexts"][cid] = {"id": cid, "kind": d["kind"], "title": d["name"], "sources": [], "file_id": d["fileId"]}
        chunks = [c.strip() for c in re.split(r"(?m)^(?=## )", body) if c.strip()]
        for i, text in enumerate(chunks, 1):
            sid = f"drive-{d['slug']}-{i:02d}"
            kb["sources"][sid] = {"id": sid, "kind": "drive", "doc_kind": d["kind"], "text": text,
                                  "author": d["owners"][0]["displayName"], "date": d["modifiedTime"][:10],
                                  "title": d["name"], "link": None, "path": d["path"], "context": cid}
            kb["contexts"][cid]["sources"].append(sid)
