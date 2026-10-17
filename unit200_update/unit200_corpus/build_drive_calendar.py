#!/usr/bin/env python3
"""Write drive_export/ (docs + meeting notes as Markdown with Drive-style metadata),
calendar_export/unit200_ops.ics, and index files. Then run checks.

  python3 build_drive_calendar.py          build everything
  python3 build_drive_calendar.py --check  consistency checks only
"""
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import date, datetime, time as dtime, timedelta, timezone

from drive_content import DOCS, EVENTS, NOTES

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVE = os.path.join(HERE, "drive_export")
CAL = os.path.join(HERE, "calendar_export")

PEOPLE = {
    "dokafor": ("Dana Okafor", "dokafor@meridian-gas.example"),
    "lferreira": ("Luis Ferreira", "lferreira@meridian-gas.example"),
    "praman": ("Priya Raman", "praman@meridian-gas.example"),
    "mdelaney": ("Mark Delaney", "mdelaney@meridian-gas.example"),
    "hcho": ("Hannah Cho", "hcho@meridian-gas.example"),
}


def la_tz(naive):
    def nth_sunday(y, m, n):
        first = date(y, m, 1)
        return first + timedelta(days=(6 - first.weekday()) % 7 + 7 * (n - 1))
    start = datetime.combine(nth_sunday(naive.year, 3, 2), dtime(2))
    end = datetime.combine(nth_sunday(naive.year, 11, 1), dtime(2))
    return timezone(timedelta(hours=-7 if start <= naive < end else -8))


def utc_iso(day, hhmm="09:00"):
    naive = datetime.strptime(day + " " + hhmm, "%Y-%m-%d %H:%M")
    return naive.replace(tzinfo=la_tz(naive)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def file_id(slug):
    return "1" + hashlib.md5(("unit200:" + slug).encode()).hexdigest()


def slugify(name):
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")


def build():
    for d in (DRIVE, CAL):
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d)
    index = []
    for kind, items in (("doc", DOCS), ("meeting_notes", NOTES)):
        for slug, title, folder, owner, created, modified, body in items:
            name, email = PEOPLE[owner]
            fid = file_id(slug)
            meta = {"fileId": fid, "name": title, "mimeType": "application/vnd.google-apps.document",
                    "kind": kind, "folder": "Unit 200 / " + folder,
                    "owners": [{"displayName": name, "emailAddress": email}],
                    "createdTime": utc_iso(created), "modifiedTime": utc_iso(modified, "15:30"), "slug": slug}
            fm = "---\n" + "\n".join("%s: %s" % (k, json.dumps(v) if not isinstance(v, str) else v if re.match(r"^[\w .:/\-]+$", v) else json.dumps(v))
                                     for k, v in meta.items() if k != "owners") + \
                 "\nowner: %s <%s>\n---\n\n" % (name, email)
            path = os.path.join(DRIVE, folder, slug + ".md")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "w").write(fm + body.strip() + "\n")
            meta["path"] = os.path.relpath(path, HERE)
            index.append(meta)
    json.dump(index, open(os.path.join(DRIVE, "drive_index.json"), "w"), indent=2)
    slug_to_id = {m["slug"]: m["fileId"] for m in index}

    def esc(s):
        return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

    def fold(line):
        out, line_b = [], line
        while len(line_b.encode()) > 74:
            cut = 74
            while len(line_b[:cut].encode()) > 74:
                cut -= 1
            out.append(line_b[:cut]); line_b = " " + line_b[cut:]
        out.append(line_b)
        return "\r\n".join(out)

    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Meridian Harbor//Unit 200 Ops//EN", "CALSCALE:GREGORIAN",
             "X-WR-CALNAME:Unit 200 Ops"]
    events_json = []
    for ev in EVENTS:
        uid = "%s-%s@meridian-gas.example" % (ev["id"].lower(), ev["date"])
        desc = ev["desc"]
        if ev["notes"]:
            desc += "\nMeeting notes: drive file %s (%s)" % (slug_to_id[ev["notes"]], ev["notes"])
        lines += ["BEGIN:VEVENT", "UID:" + uid, "DTSTAMP:" + utc_iso(ev["date"], "08:00").replace("-", "").replace(":", "")]
        if ev["start"]:
            start = utc_iso(ev["date"], ev["start"])
            naive = datetime.strptime(ev["date"] + " " + ev["start"], "%Y-%m-%d %H:%M")
            end = (naive + timedelta(minutes=ev["minutes"])).replace(tzinfo=la_tz(naive)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            lines += ["DTSTART:" + start.replace("-", "").replace(":", ""), "DTEND:" + end.replace("-", "").replace(":", "")]
        else:  # all-day, Mon-Fri week
            d0 = datetime.strptime(ev["date"], "%Y-%m-%d")
            start, end = ev["date"], (d0 + timedelta(days=5)).strftime("%Y-%m-%d")
            lines += ["DTSTART;VALUE=DATE:" + start.replace("-", ""), "DTEND;VALUE=DATE:" + end.replace("-", "")]
        lines += ["SUMMARY:" + esc(ev["summary"]), "DESCRIPTION:" + esc(desc), "LOCATION:" + esc(ev["location"]),
                  "ORGANIZER;CN=%s:mailto:%s" % (PEOPLE[ev["attendees"][0]][0], PEOPLE[ev["attendees"][0]][1])]
        for a in ev["attendees"]:
            lines.append("ATTENDEE;CN=%s:mailto:%s" % (PEOPLE[a][0], PEOPLE[a][1]))
        lines.append("END:VEVENT")
        events_json.append({"id": ev["id"], "uid": uid, "start": start, "end": end, "summary": ev["summary"],
                            "description": desc, "location": ev["location"],
                            "attendees": [PEOPLE[a][1] for a in ev["attendees"]],
                            "notesFileId": slug_to_id.get(ev["notes"]) if ev["notes"] else None})
    lines.append("END:VCALENDAR")
    open(os.path.join(CAL, "unit200_ops.ics"), "w", newline="").write("\r\n".join(fold(l) for l in lines) + "\r\n")
    json.dump(events_json, open(os.path.join(CAL, "events.json"), "w"), indent=2)
    print("wrote %d docs, %d meeting notes, %d calendar events" % (len(DOCS), len(NOTES), len(EVENTS)))


# --------------------------------------------------------------------------- checks
def read_all():
    texts = {}
    for _, items in (("d", DOCS), ("n", NOTES)):
        for slug, title, folder, owner, c, m, body in items:
            texts[slug] = (title + "\n" + body).lower()
    return texts


def check():
    texts = read_all()
    everything = "\n".join(texts.values())
    problems = []

    # gaps must stay empty in docs and notes
    for bad, why in (("20lfb10ap002", "G01"), ("vendor", "G05"), ("heat duty", "G05"), ('2"', "G03"), ("2 inch", "G03"),
                     ("16.5", "C01: the new PSV value must live only in Slack"),
                     ("wo-88213", "F11 must live only in Slack"),
                     ("moc-2021", "G02: no MOC exists for the PSV re-rating")):
        if bad in everything:
            problems.append("LEAK %r (%s)" % (bad, why))
    if "20lfc10aa191" in texts["operating_procedure"]:
        problems.append("operating procedure must not state 20LFC10AA191 data")
    if "20lfd10ct101" in everything:
        for slug, t in texts.items():
            if "20lfd10ct101" in t and slug not in ("handover_notes_dana",):
                problems.append("20LFD10CT101 appears outside handover notes: " + slug)

    # facts that must be present in a source
    need = {
        "design_basis": ["120 m3/h", "55 trays"],
        "commissioning_notes_2018": ["20lfb10cf002", "detune"],
        "incident_report_2019": ["dry running", "20lfc20aa102", "moc-2019-021"],
        "moc_2019_021": ["20lfc20cl101", "20lfc20aa011", "20lfc20cf101"],
        "moc_2020_014": ["cv 45", "cv 75"],
        "psv_201_datasheet": ["17.2"],
        "moc_2022_007": ["20lfb20aa001", "20lfb20ac001"],
        "moc_2023_009": ["tray 28", "tray 32", "81"],
        "near_miss_2024": ["20lfc20cl002", "manual", "20lfc20bb001"],
        "moc_2024_031": ["fail-closed", "20lfc20aa102"],
        "handover_notes_dana": ["30%", "20lfd10ct101", "55 c", "20lfc20ap002"],
        "operating_procedure": ["30%", "20lfc20ap002", "40%"],
        "incident_review_2019": ["dry running", "20lfc20aa102"],
        "maintenance_2021": ["wo-71120", "20lfc20ap002", "misalignment"],
        "maintenance_2022": ["20lfb20ac001", "18 months", "bypass"],
        "controls_2023": ["tray 32", "81"],
        "near_miss_review_2024": ["20lfc20cl002", "20lfc20aa102"],
        "e101_cleaning_2024": ["18 months", "2024-03"],
    }
    for slug, toks in need.items():
        for t in toks:
            if t not in texts[slug]:
                problems.append("%s missing %r" % (slug, t))

    # timeline consistency with the drawing history
    versions = json.load(open(os.path.join(HERE, "versions", "versions_api.json")))["data"]
    reg = texts["drawing_register"]
    for v in versions:
        d = v["createTime"][:10]
        if d not in reg:
            problems.append("drawing_register missing revision date %s (Rev %s)" % (d, v["revision"]))
        if v["moc"] and v["moc"].lower() not in reg:
            problems.append("drawing_register missing %s" % v["moc"])
    # every MOC form exists for every MOC in the drawing history
    mocs = {v["moc"] for v in versions if v["moc"]}
    have = {s.upper().replace("_", "-")[:12] for s in texts if s.startswith("moc_")}
    for m in mocs:
        slug = m.lower().replace("-", "_")
        if slug not in texts:
            problems.append("no MOC doc for %s" % m)

    # calendar: every notes slug exists, no all-day events with a start
    slugs = set(texts)
    for ev in EVENTS:
        if ev["notes"] and ev["notes"] not in slugs:
            problems.append("event %s points at unknown notes %s" % (ev["id"], ev["notes"]))

    # every Slack scene date that is also a calendar MOC review date lines up
    spec = json.load(open(os.path.join(HERE, "scenes.json")))["scenes"]
    cal_dates = {e["date"] for e in EVENTS}
    for s in spec:
        if s["channel"] == "moc-reviews" and s["date"] not in cal_dates:
            problems.append("Slack MOC review %s has no calendar event" % s["date"])

    # ICS parse check
    ics = open(os.path.join(CAL, "unit200_ops.ics"), newline="").read() if os.path.exists(os.path.join(CAL, "unit200_ops.ics")) else ""
    if ics.count("BEGIN:VEVENT") != len(EVENTS) or ics.count("END:VEVENT") != len(EVENTS):
        problems.append("ICS event count mismatch")
    for line in ics.split("\r\n"):
        if len(line.encode()) > 75:
            problems.append("ICS line too long: " + line[:40])
            break

    for p in problems:
        print("PROBLEM:", p)
    print("check passed" if not problems else "%d problem(s)" % len(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    if "--check" not in sys.argv:
        build()
    sys.exit(check())
