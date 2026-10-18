"""Make the flat bot modules (bot/*.py) importable as top-level modules,
exactly as the Arena loader sees them."""

import sys
from pathlib import Path

BOT_DIR = Path(__file__).resolve().parent.parent / "bot"
sys.path.insert(0, str(BOT_DIR))
