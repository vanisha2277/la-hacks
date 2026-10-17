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
- Column C-101: 55 trays
- Overhead: C3 condensed in E-102, collected in V-102, pumped back as reflux and product
- Bottoms: C4, heat-integrated against the feed in E-101, then to storage
- Reboiler E-103 is steam heated

## 3. Drawings
- PID-100 Feed and Preheat
- PID-200 Column and Overhead
Both issued Rev A with this document.

## 4. Control philosophy (summary)
| Loop | Controller | Final element |
|---|---|---|
| Feed flow | FIC-101 | FV-101 |
| Reflux flow | FIC-201 | FV-201 |
| Column temperature | TIC-203 | TV-203 (reboiler steam) |
| Column pressure | PIC-201 | PV-201 (condenser cooling water) |
| Reflux drum level | LIC-202 | LV-202 |

LV-202 is specified to fail open. On loss of instrument air the drum drains to the product line rather than backing up into the condenser.

## 5. Protection
Column overpressure is protected by PSV-201 (see datasheet). Further protection to be added at the as-built stage.

## 6. Not covered here
Equipment datasheets for pumps and exchangers are still being compiled and are not part of this document.
