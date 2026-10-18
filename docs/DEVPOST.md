## Inspiration

Process units run for decades. Engineers don't.

When a new engineer inherits a process unit, the drawings are only half the story. A **P&ID** (piping and instrumentation diagram) shows every pipe, valve and instrument, but it doesn't say *why* a valve runs in manual below 40% load, which pump everyone quietly prefers, or that the relief valve was re-set in 2021 and nobody updated the datasheet. That lives in Slack threads, meeting notes and one senior engineer's head. When that person retires, it walks out the door, and the new hire spends months asking around. In a gas processing facility, a wrong guess is a safety problem.

That's the onboarding problem at its sharpest: scattered knowledge, unfamiliar systems, and nobody to ask. We wanted a new engineer's first week to feel like sitting next to the person who built the unit.

## What it does

**Handoff lets a new engineer ask about any part of their unit and get the answer the senior engineer would have given.**

- **Ask in plain English.** "What does FIC-201 do?" Old tag names, nicknames ("the reflux drum") and new KKS tags all work.
- **See it on the drawing.** The equipment the answer is about lights up on the real P&ID. Click any valve or instrument for what it does, what it connects to, its full revision history, and any known problems.
- **Get the knowledge that never made it onto paper.** Answers pull together the drawings, every revision, Slack, Drive, meetings and the tag register, so "run it in manual below 40% load" surfaces from a 2020 Slack thread the senior engineer signed off on.
- **See disagreements, not a guess.** The datasheet says the relief valve is set at 17.2 barg, a Slack message says 16.5, and there's no approval on record. Handoff shows both, says who said what and when, and flags it.
- **Hear "not recorded" when the record is silent.** Asked who makes the reflux pumps, it says the data doesn't say instead of inventing a vendor.
- **Use it anywhere.** The same agent runs in our web app and inside **ASI:One**, with no install.
- **Add a new unit from scanned drawings.** A computer-vision pass detects symbols on a PDF, and the engineer reviews anything low-confidence before it's accepted.

All data in the demo is **synthetic**: a made-up gas processing unit, a retired senior engineer named Dana, and about 300 messages and documents with deliberate contradictions and gaps.

## How it works

**Build time (offline)**

1. **Ingest** every source: CAD drawings (DXF, all 8 revisions), Slack, Drive, calendar, the tag register and valve list.
2. **Linker agent:** attaches each message and document passage to the equipment it's about, including vague references like "don't fight it" or "the spare pump". Rules handle exact tags first; the model handles implicit references; then code keeps a link **only if the quoted evidence appears word for word** in the source.
3. **Plain-code checks** (no AI): decode tags, group control loops, and find gaps and contradictions. On our demo unit they found 9 gaps, 2 of them high severity.

**Question time**

4. **Conversation agent:** plans and calls tools (`find_component`, `get_loop`, `compare_records`, `get_history`, `get_gaps`, `search_sources`, `highlight` and more), usually 5–10 calls per answer, then writes the answer.
5. **Citation checker** (code): every cited ID must have come back from a tool call in *this* answer. If one didn't, the agent rewrites once.

The rule underneath all of it: **the model is the go-between, never the source.** Anything code can check, code checks.

**Stack:** Python and FastAPI on Railway, Next.js on Vercel, ASI:One's `asi1` model, uAgents on Agentverse, ezdxf for CAD. The UI was designed in **Paper**: a "night-shift control room" look, mostly black with navy only for selections and citations, built screen by screen on the canvas and then ported to code.

## Built for the first months on the job (Workday)

- **Who it's for:** new hires and early-career engineers ramping into a unit they didn't design, plus the senior engineers and managers who mentor them.
- **What the agent does on its own:** finds the right component, plans which sources to check, cross-references drawings, revisions and chat history, and highlights what matters on the drawing.
- **Where the human stays in control:**
  - In *junior* mode, the agent is **read-only**.
  - In *senior* mode, it can save notes, corrections and flags, but **only when the engineer explicitly asks**, and it confirms what it saved.
  - When sources conflict, **the agent doesn't pick a winner**; the engineer decides.
  - Low-confidence computer-vision detections go to a **review step** where a person accepts or fixes them.
- **Transparent:** every fact is cited to a source you can open, and "How I found this" lists the actual tool calls it made, not a story about its reasoning. General engineering knowledge and the agent's own inferences are labeled as such.
- **Reliable under uncertainty:** "not recorded" and "these sources disagree" are real answers. We test against 20 questions, including false premises, an unanswerable question and a prompt-injection message hidden in Slack.
- **Privacy:** no personal or real employee data. Everything is synthetic, and the agent sees only engineering records through its tools.
- **What it won't do:** make the call for you on safety settings, approve changes, or fill gaps with guesses.

## Fetch.ai: from intent to action in ASI:One

- Registered on **Agentverse**, discoverable through **ASI:One**, and speaks the **Agent Chat Protocol**.
- The whole workflow (question → tool calls → cited answer with gaps) runs **inside an ASI:One chat**, with no custom frontend needed.
- It's not a thin wrapper: a multi-step tool-using agent over a knowledge base built by a second (linker) agent, with code checking both.

## Challenges

- **Slack doesn't name things.** "dont fight it, just let it ride" refers to a valve three messages up. Linking at the message level missed it, so we link at the conversation level and track which message actually names the component.
- **Models cite things that aren't there.** Early answers cited plausible-looking IDs that no tool had returned. That's why the citation checker and the one-rewrite repair pass exist.
- **"Helpful" answers that pick a side.** The model kept quietly choosing the newest value in a contradiction. We had to make "show both, say what's unresolved" a hard rule, and back it with a code-level comparison.
- **CAD vs computer vision.** Tracing lines on scanned drawings is still the hardest unsolved part of P&ID digitization. We read CAD directly for precision and use vision as a second opinion and a path for sites that only have PDFs.
- **Readable answers.** The first answers were accurate but dense walls of text. We rewrote the format rules so each answer leads with the one thing you must know, then short sections.

## What we learned

- Trust comes from **structure, not tone**: citations checked by code, conflicts shown side by side, and "not recorded" treated as a real answer.
- A good onboarding agent is a **go-between**, not an oracle. Its job is to route a new hire to the right record and the right person, fast.
- Most of the value is in the **"why"** behind the drawing, and that lives in conversations, not documents.

## What's next

Real CV ingestion for scanned-only sites, auto-generated beginner docs per piece of equipment (already working from the command line), and a handover mode where a retiring engineer reviews the gaps Handoff found and fills them in before they leave.
