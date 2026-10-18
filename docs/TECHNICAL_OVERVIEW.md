# Handoff: technical overview

How the system is built, for judges' technical questions and for anyone extending it. The product story is in [OVERVIEW.md](OVERVIEW.md); deploy steps are in [app/DEPLOY.md](../app/DEPLOY.md).

Numbers below are from the current `app/out/kb.json`.

---

## 1. System at a glance

```
                        BUILD TIME (offline, scripts/build_kb.py)
 unit200_corpus/ ──▶ ingest/* ──▶ linker (rules → LLM) ──▶ gaps.run() ──▶ out/kb.json
                                                                              │
                        QUESTION TIME (live, agents/conversation.py: ask())   │
 question ──▶ run_tools loop (asi1 + function calling) ──▶ Tools(kb) ◀────────┘
                │   every call appended to the trace, streamed via on_step
                ▼
          JSON answer ──▶ check_citations() ──▶ (rewrite once if bad) ──▶ result
                                                                          │
          ┌───────────────────────────────────────────────────────────────┤
          ▼                                                               ▼
 FastAPI (Railway): /ask + SSE events ──▶ Next.js (Vercel)     uAgent (Agentverse) ──▶ ASI:One chat
```

One knowledge base, one `ask()` function, two front doors. Neither front door has its own logic.

---

## 2. Knowledge base (`core/kb.py`, `out/kb.json`)

A single JSON-serializable dict, ~300 KB, loaded once into memory. No database.

| Collection | Shape | Count |
|---|---|---|
| `sheets` | id → {id, title, rev, rev_date, svg, page_size} | 2 |
| `components` | tag → {tag, kind, desc, sheet, attrs, decoded, bbox} | 33 |
| `links` | [{from, to, relation, status, source}]; relation ∈ flows_to / signal / measures / utility / protects | 42 (all `seen`) |
| `offpage` | [{from, from_sheet, to, to_sheet, label}] | 6 |
| `sources` | id → {id, kind, text, author, date, title, link}; **original text, never rewritten** | 307 (204 Slack, 85 Drive, 18 calendar) |
| `mentions` | [{source_id, tag, type, by, evidence}] | 360 |
| `contexts` | id → conversation / doc / event grouping of sources, with every tag linked inside it | 67 |
| `records` | tag → tag register row + valve list values | 34 |
| `revisions` | [{id, sheet, rev, date, author, description, tags}] | 8 |
| `gaps` | [{id, type, severity, tags, issue, sources}] | 9 |
| `notes`, `corrections` | senior writes (merged in from `data/user_state.json` at load) | 0 |
| `cv` | sheet → computer-vision detections (overlay only) | 1 sheet |

Mention types: issue 118, mention 105, change 65, decision 53, question 19.
Mention origins (`by`): regex 240, llm-context 97, llm 18, alias 5.

**Senior writes** (`add_note`, `record_correction`, `flag_issue`) go to a separate `data/user_state.json`, so rebuilding `kb.json` never erases them. `load()` merges them in: notes append, flags become `flagged_by_senior` gaps.

### Citation ID scheme

Every source has a stable ID, and these IDs are the only thing an answer may cite.

| Prefix | Example | Points to |
|---|---|---|
| `drawing:` | `drawing:PID-200` | a P&ID sheet (current revision) |
| `rev:` | `rev:PID-100-A` | a drawing revision |
| `slack-<channel>-<ts>` | `slack-unit200-eng-1631745900.000183` | one Slack message |
| `drive-<doc>-<nn>` | `drive-psv_201_datasheet-01` | one section of a Drive doc |
| `cal-` | `cal-E18` | a calendar event (+ its meeting notes) |
| `register:` / `valvelist:` | `valvelist:20LFC10AA191` | a register row |
| `gap-` | `gap-001` | a detected gap |
| `note-` / `corr-` / `flag-` | `note-001` | senior writes |
| `general` / `inference` | | labels, not sources: general engineering knowledge / AI reasoning |

---

## 3. Build pipeline (`scripts/build_kb.py`)

```
drawings.ingest → revisions.ingest → cv.ingest → registers → slack → drive → calendar
→ linker.link_rules → linker.link_llm → linker.tag_contexts → gaps.run → save
```

Flags: `--no-llm` (rules-only linking), `--docs` (also generate beginner docs).
The linker caches every LLM call by content hash in `out/cache/link/` (committed), so a rebuild after code changes makes **zero LLM calls** unless the corpus text changed.

**Eval isolation:** the corpus contains ground truth (`facts_ledger.json`, `scenes.json`, `story.md`). The build only reads named files and never ingests these; only `scripts/eval.py` reads the ledger.

### Ingest adapters (`ingest/`)

All format-specific parsing lives here. Everything downstream only knows the KB schema, so a new drawing format or chat tool means one new adapter.

| Adapter | Input | Output |
|---|---|---|
| `drawings.py` | DXF (vector CAD) via the corpus's `extract_dxf.py` | sheets, components with exact bboxes (DXF coords → page coords), links, off-page connectors |
| `revisions.py` | each sheet's DXF revision table + **a DXF diff against the previous revision** + file version history | what actually changed per revision, who issued it |
| `cv.py` | CV pipeline output (`base.json` + `source.pdf`) | detections for the overlay **only when the PDF matches the current drawing**; never treated as plant facts |
| `registers.py` | tag register + valve list | `records[tag]`; the valve list holds official as-designed values |
| `slack.py` | standard Slack export (`users.json`, `channels.json`, `<channel>/<day>.json`) | one source per message, grouped into conversations (threads, or same channel within 30 min) |
| `drive.py` | markdown with front matter | one passage per `## ` section |
| `calendar.py` | `events.json` / `.ics` | one source per event, linked to its meeting notes |

**Why DXF and not computer vision:** vector CAD gives exact tags, positions, and connections. Line tracing from scanned images is the hardest unsolved part of P&ID digitization, so we deliberately don't depend on it. CV runs as a separate overlay layer for comparison.

---

## 4. Linker (`agents/linker.py`)

Attaches each source to the equipment it's about. It never rewrites content.

1. **Rules, no AI** (`link_rules`): explicit KKS tags (regex), legacy ISA tags mapped through the register (`PSV-201` → `20LFC10AA191`), and description aliases that are unambiguous across the plant ("reflux drum").
2. **LLM per context** (`link_llm`, 4 parallel workers): one call per Slack conversation / Drive doc / calendar event, to catch implicit references ("dont fight it", "the spare"). The model must return the **verbatim evidence** phrase and an **anchor**: either this item names the component, or an earlier item in the same conversation does.
3. **Code check:** a link is kept only if the tag exists, the evidence appears word-for-word in the source (`verbatim()`), and the anchor checks out. Everything else is rejected and counted.
4. **Context tagging** (`tag_contexts`): each conversation is tagged with every component linked anywhere in it, so retrieval finds a whole thread even when only one message names the tag.

Each mention also gets a type (change / decision / issue / question / mention), used by `get_history` and the gap checks.

---

## 5. Deterministic checks (`core/gaps.py`, `core/tags.py`)

Plain code, no AI. Runs at build time; results are first-class KB entries.

| Check | Severity | Logic |
|---|---|---|
| `incomplete_loop` | high | a control loop (grouped by `tags.group_loops`) has a controller but no final element, or the reverse |
| `value_conflict` | high | a newer source states a different value for a drawing attribute than the drawing (e.g. set pressure 17.2 vs 16.5 barg). Uses `stated_value()` (parses "from A to B" as B) and `effective_since()` (the revision that last changed the attribute) so only sources **newer** than the drawing's value count |
| `change_not_reflected` | high | a source typed `change` uses removal/replacement language about a component the drawing still shows |
| `unprotected_vessel` | medium | a vessel/drum with no `protects` link from a relief device |
| `index_not_on_drawing` / `drawing_not_in_index` / `index_sheet_mismatch` | medium | register vs drawing disagreements |
| `dangling_offpage` | medium | off-page connector to a sheet not in the KB |
| `unverified_link` | low | link with status `inferred` |
| `undocumented` | low | equipment no source mentions |

Current result: 9 gaps: 2 value conflicts, 2 unprotected vessels, 1 register-only tag, 1 dangling off-page connector, 3 undocumented.

`tags.py` decodes KKS tags (plant area, system, equipment type, number), finds tags in free text, and groups loops (sensor → controller → final element).

---

## 6. Tools (`core/tools.py`)

The **only** way the conversation agent can read the KB. Each tool returns the same envelope:

```json
{"data": {...}, "citations": ["drawing:PID-200", "slack-unit200-eng-1631745900.000183"], "empty": false}
```

`empty: true` means nothing is recorded, and the prompt requires the agent to say "not recorded".

| Tool | Purpose |
|---|---|
| `find_component(description)` | informal name → candidate tags with match reasons ("feed drum", "the spare pump", legacy tags) |
| `get_component(tag)` | decoded tag, kind, sheet, attributes, counts of links/mentions/notes |
| `get_loop(loop)` | loop members with roles and missing roles |
| `get_sheet(sheet)` | everything on a sheet + off-page connectors |
| `get_neighbors(tag)` | connected components with relation and status |
| `get_protection(tag)` | relief devices, alarms, interlocks |
| `search_sources(query, tag?, kind?, limit)` | snippets with IDs, author, date |
| `get_source(id)` | full original text of one source |
| `get_history(tag)` | dated timeline: revisions + change/decision/issue mentions |
| `compare_records(tag)` | drawing vs valve list vs register vs what sources state |
| `get_gaps(tag? / sheet?)` | gaps with severity |
| `get_notes(tag)` | senior notes |
| `highlight(tags)` | tells the UI which components to light up |
| `add_note`, `record_correction`, `flag_issue` | **senior mode only**: not even in the schema list sent to the model in junior mode, and `dispatch()` refuses them |

Write tools validate their input (unknown tags / links are refused) before persisting.

---

## 7. Question time (`agents/conversation.py`, `core/llm.py`)

```python
ask(question, history=None, mode="junior", kb=None, on_step=None)
  -> {answer, gaps, highlight, confidence, trace, check, not_recorded}
```

1. **System prompt** (`agents/prompts.py: CONVERSATION_PROMPT`): role (the senior engineer mentoring a new hire), evidence rules, procedure (resolve names with `find_component` first, check gaps and notes for anything discussed, call `highlight`), JSON output format. Mode rules are injected; senior mode may write only when the user explicitly asks.
2. **Tool loop** (`run_tools`): OpenAI-style function calling against `https://api.asi1.ai/v1`, model `asi1`. Up to **12 rounds**; each round can request several tool calls. Every call is appended to the **trace** `{step, tool, args, result}`; `on_step` fires after each one for streaming. Bad arguments or tool exceptions are returned to the model as an error envelope instead of crashing. If the budget runs out, the model is told to answer with what it has.
3. **Citation check** (`core/checks.py: check_citations`): extracts every `[...]` citation, and checks each ID is in the set of `citations` returned by tools **in this answer's trace**. `[general]` and `[inference]` are allowed labels. Markdown links `[x](url)` are ignored.
4. **One repair pass:** if any citation is unknown, the model gets the bad IDs plus the valid list and rewrites the answer with no new tool calls. The rewrite is kept only if it has fewer unknown citations. `check.regenerated` records that it happened, and any remaining bad IDs are shown in the UI.
5. **Post-processing:** `highlight` is the union of the answer's list and any `highlight` tool calls, filtered to real components; `not_recorded` lists every tool call that came back empty.

Typical answer: 5–10 tool calls, 30–60 s. `format_text()` renders the same result as plain text for ASI:One: answer → "How I found this" (numbered trace) → gaps.

### Docs writer (`agents/docs_writer.py`)

Code assembles a fact pack per piece of equipment by calling read tools in parallel; the LLM writes a beginner page from that pack only; `check_citations` validates it against the pack's citations. Output: `out/docs/<tag>.md`. Command line only (`build_kb.py --docs`), not in the UI yet.

---

## 8. API (`app/api/main.py`, FastAPI on Railway)

Thin wrappers, no business logic. KB loaded once at startup.

| Endpoint | Behavior |
|---|---|
| `POST /ask` `{question, history, mode}` | creates a job, runs `ask()` in a daemon thread, returns `{job_id}` immediately |
| `GET /ask/{job_id}/events` | **Server-sent events**: `step` per tool call `{step, tool, args, summary}`, then `done` (full result) or `error`. Keepalive comment every 15 s so proxies don't cut the stream |
| `DELETE /ask/{job_id}` | sets a cancel flag; the next `on_step` raises and the job ends |
| `GET /sheets`, `/sheets/{id}/svg`, `/sheets/{id}/overlay` | sheet list, the drawing SVG (cached 1 h), components with bbox + status + CV layer |
| `GET /tools/{name}?…` | read tools for the UI's side panel; write tools refused |
| `GET /source/{id}` | data for citation popovers |
| `GET /health` | `{"ok": true, "components": 33}` for Railway |

History is capped at the last 6 turns. Jobs live in an in-memory dict, so the API must run as **one instance**.

**Overlay status** per component: `high` if it has a high-severity gap, `attention` if any gap or an inferred link, else `ok`.

Why not serverless (Vercel functions): `ask()` blocks for up to a minute and senior mode writes to disk.

---

## 9. Web app (`app/web`, Next.js on Vercel)

- **Stack:** Next.js App Router, TypeScript, Tailwind, `@tanstack/react-query` for all GETs, `react-markdown`, `react-zoom-pan-pinch`. No component library, no global state library.
- **Components:** `Diagram.tsx` (SVG drawing + overlay, layers, tag search), `ComponentPanel.tsx` (Details / History tabs), `Chat.tsx` (input, live steps, answer rendering), `SourcePopover.tsx` (Slack thread, Drive doc, revision, register row, gap), `ui.tsx` (citation chips, gap cards).
- **Ask flow:** `POST /ask` → `new EventSource(/ask/{id}/events)` → each `step` event updates the live list → `done` renders the answer, citations, gaps and trace, and pushes `highlight` to the diagram. Stop sends `DELETE`. A dropped connection shows "Lost the connection to the API."
- **Citations:** `splitCitations()` turns `[id]` markers into chips; clicking one fetches `/source/{id}` and opens a popover that matches the source kind.
- **Config:** `NEXT_PUBLIC_API_URL`, baked in at build time.
- **Design:** "night-shift control room" tokens (black background, navy only for selection and citations), designed in Paper.

---

## 10. ASI:One / Agentverse agent (`app/agentverse/`)

- **Protocol:** uAgents with the Agent Chat Protocol (`chat_protocol_spec`), manifest published so ASI:One can discover it. On each `ChatMessage`: send `ChatAcknowledgement` immediately, run `ask()` in a thread (always **junior**, read-only), reply with `format_text()` + `EndSessionContent`. Errors become a reply, not silence.
- **Two ways to run it:**
  - `uagent.py`: runs anywhere with `mailbox=True`; Agentverse holds messages and the process collects them. Address derived from `AGENT_SEED_PHRASE`.
  - `hosted_agent.py` + `build_hosted.py`: runs **on Agentverse**. The hosted editor has flat files and no packages, so `build_hosted.py` copies the 10 backend modules flattened (`core/kb.py` → `core_kb.py`, imports rewritten). Hosted agents reset globals each call, so the agent fetches `kb.json` from GitHub `main` per message and keeps per-user history in `ctx.storage`. Only uses allowed imports (`openai`, `requests`, `uagents`, `python-dotenv`).
- Tested: the flattened bundle answered end to end in 34 s with nothing else from the app loaded.

---

## 11. Evaluation (`scripts/eval.py`, `tests/`)

- `tests/questions.json`: **20 cases**: answerable 7, gap 3, contradiction 2, and one each of cross-diagram, multi-hop, unanswerable, implicit reference, legacy tag, false premise, ambiguity, prompt injection.
- Scoring (all plain code): a case fails if any citation fails the citation check, if it cites none of the expected sources (facts-ledger IDs mapped to citation prefixes), if required terms are missing, or, for gap / unanswerable cases, if it doesn't say "not recorded" (or similar).
- **Prompt-injection case:** the eval adds a fake Slack message with instructions in it to a copy of the KB, then checks the agent treats it as data, not as commands.
- `python scripts/eval.py [-k Q04] [-j 4]`.
- Unit checks: `tests/test_drawings.py`, `tests/test_gaps.py`, and the `__main__` self-check in `core/checks.py`.

---

## 12. Configuration

| Variable | Used by | Purpose |
|---|---|---|
| `ASI1_API_KEY` | everything | ASI:One API key |
| `ASI1_MODEL` | conversation, docs | default `asi1` |
| `ASI1_MODEL_HEAVY` | linker | bulk linking (`asi1-ultra` for final builds) |
| `AGENT_SEED_PHRASE` | `uagent.py` | fixed agent address |
| `CORPUS_DIR` | build | corpus location (default `unit200_update/unit200_corpus`) |
| `CV_RUNS` | build | CV output folders |
| `WEB_ORIGIN` | API | CORS allow-list (default `*`) |
| `NEXT_PUBLIC_API_URL` | web | API base URL |
| `KB_URL` | hosted agent | where to fetch `kb.json` (default: GitHub raw, `main`) |

## 13. Deployment topology

| Piece | Host | Notes |
|---|---|---|
| API | Railway, Docker (`app/api/Dockerfile`, build context = repo root via `/railway.json`) | image contains code, `kb.json` and the drawing SVGs; health check `/health` |
| Web | Vercel, root `app/web` | static pages + client-side fetching |
| Agent | Agentverse hosted | reads `kb.json` from GitHub |
| Model | ASI:One API | |

## 14. Known limits and next steps

| Limit | Why it's fine now | Next step |
|---|---|---|
| Single JSON KB in memory | 33 components, 300 KB | SQLite or Postgres when a plant has thousands of sheets |
| In-memory jobs, one API instance | demo traffic | Redis queue |
| Senior writes on local disk, lost on Railway redeploy | demo | database (e.g. Supabase) |
| No auth, open CORS by default | demo | login + `WEB_ORIGIN` |
| DXF-only drawings | synthetic corpus is CAD | CV adapter for scanned PDFs, verified per link (vision crop check) |
| Hosted agent fetches 300 KB per message | stateless hosting | `ctx.storage` cache or a smaller per-question index |
| Docs writer not in the UI | CLI works | docs tab per component |
| Read-only on ASI:One | anyone can message the agent | allow-list senior users, then enable write tools |
