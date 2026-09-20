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
LIVE_API_PATH = STORE_DIR / "live-api.jsonl"
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
        content = msg.get("content") or {}
        text = _text(content.get("parts") if isinstance(content, dict) else content).strip()
        if not text:
            continue
        messages.append({
            "role": str(author.get("role") or "unknown"),
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
        "source": "chatgpt-export",
    }

def _load_payloads(path: Path) -> list[list[dict]]:
    payloads: list[list[dict]] = []
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                base = Path(name).name.lower()
                if base != "conversations.json" and not re.fullmatch(r"conversations-?\d+\.json", base):
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
            if row:
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

def _redact(text: str) -> str:
    value = str(text or "")
    value = re.sub(r"(?i)(authorization\s*:\s*bearer\s+)[^\s]+", r"\1<redacted>", value)
    value = re.sub(
        r"(?i)\b(api[_ -]?key|token|password|passwd|secret|otp)\b\s*[:=]\s*[^\s]+",
        r"\1=<redacted>", value,
    )
    value = re.sub(r"\bsk-[A-Za-z0-9_-]{12,}\b", "<redacted-openai-key>", value)
    value = re.sub(
        r"-----BEGIN [^-]+ PRIVATE KEY-----.*?-----END [^-]+ PRIVATE KEY-----",
        "<redacted-private-key>", value, flags=re.S,
    )
    return value

def append_api_turn(
    user_text: str,
    assistant_text: str,
    response_id: str = "",
    session_id: str = "jarvis",
) -> dict:
    user = _redact(user_text).strip()
    assistant = _redact(assistant_text).strip()
    if not user and not assistant:
        return {"ok": False, "reason": "empty_turn"}
    now = datetime.now(timezone.utc).isoformat()
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    row = {
        "id": str(response_id or f"{session_id}-{datetime.now(timezone.utc).timestamp()}"),
        "title": (user[:100] or "JARVIS ChatGPT turn").replace("\n", " "),
        "create_time": now,
        "update_time": now,
        "source": "jarvis-openai-live",
        "session_id": str(session_id or "jarvis"),
        "messages": [
            {"role": "user", "text": user[:40000], "create_time": now},
            {"role": "assistant", "text": assistant[:40000], "create_time": now},
        ],
    }
    with LIVE_API_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {"ok": True, "id": row["id"]}
def _norm(text: str) -> list[str]:
    return re.findall(r"[\w@.+-]+", (text or "").lower(), flags=re.UNICODE)

def _iter_rows():
    for path in (INDEX_PATH, LIVE_API_PATH):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue

def search_history(query: str, limit: int = 6) -> list[dict]:
    terms = set(_norm(query))
    if not terms:
        return []
    scored = []
    for row in _iter_rows():
        title = str(row.get("title") or "")
        messages = row.get("messages") or []
        joined = "\n".join(str(m.get("text") or "") for m in messages)
        hay = set(_norm(title + " " + joined))
        overlap = len(terms & hay)
        if not overlap:
            continue
        recent = row.get("update_time") or row.get("create_time") or ""
        scored.append((overlap, recent, row))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    out = []
    for _, _, row in scored[: max(1, min(int(limit or 6), 20))]:
        snippets = []
        for message in row.get("messages") or []:
            text = str(message.get("text") or "")
            if any(term in text.lower() for term in terms):
                snippets.append({
                    "role": message.get("role"),
                    "text": text[:1200],
                    "create_time": message.get("create_time"),
                })
            if len(snippets) >= 3:
                break
        out.append({
            "id": row.get("id"),
            "title": row.get("title"),
            "create_time": row.get("create_time"),
            "update_time": row.get("update_time"),
            "source": row.get("source"),
            "snippets": snippets,
        })
    return out
def stats() -> dict:
    export_count = 0
    live_count = 0
    if INDEX_PATH.exists():
        export_count = sum(1 for line in INDEX_PATH.read_text(encoding="utf-8").splitlines() if line.strip())
    if LIVE_API_PATH.exists():
        live_count = sum(1 for line in LIVE_API_PATH.read_text(encoding="utf-8").splitlines() if line.strip())
    updated_at = ""
    source = ""
    if META_PATH.exists():
        try:
            meta = json.loads(META_PATH.read_text(encoding="utf-8"))
            updated_at = str(meta.get("updated_at") or "")
            source = str(meta.get("source") or "")
        except Exception:
            pass
    return {
        "indexed_conversations": export_count + live_count,
        "export_conversations": export_count,
        "live_api_turns": live_count,
        "updated_at": updated_at,
        "source": source,
    }