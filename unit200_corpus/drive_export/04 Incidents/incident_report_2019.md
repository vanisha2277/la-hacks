---
fileId: 1152faefd44d91630ce92c12d35dda222
name: Incident Report IR-2019-014 - P-102A seal failure
mimeType: application/vnd.google-apps.document
kind: doc
folder: Unit 200 / 04 Incidents
createdTime: 2019-11-08T17:00:00Z
modifiedTime: 2019-11-18T23:30:00Z
slug: incident_report_2019
owner: Hannah Cho <hcho@meridian-gas.example>
---

# Incident Report IR-2019-014
P-102A mechanical seal failure and V-102 loss of level
Reported by: H. Cho (HSE). Technical input: D. Okafor, P. Raman. Event date: night of 2019-11-03 to 2019-11-04. Report issued 2019-11-18.

## Summary
During the night shift, instrument air pressure dipped. LV-202 failed open and drained V-102. P-102A kept running with no suction and its mechanical seal failed. Found by day shift 2019-11-04.

## Timeline
- Night of 2019-11-03: instrument air header pressure dipped (confirmed on the header trend).
- LV-202 went fully open as designed on loss of air.
- V-102 level fell to empty. P-102A continued to run.
- Early 2019-11-04: P-102A tripped. Smell noted by operators.
- 2019-11-04 morning: P-102B started, V-102 level restored manually. P-102A isolated.
- Seal inspected: failure mode is dry running.

## Root cause
Dry running of P-102A after V-102 emptied. Nothing stopped the pumps on low level.

## Contributing factors
- LV-202 fails open, so an air dip empties the drum
- No low-low level protection on the reflux pumps

## Consequences
No release, no injury, no fire. Seal replaced.

## Corrective actions
1. Add low-low level trip (LSLL-202) on both reflux pumps
2. Add discharge check valves CV-102A and CV-102B
3. Add reflux low-flow alarm FAL-201
All three under MOC-2019-021.
