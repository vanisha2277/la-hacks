# Handoff

Ask the plant: P&ID answers cited to the drawings, registers, Slack, Drive and meetings. The Unit 200 data is synthetic.

```
app/
  config.py core/ agents/ ingest/ scripts/ tests/   backend, copied from pid_agent (see its docs/BACKEND_INTEGRATION.md)
  out/kb.json  out/cache/link/                      built knowledge base + linker cache (committed so deploys need no LLM build)
  api/        FastAPI wrapper (Railway)              api/main.py, api/Dockerfile
  web/        Next.js app (Vercel)
```

The only change to the copied backend: `ask(..., on_step=)` / `run_tools(..., on_step=)` call back after each tool call, so `/ask/{job}/events` can stream progress.

## Run locally

```bash
cd app
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt fastapi uvicorn
cp .env.example .env                      # fill ASI1_API_KEY
.venv/bin/python scripts/build_kb.py      # only after the corpus changes; uses out/cache/link, so 0 LLM calls
.venv/bin/uvicorn api.main:app --reload --port 8000
```

```bash
cd app/web && npm install && npm run dev  # http://localhost:3000, talks to http://localhost:8000
```

Checks: `.venv/bin/python tests/test_drawings.py && .venv/bin/python tests/test_gaps.py`.

## API

| | |
|---|---|
| `POST /ask` `{question, history, mode}` | `{job_id}`; runs `ask()` in a thread |
| `GET /ask/{job_id}/events` | SSE: `step` per tool call `{step, tool, args, summary}`, then `done` (full `ask()` result) or `error` |
| `DELETE /ask/{job_id}` | cancel (stops at the next tool call) |
| `GET /sheets`, `/sheets/{id}/svg`, `/sheets/{id}/overlay` | sheet list, corpus SVG, component boxes + status + CV layer |
| `GET /tools/{name}?…` | read tools (`Tools.dispatch`), write tools refused |
| `GET /source/{id}` | citation popovers |
| `GET /health` | Railway health check |

## Deploy

**API on Railway** (needs a long-running process: `ask()` takes 30–60 s)

1. railway.com → New Project → Deploy from GitHub repo → this repo. Leave Root Directory empty: `/railway.json` points Railway at `app/api/Dockerfile` (build context = repo root, so it can copy the corpus drawings).
2. Variables: `ASI1_API_KEY` (required). Optional: `ASI1_MODEL`, and `WEB_ORIGIN=https://<your-app>.vercel.app` to restrict CORS (default allows any origin).
3. Settings → Networking → Generate Domain. Check `https://<api>.up.railway.app/health` returns `{"ok": true, ...}`.

**Web on Vercel**

1. vercel.com → Add New → Project → import this repo.
2. Root Directory: `app/web` (framework auto-detects as Next.js).
3. Environment variable: `NEXT_PUBLIC_API_URL=https://<api>.up.railway.app` (no trailing slash). It is baked in at build time, so redeploy after changing it.
4. Deploy.

After a KB rebuild (`scripts/build_kb.py`), commit `out/kb.json` and push; Railway redeploys.

## Not in v1

Senior write forms and `/senior/*` endpoints (the toggle only sets `mode` on `/ask`), empty-state suggested questions, unit-wide gaps view, auth, Supabase, the `+` sheet picker (both sheets are tabs), `openapi-typescript` types (the API returns untyped backend dicts; `web/lib/api.ts` has hand-written types). Jobs live in memory: one API instance only.
