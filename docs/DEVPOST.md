## What it does

**Handoff lets a new engineer ask about any part of their unit and get the answer the senior engineer would have given, on the drawing itself.**

**It connects the dots**

The core of Handoff is the **links**. Every Slack message, document section, meeting, register row and drawing revision is attached to the exact valve, instrument or vessel it's about, even when it never names it. "dont fight it and dont crank the gain back up" gets linked to the feed flow controller, FIC-101. "its been doing that since the trim change" gets linked to reflux control valve FV-201. "i think its misalignment, shaft was off when i checked" gets linked to reflux pump P-102A.

On the demo unit that's **360 links from 307 sources to 26 components**, and **115 of them came from messages that never mention a tag**. A search bot only finds text that matches your words; Handoff knows that a 2020 Slack thread, an MOC form, a procedure update and Rev 2 of the drawing are all about the same control valve, and puts them on one timeline. Each link is kept only if its quoted evidence appears word for word in the source.

**The drawing is the interface**
- The real P&ID (piping and instrumentation diagram, the master drawing of every line, valve and instrument), rendered from CAD, with zoom, pan and sheet tabs.
- When the agent answers, **the components it's talking about light up on the drawing**. Components with open problems carry markers by severity.
- **Click any valve, instrument or vessel** for a side panel:
  - **Details:** what it is, its control loop (transmitter → controller → final element), and **the drawing vs the valve list vs the register vs what people said, side by side**, with mismatches highlighted.
  - **History:** a dated timeline for that one tag: every revision that touched it **with the exact field change** (e.g. `Cv 45 → 75` in Rev 2, `fail position FO → FC` in Rev 5), plus the MOCs, incidents, Slack decisions and meetings about it.
- A **CV layer** overlays computer-vision detections on the sheet as dashed boxes, so you can compare what the model sees with what CAD says.

**The agent answers like the senior engineer**
- "What does FIC-201 do?" works with the legacy tag, the KKS tag or a nickname like "the reflux drum".
- It traces the loop, explains it in plain language, and surfaces the standing instruction nobody drew: **run it in manual below 40% load**, from a 2020 Slack thread the senior engineer approved, still in the 2025 procedure, root cause never fixed.
- It's **revision-aware**: a value conflict only counts if the source is *newer* than the revision that last set that attribute on the drawing.
- When records disagree, it **shows both values with source and date** and says what's unresolved, instead of picking one.
- When nothing is recorded (who makes the reflux pumps, the controller's setpoint), it says **"not recorded"** and lists it as a gap.
- Every fact is a **citation chip**. Click it to open the exact Slack thread, Drive section, drawing revision, register row or MOC. "How I found this" shows the real tool calls it made.

**Two ways in**
- The web app, for engineers at a desk.
- **ASI:One**, for the same agent in a chat, anywhere.

All data in the demo is **synthetic**: a made-up C3/C4 splitter unit, a retired senior engineer named Dana, and about 300 Slack messages, document sections and meetings with deliberate contradictions and gaps.

## Inspiration

Process units run for decades. Engineers don't.

When a new engineer inherits a process unit, the drawings are only half the story. A **P&ID** (piping and instrumentation diagram) shows every pipe, valve and instrument, but it doesn't say *why* a valve runs in manual below 40% load, which pump everyone quietly prefers, or that the relief valve was re-set in 2021 and nobody updated the datasheet. That lives in Slack threads, meeting notes and one senior engineer's head. When that person retires, it walks out the door, and the new hire spends months asking around. In a gas processing unit, a wrong guess is a safety problem.

That's the onboarding problem at its sharpest: scattered knowledge, unfamiliar systems, and nobody to ask. And it isn't only retirements: every time an engineer switches units, moves projects or covers for a colleague, the same ramp-up starts again. We wanted a new engineer's first week to feel like sitting next to the person who built the unit.

### Why a search bot can't do this

The knowledge isn't just scattered, it's tied to a drawing that keeps changing:

- **Revisions pile up.** Our demo unit has two sheets and **8 revisions from 2017 to 2024**, each tied to an MOC (Management of Change). The revision block gives one line per revision for the whole sheet; the history of a single valve means reading every revision and every MOC behind it.
- **Records disagree.** The P&ID, the instrument datasheet, the valve list and the tag register are maintained by different people at different times. Our relief valve is **17.2 barg** on the drawing and datasheet, but a 2021 Slack thread says it was re-set to **16.5 barg**, and no approval exists. A level valve is drawn fail-closed; a technician found it still set fail-open in the field.
- **Tags change names.** Older documents say `PSV-201` and `LV-202`; the current drawings use KKS (`20LFC10AA191`, `20LFC20AA102`). Search for one and you miss the other.
- **Nobody names the equipment.** Engineers write "the drum", "the loop is chasing it" and "dont fight it", not `20LFC20AP002`. The thread that explains a valve often never says which valve it means.
- **Answers cross sheets.** A bypass that can't be fully opened on one sheet is explained by a trip on another, connected through an off-page connector.

Generic AI tools can search Slack or summarize a PDF. None of them **connect a message to the component it's about**, understand the **drawing as a connected system**, track **what changed in which revision**, or notice when **two official records disagree**.

## How we built it

**Build time (offline)**

1. **Drawings from CAD, not pictures.** We parse the DXF directly (ezdxf): 33 components, 42 connections, 6 off-page connectors across two sheets, each with exact tags, positions and connections. Every revision is **diffed against the previous one** at the attribute level, which is how History can say "Cv 45 → 75 in Rev 2".
2. **Records:** tag register and valve list, kept separate so disagreements stay visible.
3. **Connecting the dots (linker agent):** attaches each Slack message, document section and meeting to the equipment it's about, including "dont fight it" in a thread where the controller is only named earlier on. Rules handle exact KKS and legacy tags first; the model handles implicit references; **code keeps a link only if the quoted evidence appears word for word** in the source.
4. **Plain-code checks** (no AI): decode KKS tags, group control loops, and flag value conflicts, changes not reflected on the drawing, vessels with no relief device, register-vs-drawing mismatches, dangling off-page connectors and undocumented equipment. On the demo unit: **9 gaps, 2 of them high severity**.
5. **Computer vision:** our CV model detects symbols on the PDF of each sheet (category, bounding box, tag read, confidence) and we match detections against the CAD tags. On PID-100 it found **14 symbols, matched 12 to known tags, and suggested the right tag for the other 2** where the tag read was off.

**Question time**

6. **Conversation agent:** plans and calls tools (`find_component`, `get_loop`, `get_neighbors`, `get_protection`, `compare_records`, `get_history`, `get_gaps`, `search_sources`, `highlight` and more), typically 5–10 calls per answer.
7. **Citation checker** (code): every cited ID must have come back from a tool call in *this* answer. If not, the agent rewrites once.

The rule underneath: **the model is the go-between, never the source.** Anything code can check, code checks.

### Agents + tools

**Agents.** Three of them, each with code checking its work:

- **Linker** (build time) reads every conversation, document and meeting and decides which components it's about. *Code checks* that the quoted evidence exists word for word, the tag is real, and the anchor message actually names it.
- **Conversation agent** (every question) plans, calls tools and writes the answer as the senior engineer. *Code checks* that every citation came from a tool result in that answer.
- **Docs writer** (build time) writes a beginner page per component from a fact pack that code assembles. *Code checks* that every citation is in the fact pack.

**Tools.** The conversation agent can only reach the knowledge base through these, and each returns `data`, `citations` and an `empty` flag:
- **Find:** `find_component` turns "the feed drum" or `PSV-201` into the right tag; `get_component` returns its type, sheet and attributes.
- **Trace the drawing:** `get_loop` (transmitter → controller → final element, and any missing role), `get_neighbors` (what it connects to), `get_protection` (relief devices, alarms, trips), `get_sheet` (everything on a sheet plus off-page connectors).
- **Read the history:** `search_sources`, `get_source` (the full original thread or document), `get_history` (revisions, MOCs and decisions as one timeline), `get_notes` (senior notes).
- **Check the records:** `compare_records` (drawing vs valve list vs register vs what people said), `get_gaps` (known gaps and conflicts with severity).
- **Drive the UI:** `highlight` lights components up on the drawing.
- **Write (senior mode only):** `add_note`, `record_correction`, `flag_issue`.

**How a question gets answered**
- The agent works in a **tool loop of up to 12 rounds**, and can call several tools per round. It follows a procedure: resolve informal names first, check gaps and senior notes for anything it discusses, compare records for any value, and highlight what it's talking about.
- **Every step streams live** to the UI as it happens ("Tracing the control loop", "Checking known gaps"), and the user can stop it at any time.
- **Failures don't crash the answer.** A bad argument or a tool error goes back to the model as an error result it can recover from; if the round budget runs out, it answers with what it has.
- **Citation gate:** after the answer is written, code checks every cited ID against what tools actually returned. If any are unknown, the agent gets one rewrite with the valid list, and anything still unverified is flagged in the UI.

**Permissions live in code, not the prompt.** In junior mode, the write tools (`add_note`, `record_correction`, `flag_issue`) aren't even offered to the model, and the dispatcher refuses them if called. Senior writes are validated and stored separately, so rebuilding the knowledge base never erases what an engineer recorded.

**One brain, two front doors.** The web app and ASI:One call the same `ask()`. On Agentverse the agent runs hosted, keeps per-user history between messages, and answered end to end in 34 seconds with nothing else from our app running.

**Cheap to rebuild.** The linker runs 4 workers in parallel, one model call per conversation, and caches every call by content hash, so rebuilding after a code change makes zero model calls unless the source text changed.

**Tested like software.** A 20-question eval is scored by code: an answer fails if any citation fails the check, if it misses the expected sources, or if it doesn't say "not recorded" when it should. One case plants a Slack message containing instructions, and the agent has to treat it as data, not commands.

**Stack:** Python and FastAPI on Railway, Next.js on Vercel, ASI:One's `asi1` model, uAgents on Agentverse, ezdxf for CAD, and **Paper** for design.

### Designed in Paper

Every screen started on a Paper canvas before it became code: the drawing-and-chat workspace, component panels, source viewer, home grid and the computer-vision review. Our coding agents built from the canvas over Paper's MCP, so design and app stayed in step.

- **Fundamentals.** One rule for color: black everywhere, navy only for what's selected or cited, amber only for "these records disagree", so a flag is impossible to miss. Three typefaces with three jobs: Inter Tight for headings, Inter for prose, JetBrains Mono for anything you'd copy (tags, revisions, source IDs). We checked contrast with the WCAG formula and raised our dimmest text color until it passed AA (4.5:1) on our page and panel backgrounds.
- **Ease of use.** The P&ID gets most of the screen and answers light up on it, so you never switch views. An empty chat offers three starter questions you can ask in one click. Every popup closes with a visible ×, Esc or a click outside. Keyboard users get a high-contrast focus ring, and animations turn off for people who ask their system for reduced motion.
- **Character.** The look is a night-shift control room, because that's where this gets used: next to SCADA screens, often at night. The logo came from the drawing itself. Out of three marks sketched in Paper we picked a valve: two halves meeting at a point, one engineer's knowledge passed to the next.

## Built for anyone picking up a unit (Workday)

- **Who it's for:** anyone who has to get up to speed on a unit they didn't design:
  - **New hires and early-career engineers** in their first months.
  - **Engineers switching units or projects** inside the company. Internal moves happen far more often than retirements, and each one restarts the ramp-up.
  - **Maintenance and reliability engineers** who need a valve's history and known issues before they touch it.
  - **The senior engineers and managers** handing a unit over, who can record what they know before they move on.
- **What the agent does on its own:** finds the right component from any name, plans which records to check, compares drawing, revisions, registers and conversations, and highlights the answer on the drawing.
- **Where the human stays in control:**
  - In *junior* mode, the agent is **read-only**.
  - In *senior* mode, it can save notes, corrections and flags, but **only when the engineer explicitly asks**, and it confirms what it saved.
  - When records conflict, **the agent doesn't pick a winner**; the engineer decides.
  - Low-confidence CV detections go to a **review step** where a person accepts or fixes them.
- **Transparent:** every fact links to its source, and the tool trace is the real one. General engineering knowledge and the agent's own inferences are labeled `[general]` and `[inference]`.
- **Reliable under uncertainty:** "not recorded" and "these records disagree" are real answers. We test against 20 questions, including false premises, an unanswerable question and a prompt-injection message hidden in Slack.
- **Privacy:** no personal or real employee data. Everything is synthetic, and the agent sees only engineering records through its tools.
- **What it won't do:** decide safety settings, approve an MOC, or fill a gap with a guess.

## Fetch.ai: from intent to action in ASI:One

- Registered on **Agentverse**, discoverable through **ASI:One**, and speaks the **Agent Chat Protocol**.
- The whole workflow (question → tool calls → cited answer with gaps) runs **inside an ASI:One chat**, with no custom frontend needed.
- Not a thin wrapper: a multi-step tool-using agent over a knowledge base built by a second (linker) agent, with code checking both.

## Challenges

- **Slack doesn't name things.** "dont fight it and dont crank the gain back up" is about FIC-101, which is only named earlier in the thread. We link at the conversation level and track which message actually names the component.
- **Models cite things that aren't there.** Plausible-looking IDs that no tool returned are why the citation checker and repair pass exist.
- **"Newest wins" is wrong.** A newer Slack message isn't automatically right, and an older one may be superseded by a later revision. Conflicts had to be revision-aware and shown, never silently resolved.
- **CAD vs computer vision.** Line tracing on scanned P&IDs is still the hardest unsolved part of digitization. We use CAD for exact connectivity and CV as a second opinion, matched against CAD tags.
- **Readable answers.** Accurate answers came out as dense walls of text. We rewrote the format so each answer leads with the one thing you must know, then short sections.

## What we learned

- The P&ID has to be the **center of the product**, not an attachment. Engineers think in sheets, loops and tags, so answers have to land on the drawing.
- Trust comes from **structure, not tone**: citations checked by code, revision-aware conflicts, and "not recorded" as a real answer.
- Most of the value is in the **"why" behind each revision**, and that lives in conversations and MOCs, not on the drawing.

## What's next

The CV model already detects symbols and reads tags on scanned sheets. That's what turns Handoff from "works where there's CAD" into "works at any site", and we're seriously pursuing it:

- **Scanned-only and brownfield sites.** Many older units only have PDFs or scans of their P&IDs. Next is line tracing, so CV builds the full connectivity graph (what connects to what) and the same agent works with no CAD at all.
- **Red-line and as-built detection.** Scan a field-marked-up drawing, compare it with the current CAD revision, and list every hand-drawn change that never made it into an official revision.
- **Revision diffs from scans.** Compare two scanned revisions symbol by symbol, so "what changed in Rev 4" works for units whose history is paper.
- **More drawing types.** PFDs, isometrics, electrical single-lines and cause-and-effect matrices, all linked to the same tags.
- **MOC impact review.** Before a change, list everything upstream and downstream, every procedure and datasheet that references the tag, and every past incident on it.
- **Maintenance and process data.** Connect a CMMS and the historian, so "zero maintenance history on the standby pump" and "this valve has been at 95% open for a month" show up next to the drawing.
- **Handover mode.** Before a senior engineer leaves, Handoff walks them through every gap it found so they can fill it in while they're still around.
