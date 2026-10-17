#!/usr/bin/env python3
"""Generate the Unit 200 Slack history with Gemini and save it in Slack's export format.

  python3 gen_slack.py            real run (needs GEMINI_API_KEY, see below)
  python3 gen_slack.py --mock     no API, writes placeholder text to test the pipeline
  python3 gen_slack.py --check    check the finished export against the story rules

Key: put  GEMINI_API_KEY=your_key  in a file named .env in this folder (or export it).
Optional: GEMINI_MODEL=<model name>  (default below). Each scene is cached in .cache_slack/
so if it stops (rate limit, wifi) just run it again and it picks up where it left off.

Output: slack_export/  users.json, channels.json, <channel>/<YYYY-MM-DD>.json
        slack_export/all_messages.jsonl  (flat copy, one message per line)
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "slack_export")
CACHE = os.path.join(HERE, ".cache_slack")
TZ = ZoneInfo("America/Los_Angeles")
DEFAULT_MODEL = "gemini-2.5-flash"
SLEEP_BETWEEN_CALLS = 7  # seconds; keeps free-tier rate limits happy

PEOPLE = {
    "dokafor": ("U01DOKAFOR", "Dana Okafor",
                "Senior process engineer who designed Unit 200. Terse, explains the why, uses rules of thumb and analogies."),
    "lferreira": ("U02LFERREIRA", "Luis Ferreira",
                  "Operations lead and shift supervisor. Practical shorthand, occasional ALL CAPS, cares what operators can actually do."),
    "praman": ("U03PRAMAN", "Priya Raman",
               "Instrument and controls tech. Precise, cites tag numbers and work orders."),
    "mdelaney": ("U04MDELANEY", "Mark Delaney",
                 "Maintenance planner. Short messages, schedule-focused, mentions work orders."),
    "hcho": ("U05HCHO", "Hannah Cho",
             "HSE and process safety engineer. Formal, references MOC and standards."),
}
CHANNELS = {"unit200-ops": "C01OPS", "unit200-eng": "C02ENG", "moc-reviews": "C03MOC"}

PROMPT = """You are writing a realistic Slack conversation for a fictional gas plant (synthetic demo data).

CHANNEL: #{channel}
DATE: {date} (a {weekday}), conversation starts around {start} local time
PEOPLE IN THIS CONVERSATION:
{people}

WHAT HAPPENS (convey these facts naturally, using the exact numbers and tags given):
{brief}

RULES:
- Sound like real coworkers on Slack: short messages, casual, abbreviations, an occasional typo, rare emoji. People do not summarize or recap.
- Each person only says what their role would know. Do not editorialize about what is missing or contradictory.
- People refer to equipment inconsistently sometimes ("102A", "the reflux pump", "P-102A").
- Use only the numbers, tags and work orders in WHAT HAPPENS. Do not invent new technical facts, figures or document numbers.
- NEVER mention any of these: {avoid}
- Between {lo} and {hi} messages. A few can be thread replies.

Return ONLY JSON, no markdown, in exactly this shape:
{{"messages": [{{"user": "<one of: {handles}>", "text": "...", "minutes_after_start": 0, "thread_parent": null}}]}}
"thread_parent" is null for normal messages, or the integer index (0-based) of an earlier message in this list that this message replies to.
"""


def load_env():
    p = os.path.join(HERE, ".env")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def call_gemini(prompt, model):
    from google import genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    resp = client.models.generate_content(
        model=model, contents=prompt,
        config={"response_mime_type": "application/json", "temperature": 0.9})
    return resp.text


def parse_messages(raw, allowed):
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
    data = json.loads(raw)
    msgs = data["messages"] if isinstance(data, dict) else data
    out = []
    for i, m in enumerate(msgs):
        if m.get("user") not in allowed:
            raise ValueError("unknown user %r" % m.get("user"))
        tp = m.get("thread_parent")
        if tp is not None and not (isinstance(tp, int) and 0 <= tp < i):
            tp = None
        out.append({"user": m["user"], "text": str(m["text"]).strip(),
                    "minutes": max(0, min(600, int(m.get("minutes_after_start", 0)))), "thread_parent": tp})
    if len(out) < 3:
        raise ValueError("too few messages")
    return out


def mock_messages(scene):
    chunks = re.split(r"(?<=[.!?])\s+", scene["brief"])
    out = []
    for i, c in enumerate(chunks):
        out.append({"user": scene["who"][i % len(scene["who"])], "text": "[mock] " + c,
                    "minutes": i * 3, "thread_parent": None})
    return out


def generate_scene(scene, avoid, model, mock):
    path = os.path.join(CACHE, scene["id"] + ".json")
    if os.path.exists(path):
        return json.load(open(path))
    if mock:
        msgs = mock_messages(scene)
    else:
        d = datetime.strptime(scene["date"], "%Y-%m-%d")
        people = "\n".join("- %s (%s): %s" % (h, PEOPLE[h][1], PEOPLE[h][2]) for h in scene["who"])
        prompt = PROMPT.format(channel=scene["channel"], date=scene["date"], weekday=d.strftime("%A"),
                               start=scene["start"], people=people, brief=scene["brief"],
                               avoid="; ".join(avoid), lo=scene["n"][0], hi=scene["n"][1],
                               handles=", ".join(scene["who"]))
        last = None
        for attempt in range(4):
            try:
                msgs = parse_messages(call_gemini(prompt, model), set(scene["who"]))
                break
            except Exception as e:  # rate limit, bad JSON, wrong user, ...
                last = e
                wait = 10 * (attempt + 1)
                print("   %s attempt %d failed (%s: %s), retrying in %ds" % (scene["id"], attempt + 1, type(e).__name__, str(e)[:120], wait))
                time.sleep(wait)
        else:
            raise SystemExit("Giving up on %s: %s\nRun again to resume; finished scenes are cached." % (scene["id"], last))
        time.sleep(SLEEP_BETWEEN_CALLS)
    os.makedirs(CACHE, exist_ok=True)
    json.dump(msgs, open(path, "w"), indent=1)
    return msgs


def build_export(scenes_with_msgs):
    os.makedirs(OUT, exist_ok=True)
    users = [{"id": uid, "name": h, "real_name": name, "profile": {"display_name": name.split()[0].lower(), "real_name": name},
              "is_bot": False, "deleted": False} for h, (uid, name, _) in PEOPLE.items()]
    json.dump(users, open(os.path.join(OUT, "users.json"), "w"), indent=2)

    by_channel = {c: {} for c in CHANNELS}
    flat = []
    for scene, msgs in scenes_with_msgs:
        start = datetime.strptime(scene["date"] + " " + scene["start"], "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
        prev = start
        ts_for_index = {}
        for i, m in enumerate(msgs):
            t = max(start + timedelta(minutes=m["minutes"]), prev)
            prev = t
            ts = "%d.%06d" % (int(t.timestamp()), (i + 1) * 100 + sum(ord(c) for c in scene["id"]) % 97)
            ts_for_index[i] = ts
            rec = {"type": "message", "user": PEOPLE[m["user"]][0], "text": m["text"], "ts": ts,
                   "channel": scene["channel"]}
            if m["thread_parent"] is not None:
                rec["thread_ts"] = ts_for_index[m["thread_parent"]]
            by_channel[scene["channel"]].setdefault(t.strftime("%Y-%m-%d"), []).append(rec)
            flat.append(rec)
    # mark thread parents
    for ch in by_channel.values():
        for day in ch.values():
            reply_counts = {}
            for r in day:
                if "thread_ts" in r:
                    reply_counts[r["thread_ts"]] = reply_counts.get(r["thread_ts"], 0) + 1
            for r in day:
                if r["ts"] in reply_counts:
                    r["thread_ts"] = r["ts"]
                    r["reply_count"] = reply_counts[r["ts"]]

    chans = []
    for name, cid in CHANNELS.items():
        d = os.path.join(OUT, name)
        os.makedirs(d, exist_ok=True)
        for day, recs in by_channel[name].items():
            recs.sort(key=lambda r: r["ts"])
            for r in recs:
                r.pop("channel", None)
            json.dump(recs, open(os.path.join(d, day + ".json"), "w"), indent=2)
        chans.append({"id": cid, "name": name, "created": 1500000000, "members": [u[0] for u in PEOPLE.values()]})
    json.dump(chans, open(os.path.join(OUT, "channels.json"), "w"), indent=2)

    flat.sort(key=lambda r: r["ts"])
    id_to_name = {u[0]: u[1] for u in PEOPLE.values()}
    with open(os.path.join(OUT, "all_messages.jsonl"), "w") as f:
        for r in flat:
            f.write(json.dumps({**r, "user_name": id_to_name[r["user"]],
                                "date": datetime.fromtimestamp(float(r["ts"]), TZ).isoformat()}) + "\n")
    return len(flat)


def check():
    spec = json.load(open(os.path.join(HERE, "scenes.json")))
    texts = {}
    for scene in spec["scenes"]:
        p = os.path.join(CACHE, scene["id"] + ".json")
        if not os.path.exists(p):
            print("MISSING scene", scene["id"])
            continue
        texts[scene["id"]] = " ".join(m["text"] for m in json.load(open(p))).lower()
    bad = 0
    for scene in spec["scenes"]:
        t = texts.get(scene["id"])
        if t is None:
            bad += 1
            continue
        for need in scene["must"]:
            if need.lower() not in t:
                print("%s (%s): expected to see %r" % (scene["id"], scene["date"], need))
                bad += 1
    everything = " ".join(texts.values())
    for forbidden, why in (("p-101b", "gap G01 must stay empty"), ("2 inch", "gap G03"), ('2"', "gap G03"),
                           ("heat duty", "gap G05"), ("vendor", "gap G05"), ("moc-2021", "gap G02 (no MOC for PSV re-rating)")):
        if forbidden in everything:
            print("LEAK: %r appears in the chat (%s)" % (forbidden, why))
            bad += 1
    print("check passed" if bad == 0 else "%d problem(s) found" % bad)
    return 1 if bad else 0


def main(argv):
    load_env()
    if "--check" in argv:
        return check()
    mock = "--mock" in argv
    if not mock and not os.environ.get("GEMINI_API_KEY"):
        print("No GEMINI_API_KEY found. Create a file named .env in this folder containing one line:\n  GEMINI_API_KEY=your_key_here")
        return 2
    model = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
    spec = json.load(open(os.path.join(HERE, "scenes.json")))
    done = []
    for i, scene in enumerate(spec["scenes"], 1):
        print("[%d/%d] %s #%s %s" % (i, len(spec["scenes"]), scene["id"], scene["channel"], scene["date"]))
        done.append((scene, generate_scene(scene, spec["global_avoid"], model, mock)))
    n = build_export(done)
    print("done: %d messages written to %s" % (n, OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
