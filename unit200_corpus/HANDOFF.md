# Handoff: what we have and what the agent should do

## The one-sentence version
A new engineer opens an old P&ID they've never seen. Our agent explains it like the senior engineer who used to run it: simple language, the history behind each piece of equipment, past mistakes, and honest about what nobody wrote down.

## The story (all fake, say so in the demo)
Fictional company Meridian Gas Processing. Unit 200 splits propane from butane. Senior engineer Dana Okafor designed it and retired in June 2025. Her knowledge is scattered across drawings, Slack, Drive docs, meeting notes and her calendar, and her handover notes are incomplete. The agent has to pull it all together.

## Test the data first (30 seconds)
From inside the unit200_corpus folder:

    python3 verify_data.py

You want `22 of 22 checks passed`. It checks every source is present and that each of the 12 test questions is answerable (or correctly NOT answerable) from the data. It uses only the standard library, so it runs on any Python.

## What data we have

| Source | Where | What's in it |
|---|---|---|
| Plant graph (the diagram as data) | `versions/plant_graph_current.json` | 36 pieces of equipment (nodes) and 45 pipes/signals (edges) across two sheets, PID-100 and PID-200. Nodes have id, type, label, sheet, attributes. Edges have from, to, kind, line number. Three edges cross between sheets (`crosses_to`). |
| Diagram history | `versions/rev_A.json` ... `rev_5.json`, `versions/changelog.json`, `versions/versions_api.json` | The graph as it was at each of 7 revisions (2017 to 2024) and exactly what changed each time. |
| Drawings | `dxf/*.dxf`, `png/` | Real CAD files for each revision. Optional: `extract_dxf.py` parses them back into a graph (needs Python 3.9+ and `pip install ezdxf`). To build the agent you can just use the graph JSON above. |
| Slack | `slack_export/all_messages.jsonl` (also Slack-style folders) | 204 messages, 3 channels, June 2018 to June 2025. Fields: user_name, text, ts, date, thread_ts. |
| Drive docs | `drive_export/` and `drive_index.json` | 16 docs (design basis, procedures, MOC forms, incident reports, datasheet, Dana's handover notes) plus 8 meeting notes. Index gives file id, folder, owner, created and modified time, path. |
| Calendar | `calendar_export/events.json` (also `.ics`) | 18 events. 8 link to meeting notes by file id. |

## DO NOT give the agent these (they contain the answers)
`facts_ledger.json`, `story.md` (renamed from story_bible.md), `scenes.json`, `write_slack_cache.py`, `drive_content.py`, `build_*.py`, `gen_slack.py`, `verify_data.py`. Only use the folders in the table above. `facts_ledger.json` is our answer key for the eval.

## What we're trying to show
1. **A simplified, explorable diagram.** Hover any valve, pump or instrument: plain-English explanation of what it does and why it matters.
2. **A senior-engineer chat.** You talk to "Dana". It answers in a plain mentor voice, with citations to the Slack message or document each claim came from.
3. **It knows what it doesn't know.** This is what separates us from a normal chatbot.

## How the agent should work

**Step 1: turn the mess into "knowledge atoms."** An LLM reads every Slack message, doc, note and event and writes small structured records:

    {id, claim, tags[], type, date, author, source{type,id,quote}, status}

`tags` are equipment tags (V-102, LV-202, ...). `type` is one of: decision, incident, change, gotcha, rule_of_thumb, maintenance, discrepancy. `status` is current, superseded or disputed. Keep the quote, so every answer can cite it. Two views come from the atoms: the **full atoms** (lossless, for the machine) and a **short beginner card per equipment tag** (for the UI).

**Step 2: find the gaps.** Simple rules over the atoms:
- an equipment tag with no atoms at all, or only a drawing mention
- two atoms about the same tag and attribute with different values from different sources (marks it **disputed**)
- something raised but never closed

**Step 3: chat.** Retrieve by equipment tag plus its neighbors in the graph (including across sheets via `crosses_to`). Answer rules:
- every claim cites a source
- if there's no record, say "there's no record of this" and suggest what to verify, don't guess
- if sources disagree, show both values and who said each
- keep "what's on record" separate from your own general engineering advice

**Step 4: the UI.** Draw the diagram from the graph JSON. Hover card = beginner summary plus warning badges (disputed, no record, crosses sheets). A revision slider using `rev_*.json` and `changelog.json` shows how the diagram changed over time.

## The traps (the agent must handle these, they're our demo)
- **PSV-201 set pressure.** Datasheet and drawing say 17.2 barg. Only a 2021 Slack message says it was lowered to 16.5, and no approval record exists. Correct behavior: show both, say which source says what, flag as disputed.
- **LV-202 fail position.** Drawing Rev 5 and MOC-2024-031 say fail-closed and "complete." A Slack thread in Feb 2025 says Priya found it still fail-open (WO-88213), and nobody confirmed the fix. Correct behavior: flag as disputed, true state unknown.
- **Cross-sheet gotcha.** Fully opening bypass valve BV-101 (PID-100) trips a high-temperature alarm TAH-301 (PID-300, off sheet) at 55 C. Only Dana's notes and Slack mention it. Correct behavior: connect the two sheets.
- **Real gaps (should answer "no record"):** P-101B (no history at all), who approved the PSV change, why the LV-202 bypass line is that size, E-103 heat duty.

## How we prove it works (modeling track)
`facts_ledger.json` has 12 seed questions: 8 that have an answer (2 of those are the contradictions, where the right answer shows both sides) and 4 that should get "no record". Add about 13 more. Run each question through three systems and compare:
1. plain LLM, no data
2. standard RAG over the raw files
3. our atoms plus graph-aware retrieval plus gap detection

Report: answer accuracy, citation accuracy, and **how often it makes something up on the questions that have no answer.** Put that table on a slide.

## Honest notes
- All data is synthetic. Say so on a slide. The real-world version plugs into Slack, Drive and Calendar through their APIs. Our data is shaped like their exports so the same code works.
- The drawings are real CAD files, but generated cleanly. Don't claim we read messy scans.
- Python 3.9 or newer for most LLM libraries. Check with `python3 --version`.
