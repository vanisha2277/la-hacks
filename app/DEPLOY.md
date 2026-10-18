# Deploying Handoff

For the repo owner (`vanisha2277/la-hacks`). Everything is already on `main`; this is only dashboard setup.
Do it in this order: each step needs the URL from the one before.

| Piece | Runs on | Who calls it |
|---|---|---|
| API (`app/api`) | Railway | the web app |
| Web (`app/web`) | Vercel | people in a browser |
| Agent (`app/agentverse`) | Agentverse (hosted) | ASI:One |

You need: the `ASI1_API_KEY` (from asi1.ai → API keys), and to be logged into Railway, Vercel and agentverse.ai with an account that can see this GitHub repo.

---

## 1. API on Railway (~10 min)

1. railway.com → **New Project** → **Deploy from GitHub repo** → `vanisha2277/la-hacks`.
   If the repo isn't listed: **Configure GitHub App** and give Railway access to it.
2. Leave **Root Directory** empty. `/railway.json` already points Railway at `app/api/Dockerfile`.
3. Service → **Variables** → add:
   - `ASI1_API_KEY` = your key
4. Service → **Settings** → **Networking** → **Generate Domain**. Copy the URL (`https://<something>.up.railway.app`).
5. Wait for the deploy to go green, then open `https://<something>.up.railway.app/health`.
   Expect: `{"ok": true, "components": 33}`.

Every push to `main` redeploys it automatically.

## 2. Web on Vercel (~5 min)

1. vercel.com → **Add New** → **Project** → import `vanisha2277/la-hacks`.
2. **Root Directory**: `app/web` (click Edit next to it). Framework auto-detects as Next.js.
3. **Environment Variables** → add:
   - `NEXT_PUBLIC_API_URL` = the Railway URL from step 1.4, **no trailing slash**
4. **Deploy**. Copy the Vercel URL (`https://<something>.vercel.app`).
5. Open it and ask a question. You should see tool steps stream in, then a cited answer (30–60 s).

`NEXT_PUBLIC_API_URL` is baked in at build time: if you change it, **Redeploy** in Vercel.

## 3. Lock the API to your site (~2 min)

Back in Railway → **Variables** → add:
- `WEB_ORIGIN` = the Vercel URL from step 2.4 (no trailing slash)

Railway redeploys. Reload the Vercel site and ask one question to check it still works.
(If it says it can't reach the API, the two URLs don't match exactly. Check `https` and trailing slashes.)

## 4. Agent on Agentverse, hosted (~20 min)

The agent runs on Agentverse's servers and reads `app/out/kb.json` straight from GitHub `main`, so the repo must stay **public**.

1. Build the files to paste (needs only Python 3, no installs):
   ```bash
   git pull
   python3 app/agentverse/build_hosted.py
   ```
   This writes 11 files into `app/agentverse/hosted/`.
2. agentverse.ai → **Agents** → **Launch an Agent** → create a blank **hosted** agent.
3. In the code editor:
   - Replace the contents of `agent.py` with `app/agentverse/hosted/agent.py`.
   - For each of the other 10 files, click **+ New File**, give it the **exact same name** (e.g. `core_kb.py`, `agents_conversation.py`), and paste its contents.
4. **Agent Secrets** → add `ASI1_API_KEY` = your key.
5. Fill in the profile: name, short description, and the README (paste `app/agentverse/AGENT_README.md`, see the warning below).
   ASI:One uses this text to decide when to pick the agent, so use the words people will search: P&ID, plant engineer, process safety, handover, Unit 200.
6. Click **Start**. Open **Agent Logs** and check there are no errors.
7. Test it: on asi1.ai, message the agent (search for it, or paste its address from the agent page) with
   *"What protects the main column from overpressure?"* Expect a cited answer about PSV-201 in ~30–60 s.

> **README is out of date.** `AGENT_README.md` still describes a "flash unit" and V-200, which aren't in the data. Rewrite it for the Unit 200 C3/C4 splitter before pasting, or judges' first questions will come back "not recorded".

> **One agent only.** Torazo ran a local test agent (`pid-senior-engineer`, address `agent1qdfuaz...`). Once the hosted one works, make sure that local one is stopped, and delete it from Agentverse if it shows up in your account, so ASI:One doesn't route people to a dead agent.

**Updating the agent later:** code changes → `git pull`, rerun `build_hosted.py`, re-paste the changed files, restart.
Data changes (`kb.json`) → just push to `main`; the agent fetches it on every message.

## 5. Fetch.ai submission

- Show the agent being used **inside an ASI:One chat** in the demo video.
- Submit on the **Submission Agent** too, not just Devpost: https://asi1.ai/festival/lahacksai2026/dashboard

---

## If something breaks

| Symptom | Likely cause |
|---|---|
| Railway build fails | Check the build log. The Docker build context is the repo root, so the root `railway.json` must stay. |
| `/health` 502 or timeout | Deploy still starting, or `ASI1_API_KEY` missing. Check Railway **Deploy Logs**. |
| Web says "Can't reach the API" | `NEXT_PUBLIC_API_URL` wrong (redeploy after fixing), or `WEB_ORIGIN` doesn't match the Vercel URL exactly. |
| Answers fail with an auth error | `ASI1_API_KEY` wrong or out of credits. |
| Agent never replies in ASI:One | Agent not started, or error in **Agent Logs**. If replies cut off at ~30 s, Agentverse is timing out the handler. Fallback: run `app/agentverse/uagent.py` on Railway as a second service (start command `python agentverse/uagent.py`, same variables plus `AGENT_SEED_PHRASE`, no healthcheck), then connect its mailbox via the inspector link in its logs. |
| Agent errors on `kb.json` | Repo was made private, or `app/out/kb.json` was moved. Set an Agent Secret `KB_URL` to a public URL of the file. |

## Known limits (fine for the demo)

- **No login.** Anyone with the Vercel link can ask questions (spending your ASI1 credits) and use Senior mode to write notes. Don't post the link publicly.
- **Senior notes reset on every Railway redeploy** (no database). Don't build the demo around notes written earlier in the day.
- **One API instance only.** Jobs live in memory; don't scale the Railway service past 1 replica.
