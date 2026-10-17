---
fileId: 17e5b6346e8c663ab13df946342d3506d
name: Unit 200 C3/C4 Splitter - Design Basis
mimeType: application/vnd.google-apps.document
kind: doc
folder: Unit 200 / 01 Design
createdTime: 2017-09-12T16:00:00Z
modifiedTime: 2017-09-12T22:30:00Z
slug: design_basis
owner: Dana Okafor <dokafor@meridian-gas.example>
---

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
