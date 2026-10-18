"""Revisions: each sheet's DXF revision table + what actually changed (DXF diff vs the previous rev)
+ who issued it (versions_api.json, the drawing file's version history)."""
import json

import config
from ingest.drawings import extractor


def ingest(kb):
    x = extractor()
    try:
        api = {v["revision"]: v for v in json.loads((config.CORPUS_DIR / "versions" / "versions_api.json").read_text())["data"]}
    except FileNotFoundError:
        api = {}
    plants = {r: x.extract_plant(r) for r in x.REV_ORDER}
    for r in plants[x.REV_ORDER[-1]]["revisions"]:
        rev, sheet = r["revision"], r["sheet"]
        i = x.REV_ORDER.index(rev)
        changes, tags = [], set()
        if i:
            d = x.diff(plants[x.REV_ORDER[i - 1]], plants[rev])
            on_sheet = {n["id"] for n in plants[rev]["nodes"] if n["diagram"] == sheet} | set(d["removed_nodes"])
            changes += [f"added {t}" for t in d["added_nodes"] if t in on_sheet]
            changes += [f"removed {t}" for t in d["removed_nodes"] if t in on_sheet]
            changes += [f"{c['node']} {c['attr']}: {c['from']} -> {c['to']}" for c in d["changed_attrs"] if c["node"] in on_sheet]
            tags |= {t for t in d["added_nodes"] + d["removed_nodes"] if t in on_sheet}
            tags |= {c["node"] for c in d["changed_attrs"] if c["node"] in on_sheet}
        kb["revisions"].append({"id": f"rev:{sheet}-{rev}", "sheet": sheet, "rev": rev, "date": r["date"],
                                "author": api.get(rev, {}).get("createUserName"), "description": r["description"],
                                "moc": r["moc"], "changes": changes, "tags": sorted(tags & set(kb["components"]))})
