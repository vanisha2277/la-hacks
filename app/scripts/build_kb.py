"""Build-time pipeline: corpus -> ingest -> link -> gaps -> out/kb.json (-> docs).
Usage: python scripts/build_kb.py [--no-llm] [--docs]   (corpus path: CORPUS_DIR in .env)"""
import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents import linker
from core import gaps, kb as kbm
import config
from ingest import calendar, cv, drawings, drive, registers, revisions, slack


def build(use_llm=True):
    kb = kbm.empty()
    drawings.ingest(kb)
    revisions.ingest(kb)
    cv.ingest(kb)
    # Explicit files only. Never ingest facts_ledger.json, scenes.json or story.md (eval ground truth).
    registers.ingest(config.CORPUS_DIR, kb)
    slack.ingest(config.CORPUS_DIR, kb)
    drive.ingest(config.CORPUS_DIR, kb)
    calendar.ingest(config.CORPUS_DIR, kb)
    linker.link_rules(kb)
    if use_llm:
        print("llm linker:", linker.link_llm(kb))
    linker.tag_contexts(kb)
    kb["gaps"] = gaps.run(kb)
    return kb


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-llm", action="store_true", help="regex + alias linking only")
    ap.add_argument("--docs", action="store_true", help="also generate beginner docs (LLM)")
    a = ap.parse_args()
    kb = build(use_llm=not a.no_llm)
    kbm.save(kb)
    print(f"{len(kb['sheets'])} sheets, {len(kb['components'])} components, {len(kb['links'])} links, "
          f"{len(kb['revisions'])} revisions, {len(kb['records'])} records, {len(kb['sources'])} sources in {len(kb['contexts'])} contexts, {len(kb['mentions'])} mentions "
          f"({dict(Counter(m['by'] for m in kb['mentions']))}), {len(kb['gaps'])} gaps "
          f"({dict(Counter(g['severity'] for g in kb['gaps']))}) -> {kbm.KB_PATH}")
    for g in kb["gaps"]:
        print(f"  [{g['severity']:6}] {g['type']:22} {g['issue']}")
    if a.docs:
        from agents import docs_writer
        docs_writer.write_all(kbm.load())
