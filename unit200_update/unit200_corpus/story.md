# Harbor Unit 200 — Story Bible (SYNTHETIC)

All people, documents, and events are fabricated for the hackathon. Say so in the demo.

Company: Meridian Gas Processing (fictional). Site: Harbor Terminal.
Unit 200: C3/C4 splitter. Mixed feed is separated into propane (overhead, C3) and butane (bottoms, C4).
Present day in the story: October 2026. Senior engineer Dana left June 2025.

## People

| Handle | Name | Role | Voice |
|---|---|---|---|
| dokafor | Dana Okafor | Senior Process Engineer, designed Unit 200, retired Jun 2025 | Terse, explains the why, uses rules of thumb and analogies ("think of 20LFC20BB001 as the pumps' savings account") |
| lferreira | Luis Ferreira | Operations Lead (shift supervisor) | Practical shorthand, occasional caps, cares about what operators can actually do |
| praman | Priya Raman | Instrument and Controls Tech | Precise, cites tag numbers and work orders |
| mdelaney | Mark Delaney | Maintenance Planner | Short, schedule-focused, mentions WO numbers |
| hcho | Hannah Cho | HSE / Process Safety Engineer | Formal, references MOC and standards |

## Equipment

PID-100 Feed and Preheat: 20LFB10BB001 feed surge drum, 20LFB10AP001 (running) and 20LFB10AP002 (standby), 20LFB10CF001/20LFB10CF002/20LFB10AA101 feed flow control, 20LFB10CL001, 20LFB20AC001 feed/bottoms exchanger.
PID-200 Column and Overhead: 20LFC10AT001 splitter (55 trays), 20LFC20AC001 overhead condenser, 20LFC20BB001 reflux drum, 20LFC20AP001 and 20LFC20AP002 reflux pumps, 20LFC30AC001 steam reboiler, 20LFC20AA101 reflux valve, 20LFC30CT001/20LFC30CT002/20LFC30AA101 temperature control, 20LFC10CP001/20LFC10CP002/20LFC10AA101 pressure control, 20LFC20CL001/20LFC20CL002/20LFC20AA102 reflux drum level, 20LFC10AA191 column relief.
Cross-diagram links: line 4"-C3C4-1005 (20LFB20AC001 to 20LFC10AT001) and line 4"-C4-1042 (20LFC10AT001 bottoms back through 20LFB20AC001). Off-page: battery limit feed, C3 product, C4 to storage (PID-300).

## Timeline

| Date | Rev | Event |
|---|---|---|
| 2017-09 | A | Design issued (Dana) |
| 2018-06 | 0 | As-built after commissioning, 20LFB10CP101 auto-start added |
| 2019-11-04 | n/a | Incident: 20LFC20AP001 seal failure |
| 2019-12 | 1 | MOC-2019-021 corrective actions |
| 2020-08 | 2 | MOC-2020-014 20LFC20AA101 trim upsized |
| 2021-06 | n/a | 20LFC20AP001 seal replaced again (WO-71120) |
| 2021-09 | n/a | 20LFC10AA191 re-rated (no MOC found, drawing never updated) |
| 2022-03 | 3 | MOC-2022-007 20LFB20AC001 bypass |
| 2023-05 | 4 | MOC-2023-009: 20LFC30CT001 relocated tray 28 to 32, 20LFC30CT002 setpoint 78 to 81 C |
| 2024-09 | n/a | Near-miss: 20LFC20BB001 overfill at startup |
| 2024-10 | 5 | MOC-2024-031 20LFC20AA102 fail position FO to FC |
| 2025-02 | n/a | Priya finds 20LFC20AA102 actuator still configured fail-open (WO-88213) |
| 2025-06 | n/a | Dana retires, writes partial handover notes |

## Planted facts (ground truth, see facts_ledger.json)

F01 Design basis: 120 m3/h feed, 55 trays, C3 overhead / C4 bottoms. Sources: design basis doc, Dana handover.
F02 Commissioning 2018: 20LFB10CF002 deliberately detuned because upstream feed composition swings caused oscillation in week one. Sources: Slack #unit200-eng, commissioning notes.
F03 Incident 2019-11-04: 20LFC20AP001 mechanical seal failed from dry running. 20LFC20AA102 failed open during an instrument air pressure dip and drained 20LFC20BB001. Sources: incident report, Slack #unit200-ops, incident review meeting.
F04 Corrective actions (MOC-2019-021, Rev 1): added 20LFC20CL101 low-low level trip on both reflux pumps, check valves 20LFC20AA011 and 20LFC20AA012, and low-flow alarm 20LFC20CF101. Sources: MOC form, Slack #moc-reviews, drawing Rev 1.
F05 2020 20LFC20AA101 trim upsized (Cv 45 to 75) for higher feed rates (MOC-2020-014, Rev 2). Side effect: valve hunts below about 40% load, operators run 20LFC20CF002 in manual below 40%. Sources: MOC form, Slack #unit200-ops (Luis).
F06 20LFC10AA191 was re-rated in 2021, set pressure lowered from 17.2 to 16.5 barg after inspection re-evaluated column MAWP. The datasheet in Drive still says 17.2. Sources: Slack #unit200-eng (Hannah), PSV datasheet (stale). CONTRADICTION C01.
F07 2022 20LFB20AC001 fouling: added bypass 20LFB20AA001 (MOC-2022-007, Rev 3) to hold feed temperature. Cleaning interval 18 months, last cleaned 2024-03. Sources: MOC form, Slack, maintenance meeting.
F08 2023 MOC-2023-009: 20LFC30CT001 moved from tray 28 to tray 32 (tray 28 reading was insensitive). 20LFC30CT002 setpoint changed from 78 to 81 C and loop retuned (Rev 4). Sources: Slack (Priya), meeting notes.
F09 2024-09 near-miss: 20LFC20BB001 overfilled during startup with 20LFC20CL002 left in manual. Sources: near-miss report, Slack, meeting notes.
F10 Response: 20LFC20AA102 fail position changed from fail-open to fail-closed (MOC-2024-031, Rev 5), accepting overfill risk covered by high-level alarm. Sources: MOC form, drawing Rev 5.
F11 2025-02 Priya found 20LFC20AA102 actuator still set up fail-open during PM, raised WO-88213, closure never recorded. CONTRADICTION C02 with F10. Source: Slack only.
F12 Cross-diagram: opening 20LFB20AC001 bypass makes bottoms run hotter to storage. Off-page storage high-temp alarm 20LFD10CT101 trips at 55 C, so operators only partially open 20LFB20AA001. Sources: Slack #unit200-ops, handover notes.
F13 Dana's rule: never start a reflux pump without 20LFC20BB001 level at least 30%. Sources: handover notes, operating procedure.
F14 20LFC20AP001 seal replaced again in 2021-06 (WO-71120), suspected misalignment not dry run, so 20LFC20AP002 is preferred duty pump. Sources: work order mention in Slack, maintenance meeting.

## Contradictions (must appear)

C01 20LFC10AA191 set pressure: 17.2 barg (datasheet, drawing) vs 16.5 barg (Hannah, Slack 2021).
C02 20LFC20AA102 fail position: FC (Rev 5 drawing, MOC-2024-031) vs still FO in the field (Priya, Slack 2025).

## Gaps (must be genuinely absent from the corpus)

G01 20LFB10AP002: no maintenance history, no incidents, only listed on the drawing.
G02 20LFC10AA191 re-rating: no MOC or approval document exists, only Hannah's Slack mention.
G03 Why the 20LFC20AA102 bypass line is 2": no explanation anywhere.
G04 20LFC30AC001 reboiler steam trap sizing basis: undocumented, one vague Slack remark ("not great but never failed").
G05 Pump vendor, heat duties, and design pressures beyond F01 appear nowhere (use for unanswerable eval questions).

## Corpus plan

| Source | Format | Count | Notes |
|---|---|---|---|
| Slack | Slack export JSON (users.json, channels.json, one file per day) | #unit200-ops about 120 msgs, #unit200-eng about 80, #moc-reviews about 40 | Threads, typos, emoji, abbreviations, links to Drive docs |
| Drive docs | Markdown with front matter (fileId, mimeType, owner, modifiedTime) | about 20 | 2 incident reports, 5 MOC forms, 1 stale PSV datasheet, operating procedure, startup checklist, partial handover notes, HAZOP excerpt, design basis |
| Meeting notes | Markdown docs linked from calendar events | about 8 | Messy, bullet fragments, action items |
| Calendar | .ics | about 15 events | Incident reviews, MOC reviews, HAZOP revalidation, PM shutdown, turnaround |
| Diagram versions | JSON graph per revision plus versions list | 7 revisions | Generated by pid_versions.py |

Realism rules:
1. About 30% of Slack is irrelevant chatter (shift swaps, lunch, other units, safety reminders) so retrieval is not trivial.
2. People refer to equipment inconsistently ("the reflux pump", "20LFC20AP001", "20LFC20AP001").
3. Facts are scattered: no single document holds a whole story. Each fact appears in 2 to 3 places with slightly different detail.
4. Documents contain mundane boilerplate (revision tables, approval blocks) with noise.
5. Never write the contradictions or gaps as explicit callouts in the corpus. They must be discoverable only by comparison.
