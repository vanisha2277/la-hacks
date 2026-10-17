"""Hand-written Drive docs, meeting notes, and calendar events for the Unit 200 corpus.
Everything is fictional (Meridian Gas Processing, Harbor Terminal). See story.md.

DOCS / NOTES entries: (slug, title, folder, owner_handle, created 'YYYY-MM-DD', modified 'YYYY-MM-DD', body_markdown)
EVENTS entries: dict with id, date, start 'HH:MM' (Pacific) or None for all-day, minutes, summary, attendees, notes_slug, location, desc
"""

DOCS = []
NOTES = []

# ---------------------------------------------------------------------------------- DESIGN
DOCS.append(("design_basis", "Unit 200 C3/C4 Splitter - Design Basis", "01 Design", "dokafor", "2017-09-12", "2017-09-12", """
# Unit 200 C3/C4 Splitter - Design Basis
Meridian Gas Processing, Harbor Terminal. Author: D. Okafor. Issued 2017-09-12 with drawings Rev A.

## 1. Purpose
Unit 200 splits a mixed C3/C4 stream into propane (overhead) and butane (bottoms). Propane goes to product. Butane goes to storage, which is covered on a separate sheet set (PID-300).

## 2. Basis
- Design feed rate: 120 m3/h
- Column 20LFC10AT001: 55 trays
- Overhead: C3 condensed in 20LFC20AC001, collected in 20LFC20BB001, pumped back as reflux and product
- Bottoms: C4, heat-integrated against the feed in 20LFB20AC001, then to storage
- Reboiler 20LFC30AC001 is steam heated

## 3. Drawings
- PID-100 Feed and Preheat
- PID-200 Column and Overhead
Both issued Rev A with this document.

## 4. Control philosophy (summary)
| Loop | Controller | Final element |
|---|---|---|
| Feed flow | 20LFB10CF002 | 20LFB10AA101 |
| Reflux flow | 20LFC20CF002 | 20LFC20AA101 |
| Column temperature | 20LFC30CT002 | 20LFC30AA101 (reboiler steam) |
| Column pressure | 20LFC10CP002 | 20LFC10AA101 (condenser cooling water) |
| Reflux drum level | 20LFC20CL002 | 20LFC20AA102 |

20LFC20AA102 is specified to fail open. On loss of instrument air the drum drains to the product line rather than backing up into the condenser.

## 5. Protection
Column overpressure is protected by 20LFC10AA191 (see datasheet). Further protection to be added at the as-built stage.

## 6. Not covered here
Equipment datasheets for pumps and exchangers are still being compiled and are not part of this document.
"""))

DOCS.append(("drawing_register", "Unit 200 Drawing Register", "01 Design", "dokafor", "2017-09-12", "2024-10-14", """
# Unit 200 Drawing Register
Drawings are re-issued only when an MOC is closed.

| Sheet | Rev | Date | MOC | Description |
|---|---|---|---|---|
| PID-100, PID-200 | A | 2017-09-12 | - | Issued for design |
| PID-100 | 0 | 2018-06-20 | - | As-built after commissioning. 20LFB10CP101 auto-start added. |
| PID-200 | 1 | 2019-12-02 | MOC-2019-021 | 20LFC20CL101 reflux pump trip, 20LFC20AA011 and 20LFC20AA012, 20LFC20CF101 |
| PID-200 | 2 | 2020-08-18 | MOC-2020-014 | 20LFC20AA101 trim upsized |
| PID-100 | 3 | 2022-03-09 | MOC-2022-007 | 20LFB20AA001 bypass around 20LFB20AC001 |
| PID-200 | 4 | 2023-05-22 | MOC-2023-009 | 20LFC30CT001 relocated, 20LFC30CT002 setpoint |
| PID-200 | 5 | 2024-10-14 | MOC-2024-031 | 20LFC20AA102 fail position |

Current issue: PID-100 Rev 3, PID-200 Rev 5.
Latest Rev 5 file is in the CAD vault (drawings folder).
"""))

# ---------------------------------------------------------------------------------- COMMISSIONING
DOCS.append(("commissioning_notes_2018", "Unit 200 Commissioning Notes", "02 Commissioning", "dokafor", "2018-06-11", "2018-06-20", """
# Unit 200 Commissioning Notes (June 2018)
D. Okafor. Working log, not a formal report.

## 2018-06-11 (Mon)
Mechanical completion signed off. Loop checks done on feed section and column. Priya running through instruments.

## 2018-06-12
Feed in. 20LFB10CF002 oscillating badly. Root cause is upstream: feed composition swings and the loop chases it. Retuning does nothing useful because the disturbance keeps moving.
Decision: deliberately detune 20LFB10CF002 for now. Slow response is intentional. Luis told so operators do not read it as a fault. Revisit when upstream settles.

## 2018-06-13
Column holding. Reflux drum level OK. 20LFC20AA102 stroke test fine.

## 2018-06-15
First product off spec for about a shift, then good. No action.

## 2018-06-18
Column stable. Pressure control behaves.

## 2018-06-20
As-built markup done. Added 20LFB10CP101 (low discharge pressure switch) so the standby feed pump auto-starts. PID-100 reissued Rev 0.

## Open items
- Upstream composition swings still there. 20LFB10CF002 stays detuned until that is fixed.
"""))

# ---------------------------------------------------------------------------------- PROCEDURES
DOCS.append(("operating_procedure", "Unit 200 Operating Procedure", "03 Procedures", "lferreira", "2018-07-02", "2025-05-22", """
# Unit 200 Operating Procedure
Owner: L. Ferreira (Operations). Last revised 2025-05-22. Earlier revisions: 2018-07, 2019-12, 2020-09, 2022-04, 2024-11.

## 1. Startup (summary, see checklist for full list)
1. Confirm 20LFC20BB001 level before starting any reflux pump. Do not start either reflux pump unless 20LFC20BB001 level is at least 30%.
2. Put 20LFC20CL002 in AUTO before opening feed. (Added 2024-11.)
3. Confirm 20LFC20CL101 is healthy.
4. Bring feed up on 20LFB10CF002. Expect slow response, the loop is deliberately detuned.

## 2. Normal operation
- Reflux pumps: 20LFC20AP002 is the preferred duty pump. 20LFC20AP001 is standby. (Since 2021-06.)
- 20LFC20CF002: below about 40% load the reflux valve hunts. Run 20LFC20CF002 in manual below 40% and make small moves by hand. (Since 2020-09.)
- 20LFB20AC001 bypass 20LFB20AA001: keep closed in normal running. If feed temperature sags because 20LFB20AC001 is fouled, crack 20LFB20AA001 open and watch the bottoms temperature. Do not open it fully. (Since 2022-04.)

## 3. Loss of instrument air
- 20LFC20AA102 fails closed. 20LFC20BB001 level will rise. Watch the high level alarm.
- Reflux pumps are protected by the 20LFC20CL101 low-low level trip.
- 20LFC20CF101 will alarm if reflux flow drops.

## 4. Revision notes
- 2019-12: 20LFC20CL101, check valves and 20LFC20CF101 added (MOC-2019-021)
- 2020-09: manual operation note for 20LFC20CF002
- 2021-06: 20LFC20AP002 preferred duty
- 2022-04: 20LFB20AA001 guidance
- 2024-11: 20LFC20CL002 AUTO check at startup; 20LFC20AA102 fail-closed text (MOC-2024-031)
- 2025-05: 20LFC20BB001 minimum level rule made explicit
"""))

DOCS.append(("startup_checklist", "Unit 200 Startup Checklist", "03 Procedures", "lferreira", "2019-12-10", "2025-05-21", """
# Unit 200 Startup Checklist
Owner: L. Ferreira. Last updated 2025-05-21.

- [ ] Permit and lineup complete
- [ ] Instrument air available
- [ ] 20LFC20CL002 in AUTO (added 2024-09-30)
- [ ] 20LFC20BB001 level at least 30% before starting any reflux pump (added 2025-05-21)
- [ ] 20LFC20CL101 and 20LFC20CF101 healthy (added 2019-12)
- [ ] 20LFB20AA001 closed unless 20LFB20AC001 is fouled
- [ ] Preferred duty pump: 20LFC20AP002
- [ ] 20LFB10CF002 expected to respond slowly (deliberately detuned)
- [ ] Notify control room when feed is introduced

Sign-off: ______ Shift: ______ Date: ______
"""))

# ---------------------------------------------------------------------------------- INCIDENTS
DOCS.append(("incident_report_2019", "Incident Report IR-2019-014 - 20LFC20AP001 seal failure", "04 Incidents", "hcho", "2019-11-08", "2019-11-18", """
# Incident Report IR-2019-014
20LFC20AP001 mechanical seal failure and 20LFC20BB001 loss of level
Reported by: H. Cho (HSE). Technical input: D. Okafor, P. Raman. Event date: night of 2019-11-03 to 2019-11-04. Report issued 2019-11-18.

## Summary
During the night shift, instrument air pressure dipped. 20LFC20AA102 failed open and drained 20LFC20BB001. 20LFC20AP001 kept running with no suction and its mechanical seal failed. Found by day shift 2019-11-04.

## Timeline
- Night of 2019-11-03: instrument air header pressure dipped (confirmed on the header trend).
- 20LFC20AA102 went fully open as designed on loss of air.
- 20LFC20BB001 level fell to empty. 20LFC20AP001 continued to run.
- Early 2019-11-04: 20LFC20AP001 tripped. Smell noted by operators.
- 2019-11-04 morning: 20LFC20AP002 started, 20LFC20BB001 level restored manually. 20LFC20AP001 isolated.
- Seal inspected: failure mode is dry running.

## Root cause
Dry running of 20LFC20AP001 after 20LFC20BB001 emptied. Nothing stopped the pumps on low level.

## Contributing factors
- 20LFC20AA102 fails open, so an air dip empties the drum
- No low-low level protection on the reflux pumps

## Consequences
No release, no injury, no fire. Seal replaced.

## Corrective actions
1. Add low-low level trip (20LFC20CL101) on both reflux pumps
2. Add discharge check valves 20LFC20AA011 and 20LFC20AA012
3. Add reflux low-flow alarm 20LFC20CF101
All three under MOC-2019-021.
"""))

DOCS.append(("near_miss_2024", "Near-Miss Report NM-2024-009 - 20LFC20BB001 high level at startup", "04 Incidents", "hcho", "2024-09-23", "2024-09-30", """
# Near-Miss Report NM-2024-009
20LFC20BB001 near overfill during startup
Reported by: L. Ferreira (Operations). Reviewed by: H. Cho. Event date: 2024-09-19. Report dated 2024-09-23.

## What happened
During startup on the evening of 2024-09-19, 20LFC20BB001 level climbed toward the top of the drum. 20LFC20CL002 had been left in manual by the previous shift. The high level alarm fired. An operator watching the screen called it in and level was brought back by hand.

## Outcome
No release, no injury, no damage. 20LFC20CL002 returned to auto.

## Contributing factors
- 20LFC20CL002 left in manual
- Startup checklist had no item to confirm 20LFC20CL002 mode
- 20LFC20AA102 fails open, so with the controller out of the loop there is nothing that holds the drum down on its own

## Recommendations
1. Add 20LFC20CL002 AUTO check to the startup checklist (done 2024-09-30)
2. Review 20LFC20AA102 fail position (raised under MOC-2024-031)

## Sign-off
Operations: L. Ferreira 2024-09-23. HSE: H. Cho 2024-09-30.
"""))

# ---------------------------------------------------------------------------------- MOC
DOCS.append(("moc_2019_021", "MOC-2019-021 - Reflux pump protection after IR-2019-014", "05 MOC", "hcho", "2019-11-25", "2019-12-16", """
# Management of Change MOC-2019-021
Title: Reflux pump protection after IR-2019-014
Originator: D. Okafor, 2019-11-25. Unit: 200. Drawings affected: PID-200 (Rev 1).

## Description of change
1. Add low-low level trip 20LFC20CL101 on 20LFC20BB001 that stops both 20LFC20AP001 and 20LFC20AP002 (hardwired)
2. Add check valves 20LFC20AA011 and 20LFC20AA012 on the pump discharges
3. Add low-flow alarm 20LFC20CF101 on the reflux line

## Reason
IR-2019-014: 20LFC20BB001 emptied and 20LFC20AP001 ran dry. No existing protection stopped the pumps on low level.

## Hazard review
Trip is independent of the DCS. Check valves prevent reverse flow through a stopped pump. Proof test of 20LFC20CL101 added to the test schedule.

## Approvals
| Role | Name | Date |
|---|---|---|
| Originator | D. Okafor | 2019-11-25 |
| HSE | H. Cho | 2019-12-02 |
| Operations | L. Ferreira | 2019-12-02 |
| Instruments | P. Raman | 2019-12-02 |

## Closeout
PID-200 reissued as Rev 1 on 2019-12-02. Operator briefing done. Closed 2019-12-16.
"""))

DOCS.append(("moc_2020_014", "MOC-2020-014 - 20LFC20AA101 trim upsized", "05 MOC", "dokafor", "2020-07-20", "2020-08-24", """
# Management of Change MOC-2020-014
Title: 20LFC20AA101 trim upsized
Originator: D. Okafor, 2020-07-20. Unit: 200. Drawings affected: PID-200 (Rev 2).

## Description of change
Replace 20LFC20AA101 trim: Cv 45 to Cv 75.

## Reason
Unit is moving to higher feed rates. At the new rates the existing trim runs out of range.

## Hazard review
Noise and cavitation checked at the new rates, acceptable. No change to fail position.

## Approvals
| Role | Name | Date |
|---|---|---|
| Originator | D. Okafor | 2020-07-20 |
| HSE | H. Cho | 2020-07-28 |
| Instruments | P. Raman | 2020-07-28 |

## Closeout
Trim installed. PID-200 reissued as Rev 2 on 2020-08-18. 20LFC20AA101 datasheet and loop sheet updated by P. Raman. Closed 2020-08-24.
"""))

DOCS.append(("moc_2022_007", "MOC-2022-007 - 20LFB20AC001 bypass 20LFB20AA001", "05 MOC", "dokafor", "2022-02-24", "2022-03-18", """
# Management of Change MOC-2022-007
Title: 20LFB20AC001 bypass (20LFB20AA001)
Originator: D. Okafor, 2022-02-24. Unit: 200. Drawings affected: PID-100 (Rev 3).

## Description of change
Add manual bypass valve 20LFB20AA001 around feed/bottoms exchanger 20LFB20AC001 so feed temperature can be held while 20LFB20AC001 fouls between cleanings.

## Reason
20LFB20AC001 fouling is reducing feed temperature to the column. Cleaning needs an outage and is expensive. A bypass buys time between cleanings.

## Hazard review
With 20LFB20AA001 open the bottoms are not cooled by the feed in 20LFB20AC001 and bottoms temperature rises. Mitigation: operators open 20LFB20AA001 only partially and monitor bottoms temperature. Guidance added to the operating procedure.

## Approvals
| Role | Name | Date |
|---|---|---|
| Originator | D. Okafor | 2022-02-24 |
| HSE | H. Cho | 2022-03-01 |
| Operations | L. Ferreira | 2022-03-01 |

## Closeout
20LFB20AA001 installed. PID-100 reissued as Rev 3 on 2022-03-09. Closed 2022-03-18.
"""))

DOCS.append(("moc_2023_009", "MOC-2023-009 - 20LFC30CT001 relocation and 20LFC30CT002 setpoint", "05 MOC", "praman", "2023-04-12", "2023-05-26", """
# Management of Change MOC-2023-009
Title: 20LFC30CT001 relocation and 20LFC30CT002 setpoint
Originator: P. Raman, 2023-04-12. Unit: 200. Drawings affected: PID-200 (Rev 4).

## Description of change
1. Relocate column temperature transmitter 20LFC30CT001 from tray 28 to tray 32
2. Raise 20LFC30CT002 setpoint from 78 C to 81 C
3. Retune 20LFC30CT002 after the move

## Reason
The tray 28 reading is insensitive: temperature barely changes there, so the loop sees disturbances late. Tray 32 is where the temperature actually moves.

## Hazard review
D. Okafor confirmed the 81 C setpoint stays within product specification. No new hazards identified.

## Approvals
| Role | Name | Date |
|---|---|---|
| Originator | P. Raman | 2023-04-12 |
| Process | D. Okafor | 2023-04-20 |
| HSE | H. Cho | 2023-04-20 |

## Closeout
20LFC30CT001 moved and loop retuned the week of 2023-05-08. PID-200 reissued as Rev 4 on 2023-05-22. Closed 2023-05-26.
"""))

DOCS.append(("moc_2024_031", "MOC-2024-031 - 20LFC20AA102 fail position", "05 MOC", "hcho", "2024-09-30", "2024-10-28", """
# Management of Change MOC-2024-031
Title: 20LFC20AA102 fail position, fail-open to fail-closed
Originator: D. Okafor, 2024-09-30. Unit: 200. Drawings affected: PID-200 (Rev 5).

## Description of change
Change 20LFC20AA102 fail position from fail-open to fail-closed.

## Reason
NM-2024-009 (20LFC20BB001 near overfill at startup). With 20LFC20AA102 failing open, a lost or out-of-service level controller leaves nothing holding the drum down.

## Hazard review
Fail-closed means 20LFC20BB001 can overfill on loss of instrument air. This risk is accepted. It is covered by the 20LFC20BB001 high-level alarm. Operators can see 20LFC20AA102 position on the console.

## Actions
| Action | Owner | Status |
|---|---|---|
| Update PID-200 | D. Okafor | Complete 2024-10-14 |
| Reconfigure 20LFC20AA102 actuator for fail-closed | P. Raman | Complete 2024-10-21 |
| Update operating procedure text | L. Ferreira | Complete 2024-11-05 |

## Approvals
| Role | Name | Date |
|---|---|---|
| Originator | D. Okafor | 2024-09-30 |
| HSE | H. Cho | 2024-10-08 |
| Operations | L. Ferreira | 2024-10-08 |

## Closeout
PID-200 reissued as Rev 5 on 2024-10-14. Closed 2024-10-28.
"""))

# ---------------------------------------------------------------------------------- DATASHEET
DOCS.append(("psv_201_datasheet", "20LFC10AA191 Datasheet", "06 Datasheets", "praman", "2018-05-30", "2018-06-20", """
# Relief Valve Datasheet: 20LFC10AA191
Datasheet revision: 0 (as-built). Updated 2018-06-20. Owner: P. Raman.

| Field | Value |
|---|---|
| Tag | 20LFC10AA191 |
| Service | Column 20LFC10AT001 overpressure |
| Location | Column overhead, PID-200 |
| Set pressure | 17.2 barg |
| Manufacturer / model | not recorded on this sheet |
| Orifice | not recorded on this sheet |

Notes: Set pressure verified at installation, June 2018.
"""))

# ---------------------------------------------------------------------------------- REVIEWS
DOCS.append(("hazop_excerpt_2023", "HAZOP Revalidation 2023 - Unit 200 (excerpt)", "08 Reviews", "hcho", "2023-09-14", "2023-10-20", """
# HAZOP Revalidation 2023 - Unit 200 (excerpt)
Facilitator: H. Cho. Sessions from 2023-09-14. Report dated 2023-10-20. Team: D. Okafor, L. Ferreira, P. Raman, M. Delaney.

## Node 3: Reflux drum 20LFC20BB001 and reflux pumps
| Deviation | Causes | Safeguards | Action |
|---|---|---|---|
| Low level | 20LFC20AA102 fails open on loss of air. 20LFC20CL002 failure. | 20LFC20CL101 trips both reflux pumps. 20LFC20CF101. | None |
| High level | 20LFC20CL002 in manual or failed. | 20LFC20BB001 high level alarm. | None |
| No flow | Pump trip. | 20LFC20CF101. Standby pump. | None |

## Node 4: Column 20LFC10AT001 pressure
| Deviation | Causes | Safeguards | Action |
|---|---|---|---|
| High pressure | 20LFC10CP002 failure. Loss of cooling water. | 20LFC10CP002. 20LFC10AA191 (see datasheet). | None |

## Other
All nodes reviewed against drawings PID-100 Rev 3 and PID-200 Rev 4. No new actions raised.
"""))

# ---------------------------------------------------------------------------------- MAINTENANCE
DOCS.append(("e101_cleaning_2024", "20LFB20AC001 Cleaning Record March 2024", "09 Maintenance", "mdelaney", "2024-03-11", "2024-03-11", """
# 20LFB20AC001 Cleaning Record - March 2024
M. Delaney. Written 2024-03-11.

- Outage: week of 2024-03-04
- 20LFB20AC001 bundle pulled and cleaned. Fouling heavier than expected.
- Cleaning interval for 20LFB20AC001: about 18 months
- Previous cleaning was before 20LFB20AA001 was installed. That is why 20LFB20AA001 had been open so often this past year.
- 20LFB20AA001 closed again 2024-03-08 after restart. Feed temperature back to normal.
- Next cleaning due about 18 months out (September 2025). Put on the PM calendar.
"""))

# ---------------------------------------------------------------------------------- HANDOVER
DOCS.append(("handover_notes_dana", "Unit 200 Handover Notes (Dana) - INCOMPLETE", "07 Handover", "dokafor", "2025-05-20", "2025-06-12", """
# Unit 200 Handover Notes
Dana Okafor, written May-June 2025 before I retire on 2025-06-13. These are the things I carry in my head. NOT COMPLETE, see the end.

## What the unit is
C3/C4 splitter. 120 m3/h design feed, 55 trays in 20LFC10AT001. Propane overhead, butane bottoms to storage (PID-300).

## Rules I follow
1. Never start either reflux pump unless 20LFC20BB001 level is at least 30%. Dry running killed 20LFC20AP001 in 2019.
2. 20LFC20AP002 is the duty pump. 20LFC20AP001 had a seal problem again in 2021 and I think it was alignment. Keep A as the spare.
3. Below about 40% load 20LFC20AA101 hunts. Run 20LFC20CF002 in manual there. It is the price of the bigger trim from 2020.
4. 20LFB10CF002 is detuned on purpose since commissioning. Do not tune it up to make it look nicer.
5. Never open 20LFB20AA001 fully. Opening the 20LFB20AC001 bypass makes the bottoms run hotter on the way to storage, and 20LFD10CT101 on PID-300 trips at 55 C. Crack it, and watch the storage temperature, not just the feed temperature. This is the one that bites people because the valve is on one sheet and the alarm is on another.
6. 20LFC30CT001 was on tray 28 until 2023. It was useless there. It is on tray 32 now and 20LFC30CT002 runs at 81 C.
7. 20LFC20AA102 fails closed since the 2024 change. Before that it failed open and that is what emptied 20LFC20BB001 in 2019.

## History in one paragraph
Design 2017, commissioning June 2018, seal failure and low level trip 2019, bigger 20LFC20AA101 trim 2020, 20LFB20AC001 bypass 2022, 20LFC30CT001 move 2023, 20LFC20AA102 fail position 2024.

## Things I did not get to
- Relief devices
- Reboiler 20LFC30AC001
- Instrument details (ask Priya)
- Where the old calculations live
"""))

# ======================================================================================= MEETING NOTES
NOTES.append(("incident_review_2019", "Meeting notes - Incident review IR-2019-014", "10 Meeting Notes", "hcho", "2019-11-12", "2019-11-12", """
# Incident review, 2019-11-12, 10:00
Attendees: Dana, Hannah, Luis, Mark, Priya

- seal failure on 20LFC20AP001, confirmed dry running (Mark showed the seal face)
- how did 20LFC20BB001 empty: air dipped, 20LFC20AA102 went wide open (fail open by design) -> drum drained -> pump ran dry
- nothing stopped the pump on low level. thats the gap
- Dana: 20LFC20AA102 fail-open is intentional, drain to product on loss of air. not changing it for this. revisit later maybe
- proposed fixes: low-low level trip on both reflux pumps, check valves on discharge, low flow alarm
- Hannah: needs MOC. review set for 12/2

Actions
- Dana: draft MOC (LSLL on both pumps, check valves, 20LFC20CF101)
- Hannah: schedule MOC review
- Priya: pull air header trend for the report
- Mark: keep the old seal
- Luis: brief crews on what happened
"""))

NOTES.append(("maintenance_2021", "Meeting notes - Monthly maintenance planning June 2021", "10 Meeting Notes", "mdelaney", "2021-06-24", "2021-06-24", """
# Monthly maintenance planning, 2021-06-24
Attendees: Mark, Luis, Dana, Priya

- 20LFC20AP001 seal replaced again, WO-71120, done 6/22
- no dry running marks this time. shaft alignment was off. Mark thinks misalignment is the cause
- Dana: agrees. make 20LFC20AP002 the preferred duty pump, 20LFC20AP001 standby until alignment is sorted
- Luis updating operator notes
- fire water test due next month
- 20LFC20AC001 cooling water strainer, clean at next window
- tank farm inspection pushed to Aug
- forklift near-miss refresher for night crew

Actions
- Mark: realign 20LFC20AP001 when it is back from shop
- Luis: operator notes, 20LFC20AP002 duty
- Mark: strainer
"""))

NOTES.append(("maintenance_2022", "Meeting notes - Maintenance planning February 2022", "10 Meeting Notes", "mdelaney", "2022-02-22", "2022-02-22", """
# Maintenance planning, 2022-02-22
Attendees: Mark, Luis, Dana

- 20LFB20AC001 fouling getting worse, feed temp to column sagging. Luis says crews chasing it daily
- options: A) clean now. needs outage, expensive. B) add a bypass around 20LFB20AC001 and hold feed temp between cleanings
- cleaning interval roughly 18 months
- Dana leaning to B. will write the MOC
- Mark: B buys time, still need to clean eventually
- Luis ok if it is written in the procedure

Other
- PM list for Q2 reviewed
- lube oil analysis results ok

Actions
- Dana: MOC for bypass
- Luis: procedure wording
- Mark: pencil in next 20LFB20AC001 cleaning once bypass in
"""))

NOTES.append(("controls_2023", "Meeting notes - Controls sync April 2023", "10 Meeting Notes", "praman", "2023-04-27", "2023-04-27", """
# Controls sync, 2023-04-27
Attendees: Priya, Dana, Luis

- 20LFC30CT001 move: tray 28 -> tray 32. approved 4/20 (MOC-2023-009)
- why: tray 28 barely moves, loop sees disturbances late. tray 32 much more sensitive
- 20LFC30CT002 setpoint 78 -> 81 C. Dana says in spec
- retune planned week of 5/8 after transmitter is moved
- Luis: tell crews old setpoint was 78 so old notes dont confuse
- 20LFC10CP001 calibration due, Priya will do with next round

Actions
- Priya: move 20LFC30CT001, retune 20LFC30CT002, update trend screens
- Priya: drawing Rev 4
- Luis: pass setpoint change to crews
"""))

NOTES.append(("hazop_kickoff_2023", "Meeting notes - HAZOP revalidation kickoff", "10 Meeting Notes", "hcho", "2023-09-14", "2023-09-14", """
# HAZOP revalidation kickoff, 2023-09-14
Attendees: Hannah (facilitator), Dana, Luis, Priya, Mark

- scope: Unit 200, drawings PID-100 Rev 3 and PID-200 Rev 4
- nodes: feed and preheat, column, reflux drum and pumps, column pressure, bottoms
- sessions: 4 half days, report end of October
- bring: latest MOCs since last HAZOP, incident reports
- Luis wants operators in the room for the reflux drum node

Actions
- Hannah: circulate node list
- Priya, Mark: pull open work orders list
"""))

NOTES.append(("near_miss_review_2024", "Meeting notes - Near-miss review NM-2024-009", "10 Meeting Notes", "hcho", "2024-09-26", "2024-09-26", """
# Near-miss review, 2024-09-26, 10:00
Attendees: Hannah, Dana, Luis, Mark, Priya

- 20LFC20BB001 almost overfilled at startup on 9/19
- 20LFC20CL002 left in manual from previous shift. startup checklist has no check for this
- high level alarm worked, Mark saw level climbing and called it in
- no release, no injury
- discussion on 20LFC20AA102. fails open now. with the controller out of the loop nothing holds the drum
- option A: keep fail-open and add more alarms. option B: change to fail-closed, accept overfill on loss of air, covered by high level alarm
- Dana prefers B. Hannah wants it under MOC. agreed

Actions
- Luis: add 20LFC20CL002 AUTO check to startup checklist (by 9/30)
- Dana: draft MOC for 20LFC20AA102 fail closed
- Priya: check actuator and what is needed
- Hannah: set up MOC review for early Oct
"""))

NOTES.append(("pm_planning_2025", "Meeting notes - PM planning January 2025", "10 Meeting Notes", "mdelaney", "2025-01-23", "2025-01-23", """
# PM planning, 2025-01-23
Attendees: Mark, Luis, Priya, Dana

- 2025 PM calendar reviewed
- 20LFB20AC001 next cleaning: 18 months after last (March 2024) so September 2025
- Priya: instrument PM rounds on Unit 200 planned for February
- Dana: retiring in June, handover notes to start in spring
- fire water test done, no issues
- stores: spare seal kits in stock

Actions
- Mark: book 20LFB20AC001 cleaning window for September
- Priya: PM rounds Feb
- Dana: start handover notes
"""))

NOTES.append(("handover_session_2025", "Meeting notes - Dana handover session", "10 Meeting Notes", "praman", "2025-05-29", "2025-05-29", """
# Handover session with Dana, 2025-05-29, 13:00
Attendees: Dana, Priya, Luis (Mark joined late)

Covered
- operating rules of thumb (20LFC20BB001 30% before starting reflux pumps, 20LFC20AP002 duty, manual below 40% on 20LFC20CF002)
- 20LFB20AA001 and the storage temperature catch
- history of the big changes

Did not get to (ran out of time)
- relief devices
- reboiler 20LFC30AC001
- instrument details
- where old calcs are stored

Actions
- Dana: finish written handover notes by 6/12
- Priya, Luis: ask Dana about the rest before she leaves
"""))

# ======================================================================================= CALENDAR
EVENTS = [
 dict(id="E01", date="2018-06-11", start="09:00", minutes=60, summary="Unit 200 commissioning kickoff", attendees=["dokafor", "lferreira", "praman"], notes=None, location="Control room", desc="Start of commissioning week. Loop checks and feed introduction."),
 dict(id="E02", date="2018-06-20", start="14:00", minutes=60, summary="As-built drawing review (PID-100 Rev 0)", attendees=["dokafor", "praman"], notes=None, location="Engineering office", desc="Review as-built markup. 20LFB10CP101 added."),
 dict(id="E03", date="2019-11-12", start="10:00", minutes=90, summary="Incident review IR-2019-014 (20LFC20AP001 seal / 20LFC20BB001 level)", attendees=["hcho", "dokafor", "lferreira", "mdelaney", "praman"], notes="incident_review_2019", location="Conference room B", desc="Review of the 2019-11-04 event. Report: IR-2019-014."),
 dict(id="E04", date="2019-12-02", start="10:15", minutes=60, summary="MOC review MOC-2019-021 (reflux pump protection)", attendees=["hcho", "dokafor", "lferreira", "praman"], notes=None, location="#moc-reviews", desc="Approve 20LFC20CL101, 20LFC20AA011 and 20LFC20AA012 and 20LFC20CF101. Drawing to Rev 1."),
 dict(id="E05", date="2020-07-28", start="11:00", minutes=45, summary="MOC review MOC-2020-014 (20LFC20AA101 trim)", attendees=["dokafor", "hcho", "praman"], notes=None, location="#moc-reviews", desc="20LFC20AA101 trim upsize for higher feed rates. Drawing to Rev 2."),
 dict(id="E06", date="2021-06-24", start="13:00", minutes=60, summary="Monthly maintenance planning", attendees=["mdelaney", "lferreira", "dokafor", "praman"], notes="maintenance_2021", location="Maintenance office", desc="Monthly maintenance planning. Includes 20LFC20AP001 seal WO-71120."),
 dict(id="E07", date="2022-02-22", start="13:00", minutes=60, summary="Maintenance planning: 20LFB20AC001 fouling", attendees=["mdelaney", "lferreira", "dokafor"], notes="maintenance_2022", location="Maintenance office", desc="20LFB20AC001 fouling options: clean now or bypass."),
 dict(id="E08", date="2022-03-01", start="09:45", minutes=45, summary="MOC review MOC-2022-007 (20LFB20AC001 bypass)", attendees=["dokafor", "hcho", "lferreira"], notes=None, location="#moc-reviews", desc="20LFB20AA001 bypass. Drawing to Rev 3."),
 dict(id="E09", date="2023-04-20", start="10:00", minutes=45, summary="MOC review MOC-2023-009 (20LFC30CT001 relocation)", attendees=["praman", "dokafor", "hcho"], notes=None, location="#moc-reviews", desc="20LFC30CT001 tray 28 to 32, 20LFC30CT002 setpoint. Drawing to Rev 4."),
 dict(id="E10", date="2023-04-27", start="15:00", minutes=45, summary="Controls sync", attendees=["praman", "dokafor", "lferreira"], notes="controls_2023", location="Engineering office", desc="Follow-up on 20LFC30CT001 move and retune plan."),
 dict(id="E11", date="2023-09-14", start="09:00", minutes=180, summary="HAZOP revalidation kickoff - Unit 200", attendees=["hcho", "dokafor", "lferreira", "praman", "mdelaney"], notes="hazop_kickoff_2023", location="Conference room A", desc="Kickoff for HAZOP revalidation. Report due end of October."),
 dict(id="E12", date="2024-03-04", start=None, minutes=5, summary="20LFB20AC001 cleaning outage", attendees=["mdelaney", "lferreira"], notes=None, location="Unit 200", desc="20LFB20AC001 bundle pulled and cleaned. Week of 2024-03-04."),
 dict(id="E13", date="2024-09-26", start="10:00", minutes=90, summary="Near-miss review NM-2024-009 (20LFC20BB001 high level)", attendees=["hcho", "dokafor", "lferreira", "mdelaney", "praman"], notes="near_miss_review_2024", location="Conference room B", desc="Review of 2024-09-19 startup near-miss."),
 dict(id="E14", date="2024-10-08", start="09:15", minutes=45, summary="MOC review MOC-2024-031 (20LFC20AA102 fail position)", attendees=["hcho", "dokafor", "lferreira"], notes=None, location="#moc-reviews", desc="20LFC20AA102 fail-open to fail-closed. Drawing to Rev 5."),
 dict(id="E15", date="2025-01-23", start="14:00", minutes=60, summary="PM planning 2025", attendees=["mdelaney", "lferreira", "praman", "dokafor"], notes="pm_planning_2025", location="Maintenance office", desc="2025 PM calendar, 20LFB20AC001 next cleaning."),
 dict(id="E16", date="2025-02-11", start="08:00", minutes=360, summary="PM rounds: Unit 200 instruments", attendees=["praman"], notes=None, location="Unit 200", desc="Instrument preventive maintenance round."),
 dict(id="E17", date="2025-05-29", start="13:00", minutes=120, summary="Handover session with Dana", attendees=["dokafor", "praman", "lferreira", "mdelaney"], notes="handover_session_2025", location="Conference room A", desc="Dana walks through what she carries in her head. Notes in Drive."),
 dict(id="E18", date="2025-06-13", start="15:00", minutes=60, summary="Dana send-off", attendees=["dokafor", "lferreira", "mdelaney", "praman", "hcho"], notes=None, location="Break room", desc="Dana's last day."),
]
