"""Documentation agent: code assembles a fact pack with read tools, the LLM writes, the checker verifies."""
import json
from concurrent.futures import ThreadPoolExecutor

from agents.prompts import DOCS_PROMPT
from core import kb as kbm
from core.checks import check_citations
from core.gaps import EQUIPMENT_KINDS
from core.llm import chat
from core.tools import Tools

DOCS_DIR = kbm.ROOT / "out" / "docs"


def fact_pack(kb, tag):
    t = Tools(kb)
    calls = [("get_component", {"tag": tag}), ("get_neighbors", {"tag": tag}), ("get_protection", {"tag": tag}),
             ("get_history", {"tag": tag}), ("get_notes", {"tag": tag}), ("get_gaps", {"tag": tag}),
             ("search_sources", {"query": kb["components"][tag]["desc"], "tag": tag, "limit": 8})]
    measuring = {l["from"] for l in kb["links"] if l["to"] == tag and l["relation"] == "measures"}
    calls += [("get_loop", {"tag": m}) for m in sorted(measuring)]
    pack = [{"tool": n, "args": a, "result": t.dispatch(n, a)} for n, a in calls]
    return pack, {c for p in pack for c in p["result"]["citations"]}


def write_page(kb, tag):
    pack, allowed = fact_pack(kb, tag)
    subject = f"{tag} ({kb['components'][tag]['desc']})"
    md = chat([{"role": "user", "content": DOCS_PROMPT.format(subject=subject, facts=json.dumps(pack))}]).content or ""
    check = check_citations(md, allowed)
    status = "PASS" if check["ok"] else "FAIL, unverified IDs: " + ", ".join(check["unknown"])
    md = md.strip() + f"\n\n---\n*Generated from the knowledge base. Citation check: {status}.*\n"
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / f"{tag}.md").write_text(md)
    return tag, status


def write_all(kb, tags=None):
    tags = tags or [t for t, c in kb["components"].items() if c["kind"] in EQUIPMENT_KINDS]
    with ThreadPoolExecutor(4) as ex:
        for tag, status in ex.map(lambda t: write_page(kb, t), tags):
            print(f"  docs {tag}: {status}")
