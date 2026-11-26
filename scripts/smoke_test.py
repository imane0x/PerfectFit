"""Run a few real queries end to end (needs Ollama, the model and an indexed catalog).

Usage: python scripts/smoke_test.py
"""
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
logging.basicConfig(level=logging.WARNING)

from src.assistant import get_assistant  # noqa: E402

a = get_assistant()
first = next(iter(a.catalog.products.values()))
img = a.catalog.image_path(first).read_bytes()
cases = [
    ("navy blue shirt for men", None),
    ("a women's watch, something silver", None),
    ("do you have a purple wedding dress with a long train?", None),
    ("any hoodies?", None),
    ("I need a sofa for my living room", None),
    ("I want something like this", img),
]
for text, image in cases:
    t = time.time()
    turn = a.ask(text, image)
    label = f"{text} [+image of: {first.title}]" if image else text
    print(f"\n> {label}  ({time.time() - t:.1f}s)")
    print("  filters:", turn.query.filters if turn.query else None)
    print("  answer:", turn.answer)
    print("  exact match:", turn.exact_match, "| products:", [p.title for p in turn.products])
