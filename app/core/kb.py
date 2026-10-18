"""Knowledge base: one JSON-serializable dict. Senior writes live in a separate state file so rebuilds keep them."""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB_PATH = ROOT / "out" / "kb.json"
STATE_PATH = ROOT / "data" / "user_state.json"  # senior notes / corrections / flags

COLLECTIONS = {"sheets": dict, "components": dict, "links": list, "offpage": list, "sources": dict,
               "mentions": list, "contexts": dict, "records": dict, "revisions": list, "gaps": list,
               "notes": list, "corrections": list, "cv": dict}
STATE_KEYS = ("notes", "corrections", "flags")


def empty():
    return {k: t() for k, t in COLLECTIONS.items()}


def save(kb, path=KB_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(kb, indent=1))


def load(path=KB_PATH):
    kb = json.loads(Path(path).read_text())
    state = load_state()
    kb["notes"] = kb.get("notes", []) + state["notes"]
    kb["corrections"] = state["corrections"]
    kb["gaps"] = kb["gaps"] + [flag_to_gap(f) for f in state["flags"]]
    return kb


def load_state():
    try:
        s = json.loads(STATE_PATH.read_text())
    except FileNotFoundError:
        s = {}
    return {k: s.get(k, []) for k in STATE_KEYS}


def append_state(key, item):
    """Persist one senior write. Returns the item with an id assigned."""
    # ponytail: read-modify-write without locking; fine for one demo laptop
    state = load_state()
    prefix = {"notes": "note", "corrections": "corr", "flags": "flag"}[key]
    item = {"id": f"{prefix}-{len(state[key]) + 1:03d}",
            "date": date.today().isoformat()} | item
    state[key].append(item)
    STATE_PATH.write_text(json.dumps(state, indent=1))
    return item


def flag_to_gap(f):
    return {"id": f"gap-{f['id']}", "type": "flagged_by_senior", "severity": "medium",
            "tags": f["tags"], "issue": f["description"], "sources": [f["id"]]}
