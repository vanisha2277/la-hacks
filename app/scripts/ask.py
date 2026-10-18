"""CLI: python scripts/ask.py "Why does V-200 have two level transmitters?" [--senior] [--json]"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents.conversation import ask, format_text

ap = argparse.ArgumentParser()
ap.add_argument("question")
ap.add_argument("--senior", action="store_true")
ap.add_argument("--json", action="store_true")
a = ap.parse_args()
r = ask(a.question, mode="senior" if a.senior else "junior")
print(json.dumps(r, indent=1) if a.json else format_text(r))
