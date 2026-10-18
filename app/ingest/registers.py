"""Tag register + valve list -> records[tag]. The valve list holds the official (as-designed) values."""
import json


def ingest(root, kb):
    valves = {v["KKS TAG"]: v for v in json.loads((root / "valve_list" / "unit200_valve_list.json").read_text())}
    for r in json.loads((root / "tag_register.json").read_text()):
        v = valves.get(r["kks"])
        kb["records"][r["kks"]] = {"tag": r["kks"], "legacy": r["legacy"], "type": r["type"],
                                   "description": r["description"], "system": r["system"],
                                   "sheet": v["P&ID"].split()[0] if v else None,
                                   "register": r, "valve_list": v}
