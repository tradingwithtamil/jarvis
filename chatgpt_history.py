from __future__ import annotations

import json
import re
import unicodedata
import zipfile
from difflib import SequenceMatcher
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
_TAMIL_MAP = {
    "ஃப":"f","அ":"a","ஆ":"aa","இ":"i","ஈ":"i","உ":"u","ஊ":"u","எ":"e","ஏ":"e","ஐ":"ai","ஒ":"o","ஓ":"o","ஔ":"au",
    "க":"k","ங":"ng","ச":"s","ஞ":"ny","ட":"d","ண":"n","த":"th","ந":"n","ப":"p","ம":"m","ய":"y","ர":"r","ல":"l",
    "வ":"v","ழ":"zh","ள":"l","ற":"r","ன":"n","ஜ":"j","ஷ":"sh","ஸ":"s","ஹ":"h","ஃ":"",
    "ா":"a","ி":"i","ீ":"i","ு":"u","ூ":"u","ெ":"e","ே":"e","ை":"ai","ொ":"o","ோ":"o","ௌ":"au","்":"",
}
_TELUGU_MAP = {
    "అ":"a","ఆ":"aa","ఇ":"i","ఈ":"i","ఉ":"u","ఊ":"u","ఎ":"e","ఏ":"e","ఐ":"ai","ఒ":"o","ఓ":"o","ఔ":"au",
    "క":"k","ఖ":"kh","గ":"g","ఘ":"gh","ఙ":"ng","చ":"ch","ఛ":"ch","జ":"j","ఝ":"jh","ఞ":"ny",
    "ట":"t","ఠ":"th","డ":"d","ఢ":"dh","ణ":"n","త":"t","థ":"th","ద":"d","ధ":"dh","న":"n",
    "ప":"p","ఫ":"f","బ":"b","భ":"bh","మ":"m","య":"y","ర":"r","ల":"l","వ":"v","శ":"sh","ష":"sh","స":"s","హ":"h","ళ":"l",
    "ా":"a","ి":"i","ీ":"i","ు":"u","ూ":"u","ె":"e","ే":"e","ై":"ai","ొ":"o","ో":"o","ౌ":"au","్":"","ం":"n","ః":"h",
}

def _latinize(text: str) -> str:
    value = str(text or "")
    # Common Tamil loan-word digraphs first.
    value = value.replace("ஃப", "f")
    out = []
    for ch in value:
        if ch in _TAMIL_MAP:
            out.append(_TAMIL_MAP[ch])
        elif ch in _TELUGU_MAP:
            out.append(_TELUGU_MAP[ch])
        else:
            out.append(ch)
    value = "".join(out).lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    # Phonetic cleanup for English loan words as captured by Indic STT.
    value = value.replace("ph", "f").replace("pp", "p")
    value = re.sub(r"[^a-z0-9@.+-]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def _norm(text: str) -> list[str]:
    raw = re.findall(r"[\w@.+-]+", (text or "").lower(), flags=re.UNICODE)
    latin = re.findall(r"[a-z0-9@.+-]+", _latinize(text))
    return raw + [t for t in latin if t not in raw]

def _fuzzy_overlap(query_terms: set[str], hay_terms: set[str]) -> tuple[int, float]:
    matched = 0
    total = 0.0
    for q in query_terms:
        if len(q) < 3:
            continue
        best = 0.0
        for h in hay_terms:
            if len(h) < 3:
                continue
            ratio = SequenceMatcher(None, q, h).ratio()
            if ratio > best:
                best = ratio
        if best >= 0.72:
            matched += 1
            total += best
    return matched, total

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
    latin_terms = {t for t in _norm(_latinize(query)) if re.fullmatch(r"[a-z0-9@.+-]+", t)}
    compare_terms = latin_terms or {t for t in terms if re.fullmatch(r"[a-z0-9@.+-]+", t)}
    if not terms:
        return []
    scored = []
    for row in _iter_rows():
        title = str(row.get("title") or "")
        messages = row.get("messages") or []
        joined = "\n".join(str(m.get("text") or "") for m in messages)
        hay = set(_norm(title + " " + joined))
        hay_latin = {t for t in _norm(_latinize(title + " " + joined)) if re.fullmatch(r"[a-z0-9@.+-]+", t)}
        overlap = len(terms & hay)
        fuzzy_count, fuzzy_total = _fuzzy_overlap(compare_terms, hay_latin)
        if not overlap and not fuzzy_count:
            continue
        recent = row.get("update_time") or row.get("create_time") or ""
        score = overlap * 4.0 + fuzzy_count * 3.0 + fuzzy_total
        joined_low = joined.lower()
        # Do not let a previous failed history-search response outrank the
        # actual conversation the user is trying to recover.
        if "history" in joined_low and (
            "no matching" in joined_low
            or "matching-ah" in joined_low
            or "matching ah" in joined_low
        ):
            score -= 20.0
        if score <= 0:
            continue
        scored.append((score, recent, row))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    out = []
    for score, _, row in scored[: max(1, min(int(limit or 6), 20))]:
        snippets = []
        for message in row.get("messages") or []:
            text = str(message.get("text") or "")
            message_terms = set(_norm(_latinize(text)))
            exact_here = bool(terms & set(_norm(text)))
            fuzzy_here, _ = _fuzzy_overlap(compare_terms, message_terms)
            if exact_here or fuzzy_here:
                snippets.append({
                    "role": message.get("role"),
                    "text": text[:1200],
                    "create_time": message.get("create_time"),
                })
            if len(snippets) >= 3:
                break
        if snippets and not any(str(s.get("role") or "") == "assistant" for s in snippets):
            for message in row.get("messages") or []:
                if str(message.get("role") or "") == "assistant":
                    snippets.append({
                        "role": "assistant",
                        "text": str(message.get("text") or "")[:1200],
                        "create_time": message.get("create_time"),
                    })
                    break
        if not snippets:
            for message in (row.get("messages") or [])[:3]:
                snippets.append({
                    "role": message.get("role"),
                    "text": str(message.get("text") or "")[:1200],
                    "create_time": message.get("create_time"),
                })
        out.append({
            "id": row.get("id"),
            "title": row.get("title"),
            "create_time": row.get("create_time"),
            "update_time": row.get("update_time"),
            "source": row.get("source"),
            "match_score": round(float(score), 3),
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