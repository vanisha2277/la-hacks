"""Flatten the backend into agentverse/hosted/ for the Agentverse hosted editor (one folder, imports by module name).
core/kb.py -> core_kb.py, agents/linker.py -> agents_linker.py, ... Paste every file in hosted/ into the editor.
Run: python agentverse/build_hosted.py"""
import re
import shutil
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "hosted"
MODULES = ["config.py", "core/checks.py", "core/gaps.py", "core/kb.py", "core/llm.py", "core/tags.py", "core/tools.py",
           "agents/conversation.py", "agents/linker.py", "agents/prompts.py"]


def flatten(src):
    src = re.sub(r"from (core|agents) import (\w+)", r"import \1_\2", src)  # from core import kb as kbm
    return re.sub(r"from (core|agents)\.(\w+) import", r"from \1_\2 import", src)


shutil.rmtree(OUT, ignore_errors=True)
OUT.mkdir()
for m in MODULES:
    (OUT / m.replace("/", "_")).write_text(flatten((APP / m).read_text()))
shutil.copy(Path(__file__).with_name("hosted_agent.py"), OUT / "agent.py")
print("\n".join(sorted(p.name for p in OUT.iterdir())))
