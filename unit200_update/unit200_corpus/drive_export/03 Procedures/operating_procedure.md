---
fileId: 1a639a503a6698cd00ee3c6619dea3b29
name: Unit 200 Operating Procedure
mimeType: application/vnd.google-apps.document
kind: doc
folder: Unit 200 / 03 Procedures
createdTime: 2018-07-02T16:00:00Z
modifiedTime: 2025-05-22T22:30:00Z
slug: operating_procedure
owner: Luis Ferreira <lferreira@meridian-gas.example>
---

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
