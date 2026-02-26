from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional during bootstrap
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent
if load_dotenv is not None:
    load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "stiftelseforum.db"
STIFTELSER_PATH = DATA_DIR / "stiftelser.json"
APP_TITLE = "Stiftelseforum MVP"
APP_SUBTITLE = "Inmatning → resultat → bonus för stiftelsen"
TOP_MATCH_COUNT = 3

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
OPENAI_REASONING_EFFORT = os.getenv("OPENAI_REASONING_EFFORT", "low")
OPENAI_WEB_MODEL = os.getenv("OPENAI_WEB_MODEL", "gpt-5.2")
ENABLE_OPENAI_BY_DEFAULT = os.getenv("ENABLE_OPENAI_BY_DEFAULT", "true").lower() == "true"
ENABLE_WEB_RESEARCH_BY_DEFAULT = os.getenv("ENABLE_WEB_RESEARCH_BY_DEFAULT", "false").lower() == "true"
