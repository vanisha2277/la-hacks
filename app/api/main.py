"""HTTP API over the backend. Thin wrappers, no business logic.
Run from app/:  .venv/bin/uvicorn api.main:app --reload --port 8000"""
import json
import os
import queue
import sys
import threading
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

import config
from agents.conversation import ask
from core import kb as kbm
from core.tools import WRITE, Tools

kb = kbm.load()
app = FastAPI(title="Handoff API")
# ponytail: open CORS, no auth (demo). Set WEB_ORIGIN to the Vercel URL to lock it down.
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("WEB_ORIGIN", "*").split(","), allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"ok": True, "components": len(kb["components"])}


# ---- ask: job + SSE ----
class AskBody(BaseModel):
    question: str
    history: list[dict] = []
    mode: str = "junior"


class Cancelled(Exception):
    pass


JOBS = {}  # job_id -> {"q": Queue, "cancel": Event}  # ponytail: in-memory, one process


def _summary(entry):
    r = entry["result"]
    if r.get("error"):
        return "error: " + r["error"]
    if r.get("empty"):
        return "nothing recorded"
    d = r.get("data")
    if entry["tool"] == "get_source" and isinstance(d, dict):
        return d.get("context_title") or d.get("title") or entry["args"].get("id", "")
    if entry["tool"] == "get_history" and isinstance(d, dict):
        return f"{len(d.get('events', []))} history events"
    if isinstance(d, list):
        return f"{len(d)} results"
    return f"{len(r.get('citations', []))} citations"


def _run(job, body):
    def on_step(entry):
        if job["cancel"].is_set():
            raise Cancelled
        job["q"].put(("step", {"step": entry["step"], "tool": entry["tool"], "args": entry["args"], "summary": _summary(entry)}))

    try:
        mode = "senior" if body.mode == "senior" else "junior"
        job["q"].put(("done", ask(body.question, history=body.history[-6:], mode=mode, kb=kb, on_step=on_step)))
    except Cancelled:
        job["q"].put(("error", {"message": "cancelled"}))
    except Exception as e:  # surface backend failures to the UI instead of hanging the stream
        job["q"].put(("error", {"message": str(e)}))


@app.post("/ask")
def start_ask(body: AskBody):
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = job = {"q": queue.Queue(), "cancel": threading.Event()}
    threading.Thread(target=_run, args=(job, body), daemon=True).start()
    return {"job_id": job_id}


@app.get("/ask/{job_id}/events")
def ask_events(job_id: str, request: Request):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "unknown job")

    def stream():  # sync generator: Starlette runs it in a thread pool
        while True:
            try:
                kind, data = job["q"].get(timeout=15)
            except queue.Empty:
                yield ": keepalive\n\n"
                continue
            yield f"event: {kind}\ndata: {json.dumps(data)}\n\n"
            if kind in ("done", "error"):
                JOBS.pop(job_id, None)
                return

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.delete("/ask/{job_id}")
def cancel_ask(job_id: str):
    if job_id in JOBS:
        JOBS[job_id]["cancel"].set()
    return {"ok": True}


# ---- sheets / drawing ----
@app.get("/sheets")
def sheets():
    return [{k: s.get(k) for k in ("id", "title", "rev", "rev_date", "page_size")} for s in kb["sheets"].values()]


def _sheet(sheet_id):
    s = kb["sheets"].get(sheet_id)
    if not s:
        raise HTTPException(404, "unknown sheet")
    return s


@app.get("/sheets/{sheet_id}/svg")
def sheet_svg(sheet_id: str):
    p = Path(_sheet(sheet_id)["svg"])
    if not p.exists():  # kb.json holds the build machine's absolute path; fall back to the corpus in this deploy
        p = config.CORPUS_DIR / "drawings" / p.name
    return FileResponse(p, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=3600"})


def status(tag):
    """Same rule as the reference app's drawing.status(): high gap > any gap or unverified link > ok."""
    gaps = [g for g in kb["gaps"] if tag in g["tags"]]
    if any(g["severity"] == "high" for g in gaps):
        return "high"
    inferred = any(tag in (l["from"], l["to"]) and l["status"] != "seen" for l in kb["links"])
    return "attention" if gaps or inferred else "ok"


@app.get("/sheets/{sheet_id}/overlay")
def sheet_overlay(sheet_id: str):
    _sheet(sheet_id)
    comps = [{"tag": t, "kind": c["kind"], "desc": c["desc"], "bbox": c["bbox"], "status": status(t),
              "legacy": kb["records"].get(t, {}).get("legacy")}
             for t, c in kb["components"].items() if c["sheet"] == sheet_id and c.get("bbox")]
    return {"components": comps, "cv": kb["cv"].get(sheet_id)}


# ---- tools / sources ----
@app.get("/tools/{name}")
def tool(name: str, request: Request):
    if name in WRITE:
        raise HTTPException(403, "write tools are not exposed here")
    args = dict(request.query_params)
    if "limit" in args:
        args["limit"] = int(args["limit"])
    try:
        return Tools(kb).dispatch(name, args)
    except (ValueError, TypeError, AttributeError) as e:
        raise HTTPException(400, str(e))


@app.get("/source/{sid:path}")
def source(sid: str):
    r = Tools(kb).get_source(sid)
    if r["empty"]:  # senior items aren't in get_source yet (BACKEND_INTEGRATION §4)
        hit = next((x for x in kb["notes"] + kb["corrections"] if x.get("id") == sid), None) \
            or next((g for g in kb["gaps"] if g["id"] == f"gap-{sid}"), None)
        if hit:
            return {"data": hit, "citations": [sid], "empty": False}
    return r
