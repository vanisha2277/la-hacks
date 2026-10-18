"""Slack export (users.json, channels.json, <channel>/<day>.json) -> one source per message, grouped into
conversations: a thread if the message has thread_ts, else same channel with gaps <= 30 min."""
import json
from datetime import datetime, timezone

GAP_S = 30 * 60


def ingest(root, kb):
    root = root / "slack_export"
    users = {u["id"]: u.get("real_name") or u["name"] for u in json.loads((root / "users.json").read_text())}
    for ch in json.loads((root / "channels.json").read_text()):
        name = ch["name"]
        msgs = [m for f in sorted((root / name).glob("*.json")) for m in json.loads(f.read_text())
                if m.get("type") == "message" and m.get("text")]
        msgs.sort(key=lambda m: float(m["ts"]))  # thread replies live in the file of the day they were written
        last_ts, conv = None, None
        for m in msgs:
            ts = float(m["ts"])
            if m.get("thread_ts"):
                cid = f"slack-{name}-thread-{m['thread_ts']}"
            else:
                if last_ts is None or ts - last_ts > GAP_S:
                    conv = f"slack-{name}-{m['ts']}"
                cid, last_ts = conv, ts
            sid = f"slack-{name}-{m['ts']}"
            when = datetime.fromtimestamp(ts, timezone.utc)
            kb["sources"][sid] = {"id": sid, "kind": "slack", "text": m["text"],
                                  "author": users.get(m.get("user"), m.get("user")),
                                  "date": when.strftime("%Y-%m-%d %H:%M UTC"), "title": f"#{name}", "link": None,
                                  "context": cid}
            ctx = kb["contexts"].setdefault(cid, {"id": cid, "kind": "slack", "sources": [],
                                                  "title": f"#{name} conversation {when:%Y-%m-%d}"})
            ctx["sources"].append(sid)
