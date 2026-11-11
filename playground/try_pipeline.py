# %% Change the question, then run this cell. No Gmail, no reply sent.
# Kernel: pick the project .venv (Python 3.13), top right of the interactive window.
# Terminal alternative: uv run python playground/try_pipeline.py
import sys
from pathlib import Path

import nest_asyncio

ROOT = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path.cwd()
sys.path.append(str(ROOT))
nest_asyncio.apply()

from app.ai.decide import decide

question = "Hello, I ordered my debit card 12 business days ago and it has not arrived."
decision = decide(question)
print(decision.model_dump_json(indent=2))
