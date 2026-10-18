import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ASI1_API_KEY = os.getenv("ASI1_API_KEY", "")
ASI1_BASE_URL = "https://api.asi1.ai/v1"
AGENT_SEED_PHRASE = os.getenv("AGENT_SEED_PHRASE", "")
MODEL = os.getenv("ASI1_MODEL", "asi1")              # conversation, docs
MODEL_HEAVY = os.getenv("ASI1_MODEL_HEAVY", MODEL)   # bulk linking; flip to asi1-ultra for final runs

# Unit 200 corpus (teammate repo). Pinned: build warns if their HEAD moves.
CORPUS_DIR = Path(os.getenv("CORPUS_DIR", Path(__file__).resolve().parent.parent / "unit200_update" / "unit200_corpus"))
CORPUS_COMMIT = "26eced0e23f8562f25fb0cf3f6b7004f3013a07b"

# CV pipeline output folders (base.json + source.pdf). Shown as an overlay layer when the PDF matches a sheet.
CV_RUNS = [Path(p) for p in os.getenv("CV_RUNS", str(Path(__file__).resolve().parent / "kelly_run")).split(os.pathsep)]
