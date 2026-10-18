"""Planted contradictions/gaps must surface, and nothing else may be flagged as a value conflict.
Needs a built KB: .venv/bin/python scripts/build_kb.py && .venv/bin/python tests/test_gaps.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import gaps, kb as kbm

kb = kbm.load()
g = gaps.run(kb)
conflicts = {x["tags"][0]: x for x in g if x["type"] == "value_conflict"}
assert set(conflicts) == {"20LFC10AA191", "20LFC20AA102"}, conflicts  # C01, C02 only
assert "16.5" in conflicts["20LFC10AA191"]["issue"] and "17.2" in conflicts["20LFC10AA191"]["issue"]
assert "FO" in conflicts["20LFC20AA102"]["issue"] and conflicts["20LFC20AA102"]["severity"] == "high"
assert any(x["type"] == "undocumented" and x["tags"] == ["20LFB10AP002"] for x in g)  # G01
assert not [x for x in g if x["type"] in ("incomplete_loop", "change_not_reflected")], "none planted"
print(f"gaps ok: {len(g)} gaps, conflicts {sorted(conflicts)}")
