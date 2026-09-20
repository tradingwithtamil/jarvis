#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from chatgpt_history import import_export

def candidates():
    downloads = Path.home() / "Downloads"
    pats = ["*chatgpt*.zip", "*openai*.zip", "*export*.zip", "conversations*.json"]
    found = []
    for pat in pats:
        found.extend(downloads.glob(pat))
    return sorted({p.resolve() for p in found if p.is_file()}, key=lambda p: p.stat().st_mtime, reverse=True)

def main():
    if len(sys.argv) > 1:
        src = Path(sys.argv[1]).expanduser()
    else:
        found = candidates()
        if not found:
            raise SystemExit("No ChatGPT export ZIP/JSON found in ~/Downloads.")
        src = found[0]
    result = import_export(src)
    print(f"Imported ChatGPT history: {result['indexed_conversations']} conversations indexed from {src}")

if __name__ == "__main__":
    main()
