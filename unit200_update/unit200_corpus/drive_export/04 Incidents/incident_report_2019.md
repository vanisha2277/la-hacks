---
fileId: 1152faefd44d91630ce92c12d35dda222
name: Incident Report IR-2019-014 - 20LFC20AP001 seal failure
mimeType: application/vnd.google-apps.document
kind: doc
folder: Unit 200 / 04 Incidents
createdTime: 2019-11-08T17:00:00Z
modifiedTime: 2019-11-18T23:30:00Z
slug: incident_report_2019
owner: Hannah Cho <hcho@meridian-gas.example>
---

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
