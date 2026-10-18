"""Calendar export (events.json) -> one source per event, linked to its meeting notes doc if any."""
import json


def ingest(root, kb):
    names = {u["name"]: u.get("real_name") or u["name"]
             for u in json.loads((root / "slack_export" / "users.json").read_text())}
    notes = {d["fileId"]: f"drive-{d['slug']}" for d in json.loads((root / "drive_export" / "drive_index.json").read_text())}
    for e in json.loads((root / "calendar_export" / "events.json").read_text()):
        sid = f"cal-{e['id']}"
        who = ", ".join(names.get(a.split("@")[0], a) for a in e.get("attendees", []))
        text = f"{e['summary']}. {e.get('description', '')} Location: {e.get('location', '')}. Attendees: {who}."
        kb["sources"][sid] = {"id": sid, "kind": "calendar", "text": text, "author": "calendar",
                              "date": e["start"][:10], "title": e["summary"], "link": None, "context": sid,
                              "notes": notes.get(e.get("notesFileId"))}
        kb["contexts"][sid] = {"id": sid, "kind": "calendar", "title": e["summary"], "sources": [sid]}
