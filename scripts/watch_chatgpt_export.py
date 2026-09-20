#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from chatgpt_history import import_export
STATE = BASE / "data" / "chatgpt_history" / "watch-state.json"
DOWNLOADS = Path.home() / "Downloads"

def is_chatgpt_export(path: Path) -> bool:
    if path.suffix.lower() == ".json":
        return path.name.lower().startswith("conversations")
    if path.suffix.lower() != ".zip":
        return False
    try:
        with zipfile.ZipFile(path) as zf:
            names = {Path(n).name.lower() for n in zf.namelist()}
        return "conversations.json" in names or any(n.startswith("conversations-") and n.endswith(".json") for n in names)
    except Exception:
        return False

def main():
    candidates = [p for p in DOWNLOADS.glob("*") if p.is_file() and is_chatgpt_export(p)]
    if not candidates:
        return
    source = max(candidates, key=lambda p: p.stat().st_mtime)
    fingerprint = f"{source.resolve()}::{source.stat().st_size}::{source.stat().st_mtime_ns}"
    previous = {}
    if STATE.exists():
        try:
            previous = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            previous = {}
    if previous.get("fingerprint") == fingerprint:
        return
    result = import_export(source)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"fingerprint": fingerprint, "result": result}, indent=2), encoding="utf-8")
    print(f"ChatGPT history auto-imported: {result['indexed_conversations']} conversations")

if __name__ == "__main__":
    main()
