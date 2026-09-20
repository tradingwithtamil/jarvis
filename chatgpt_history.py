from __future__ import annotations

import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent
STORE_DIR = BASE / "data" / "chatgpt_history"
INDEX_PATH = STORE_DIR / "conversations.jsonl"
META_PATH = STORE_DIR / "meta.json"

def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(x for x in (_text(v) for v in value) if x)
    if isinstance(value, dict):
        if "text" in value:
            return _text(value.get("text"))
        if "parts" in value:
            return _text(value.get("parts"))
    return ""

def _iso(ts: Any) -> str:
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
    except Exception:
        return ""
def _conversation_row(conv: dict) -> dict | None:
    cid = str(conv.get("id") or conv.get("conversation_id") or "").strip()
    title = str(conv.get("title") or "Untitled").strip()
    mapping = conv.get("mapping") or {}
    messages = []
    for node in mapping.values() if isinstance(mapping, dict) else []:
        msg = node.get("message") if isinstance(node, dict) else None
        if not isinstance(msg, dict):
            continue
        author = msg.get("author") or {}
        role = str(author.get("role") or "").strip()
        content = msg.get("content") or {}
        text = _text(content.get("parts") if isinstance(content, dict) else content).strip()
        if not text:
            continue
        messages.append({
            "role": role or "unknown",
            "text": text,
            "create_time": _iso(msg.get("create_time")),
        })
    messages.sort(key=lambda m: m.get("create_time") or "")
    if not messages:
        return None
    return {
        "id": cid or f"untitled-{abs(hash((title, len(messages))))}",
        "title": title,
        "create_time": _iso(conv.get("create_time")),
        "update_time": _iso(conv.get("update_time")),
        "messages": messages,
    }

def _load_payloads(path: Path) -> list[list[dict]]:
    payloads: list[list[dict]] = []
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                base = Path(name).name.lower()
                if not (base == "conversations.json" or re.fullmatch(r"conversations-?\d+\.json", base)):
                    continue
                raw = json.loads(zf.read(name).decode("utf-8-sig"))
                if isinstance(raw, list):
                    payloads.append(raw)
    else:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(raw, list):
            payloads.append(raw)
    return payloads
def import_export(path: str | Path) -> dict:
    source = Path(path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(str(source))
    rows: dict[str, dict] = {}
    if INDEX_PATH.exists():
        for line in INDEX_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                rows[str(row["id"])] = row
            except Exception:
                pass
    imported = 0
    for payload in _load_payloads(source):
        for conv in payload:
            if not isinstance(conv, dict):
                continue
            row = _conversation_row(conv)
            if not row:
                continue
            rows[row["id"]] = row
            imported += 1
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    ordered = sorted(rows.values(), key=lambda r: r.get("update_time") or r.get("create_time") or "", reverse=True)
    INDEX_PATH.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in ordered) + ("\n" if ordered else ""), encoding="utf-8")
    meta = {
        "source": str(source),
        "indexed_conversations": len(ordered),
        "imported_rows": imported,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta

def _norm(s: str) -> list[str]:
    return re.findall(r"[\w@.+-]+", (s or "").lower(), flags=re.UNICODE)
def search_history(query: str, limit: int = 6) -> list[dict]:
    terms = set(_norm(query))
    if not terms or not INDEX_PATH.exists():
        return []
    scored = []
    for line in INDEX_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        title = str(row.get("title") or "")
        messages = row.get("messages") or []
        joined = "\n".join(str(m.get("text") or "") for m in messages)
        hay = set(_norm(title + " " + joined))
        overlap = len(terms & hay)
        if overlap == 0:
            continue
        recent = row.get("update_time") or row.get("create_time") or ""
        scored.append((overlap, recent, row))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    out = []
    for _, _, row in scored[: max(1, min(int(limit or 6), 20))]:
        messages = row.get("messages") or []
        snippets = []
        q = [t for t in terms if t]
        for m in messages:
            text = str(m.get("text") or "")
            low = text.lower()
            if any(t in low for t in q):
                snippets.append({"role": m.get("role"), "text": text[:1200], "create_time": m.get("create_time")})
            if len(snippets) >= 3:
                break
        out.append({
            "id": row.get("id"),
            "title": row.get("title"),
            "create_time": row.get("create_time"),
            "update_time": row.get("update_time"),
            "snippets": snippets,
        })
    return out

def stats() -> dict:
    if META_PATH.exists():
        try:
            return json.loads(META_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"indexed_conversations": 0, "updated_at": "", "source": ""}
