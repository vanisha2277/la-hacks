# Handoff: project overview

Context for anyone building the presentation. What the product is, why it matters, how it works, and what to show.
Deploy steps live in [app/DEPLOY.md](../app/DEPLOY.md). The original design notes are in the teammate repo `pid_agent/PROJECT_CONTEXT.md`.

> All plant data is **synthetic** (a made-up company and unit). Say so in the demo.

---

## 1. The one-liner

**Handoff lets a new engineer "talk to" the senior engineer who used to own the plant's P&IDs, and it never tells you anything it can't show you.**

Every plant fact in an answer is cited to a drawing, Slack message, Drive document, meeting, or register row, and the answer shows the exact steps the agent took to find it.

---

## 2. The problem

- A **P&ID** (piping and instrumentation diagram) is the master engineering drawing of a plant section: every pipe, vessel, pump, valve, and instrument, and how they're controlled. Operations, maintenance, and safety reviews all depend on it.
- **Drawings drift from reality.** Field changes don't get drawn. Datasheets, registers, and drawings disagree with each other.
- **The "why" lives in people's heads.** Why a valve runs in manual below 40% load, why one pump is preferred, what happened in the 2019 incident: that lives in Slack threads, meeting notes, and the senior engineer's memory.
- **When the senior engineer leaves, it walks out the door.** New engineers spend weeks decoding drawings and asking around, and in a safety-critical plant, a wrong guess is dangerous.
- Existing tools focus on **digitizing** drawings (detecting symbols). None of them **explain** the plant, cross-check the sources, or capture the expert's knowledge.

## 3. The solution

1. **Ingest everything**: the drawings (all revisions), Slack, Google Drive, meeting notes, calendar, tag register, valve list.
2. **Build one verified knowledge base**: link every Slack message and document passage to the equipment it's about, decode tags, group control loops, and run plain-code checks for gaps and contradictions.
3. **Let people ask in plain English**: an AI agent answers like the senior engineer would, but only using facts it looked up through tools, each one cited.
4. **Surface what's missing**: "not recorded" and "these two sources disagree" are first-class answers, never silently filled in.

Two front doors, one brain:
- **Web app**: an interactive drawing next to a chat, for engineers at a desk.
- **ASI:One (Fetch.ai)**: the same agent in a chat, anywhere, no install.

---

## 4. Demo story: the synthetic plant

**Meridian Gas Processing, Harbor Terminal, Unit 200**: a C3/C4 splitter (separates mixed feed into propane and butane).
The senior engineer, **Dana Okafor**, designed the unit and retired in June 2025. It's now October 2026, and a new engineer has inherited it.

What's in the data:
| | |
|---|---|
| Drawings | 2 sheets: PID-100 (feed and preheat), PID-200 (column and overhead), 8 revisions from 2017 to 2024, plus a legend |
| Equipment and instruments | 33 components, 42 connections, 6 cross-sheet connectors |
| Slack | ~200 messages across #unit200-ops, #unit200-eng, #moc-reviews (threads, typos, shorthand) |
| Drive | ~85 passages: incident reports, change forms (MOCs), a stale datasheet, procedures, Dana's partial handover notes |
| Calendar / meetings | 18 events: incident reviews, change reviews, maintenance |
| Registers | tag register (34 rows), valve list |

The data has planted problems the agent must find:
- **Contradiction C01**: the column relief valve's set pressure. Drawing and datasheet say **17.2 barg**; Slack (2021) says it was lowered to **16.5 barg** and the paperwork was never updated.
- **Contradiction C02**: a level valve's fail position. The 2024 drawing says fail-closed; a technician found it still set fail-open in the field in 2025, and the fix was never recorded.
- **Gaps**: a standby pump with zero maintenance history, a relief valve re-rating with no approval document, design data that exists nowhere.

### Good demo questions

| Question | What it shows |
|---|---|
| "What protects the main column from overpressure?" | Finds the relief valve **and** flags the 17.2 vs 16.5 barg contradiction across drawing, datasheet, and Slack |
| "Why did 20LFC20AP001's seal fail in 2019?" | Pulls the incident report, Slack, and meeting notes into one history |
| "What protections were added to the reflux pumps after the 2019 incident?" | Multi-source: the change form, the drawing revision, Slack |
| "Is 20LFC20AA102 fail-open or fail-closed?" | Contradiction C02: drawing vs field reality |
| "Who makes the reflux pumps?" | The data doesn't say, so it answers **"not recorded"** instead of inventing one |

Tags use the **KKS** naming system (e.g. `20LFC10AA191`). Older documents use legacy names (e.g. `PSV-201`), and the agent maps between them.

---

## 5. How it works

### Architecture

```
SOURCES     drawings (DXF/SVG, all revisions) · Slack · Drive · meetings · calendar · registers
               │
BUILD TIME  ingest adapters (one per source)
(offline)      │
            LINKER AGENT: which equipment is each message/passage about?
               │   rules first (exact tags, legacy tags, names), then the LLM for implicit references;
               │   code keeps a link only if the quoted evidence is word-for-word in the source
            DETERMINISTIC CHECKS (plain code, no AI): decode tags, group control loops,
               │   find gaps and contradictions
               ▼
            KNOWLEDGE BASE  (out/kb.json, one file, plant-wide)
               │
QUESTION    TOOLS: the only way into the knowledge base; every call is logged
TIME           │
            CONVERSATION AGENT ("the senior engineer"): plans, calls tools, writes a cited answer
               │
            CITATION CHECKER (plain code): every cited ID must have come from a tool result
               │   in this answer; if not, the agent rewrites once
               ▼
FRONT DOORS  Web app (Next.js)              ASI:One chat
             via FastAPI on Railway         via the agent on Agentverse
```

### The agents

| Agent | Job | AI or code |
|---|---|---|
| **Conversation agent** | Answers questions as the senior engineer. Picks which tools to call, in what order, then writes the answer. | AI (ASI:One `asi1` model) |
| **Linker agent** | At build time, attaches each Slack message, document passage, and meeting to the equipment it's about, including vague references like "don't fight it" or "the spare pump". | Rules + AI, with a code check |
| **Docs writer** | Writes a beginner-friendly page per piece of equipment from a fact pack the code assembles. Built and working from the command line; not shown in the UI yet. | AI + citation check |
| **Gap and contradiction checks** | Incomplete control loops, vessels with no relief valve, register vs drawing mismatches, conflicting values, undocumented equipment. Found 9 gaps (2 high severity). | Plain code |
| **Citation checker** | Rejects any citation that didn't come from a tool result. | Plain code |

### The tools the agent can call

Look things up: `find_component` (turns "the feed drum" into a tag), `get_component`, `get_loop`, `get_sheet`, `get_neighbors`, `get_protection`, `search_sources`, `get_source`, `get_history`, `compare_records`, `get_gaps`, `get_notes`.
Drive the UI: `highlight` (lights up components on the drawing).
Write (senior mode only): `add_note`, `record_correction`, `flag_issue`. These are how the senior engineer's knowledge gets captured permanently.

A typical answer takes **5–10 tool calls and 30–60 seconds**.

### Anti-hallucination rules (the core idea, worth a slide)

1. **The AI is the go-between, never the source.** Plant facts come only from tool results.
2. **Every fact carries a citation**, and code checks the citation was actually returned by a tool in that answer.
3. **Show the real steps, not the AI's story about its thinking.** The UI shows the actual tool calls ("How I found this").
4. **Empty is an answer.** If nothing is recorded, it says "not recorded" and lists it as a gap.
5. **Conflicts are shown side by side.** The agent doesn't pick a winner between the drawing and Slack.
6. **General engineering knowledge and AI reasoning are labeled** `[general]` and `[inference]`, never passed off as plant facts.
7. **Anything code can check, code checks.** AI is used only where judgment is needed.

Tested with **20 evaluation questions** (`app/tests/questions.json`) covering normal answers, gaps, contradictions, cross-sheet questions, legacy tags, false premises, an unanswerable question, and a prompt-injection attempt.

---

## 6. The web app (UI)

Mood: **a night-shift control room**. Mostly black; navy only marks selections and citations. Designed in Paper ("Witty beacon" file).

**Left: the drawing**
- The real P&ID (vector SVG), zoom and pan, switch between sheets.
- An interactive layer over the drawing: components the answer is about light up; components with problems get markers (high severity / needs attention).
- Layer toggles: Drawing, Cited, CV layer (computer-vision detections, shown as dashed boxes).
- Tag search.
- **Click any component** to open a side panel:
  - **Details**: what it is, its control loop, drawing vs register vs sources side by side (mismatches highlighted).
  - **History**: dated timeline of changes, incidents, and decisions from all sources.

**Right: the chat**
- Ask anything; a clicked component can be attached as context.
- **While working**: live list of each tool call as it happens (streamed).
- **The answer**: markdown with inline citation chips, gaps found, and "How I found this" (the tool trace).
- **Click a citation** to open the source in a popover: a Slack thread, a Drive document, a drawing revision, a register row, or a gap.
- **Junior / Senior toggle**: Senior mode lets the agent save notes, corrections, and flags.
- New chat, stop button, keep typing while it works.

---

## 7. Fetch.ai / ASI:One integration

- The agent is registered on **Agentverse** and discoverable through **ASI:One**. It speaks the Agent Chat Protocol.
- It's set up to be **hosted on Agentverse** (runs on Fetch's servers, not ours; see [app/DEPLOY.md](../app/DEPLOY.md) step 4) and calls the same `ask()` as the web app.
- The whole question → cited answer flow works **inside an ASI:One chat**, no custom frontend needed, which is a Fetch requirement.
- The model behind everything is ASI:One's `asi1` (OpenAI-compatible API).
- Answers in ASI:One are plain text: answer, then "How I found this" (numbered tool calls), then gaps.

## 8. Tech stack

| Layer | Tech | Hosted on |
|---|---|---|
| Model | ASI:One `asi1` | Fetch.ai |
| Backend | Python 3.12, OpenAI SDK pointed at ASI:One | |
| API | FastAPI, streaming progress (server-sent events) | Railway |
| Web | Next.js (App Router, TypeScript), Tailwind, react-markdown, react-zoom-pan-pinch, TanStack Query | Vercel |
| Agent | uAgents, Agent Chat Protocol | Agentverse (hosted) |
| Knowledge base | one JSON file (`out/kb.json`), rebuilt by `scripts/build_kb.py` | |
| Drawings | DXF (CAD) parsed with ezdxf, rendered to SVG | |

## 9. Repo map

```
app/
  core/          knowledge base, tag decoding, gap checks, tools, LLM client, citation checks
  agents/        conversation agent, linker, docs writer, all prompts
  ingest/        one adapter per source: drawings, Slack, Drive, calendar, registers, revisions, CV
  scripts/       build_kb.py (build the knowledge base), ask.py (CLI), eval.py (run the 20 questions)
  api/           FastAPI service + Dockerfile (Railway)
  web/           Next.js app (Vercel)
  agentverse/    the ASI:One agent: uagent.py (local), hosted_agent.py + build_hosted.py (Agentverse)
  out/kb.json    the built knowledge base
unit200_update/unit200_corpus/   the synthetic plant: drawings, Slack, Drive, calendar, registers, story.md
docs/            this file
```

---

## 10. Pitch lines

- "It never tells you anything it can't show you."
- "When your senior engineer retires, their knowledge doesn't have to."
- "Not recorded is an answer." (and a safer one than a confident guess)
- "Most AI tools digitize drawings. Handoff explains them, checks them against everything else, and admits what it doesn't know."
- "One brain, two front doors: the web app at your desk, ASI:One anywhere."

## 11. Honest limits (for Q&A)

- **Synthetic data.** Real plants would need an adapter for their drawing format; scanned PDFs need computer vision, which we treat as a hint layer, not as facts.
- **No login yet.** Anyone with the link can use it.
- **Senior notes don't persist across redeploys** (no database yet).
- **Docs writer isn't in the UI yet** (command line only).
- **Answers take 30–60 s**, because the agent does real multi-step lookups. The UI streams each step so you can see progress.
- It doesn't replace engineers: it captures and shares the senior engineer's knowledge, and engineers verify it through the citations.

## 12. Glossary

| Term | Meaning |
|---|---|
| P&ID | Piping and instrumentation diagram: the detailed engineering drawing of a plant section |
| KKS | A tag naming system for plant equipment (e.g. `20LFC10AA191`) |
| Legacy tag | Older name for the same thing (e.g. `PSV-201`) |
| PSV | Pressure safety valve: opens to stop a vessel from over-pressurizing |
| Control loop | Sensor → controller → valve, working together to hold a value |
| MOC | Management of change: the formal approval process for plant modifications |
| barg | Pressure in bar above atmospheric |
| Gap | Missing, conflicting, or unverified information, shown explicitly |
| Trace | The logged sequence of tool calls behind an answer ("How I found this") |
