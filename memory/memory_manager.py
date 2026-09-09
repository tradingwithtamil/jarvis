import json
import re
import sys
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from threading import RLock


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
MEMORY_PATH = BASE_DIR / "memory" / "long_term.json"
_lock = RLock()
MAX_VALUE_LENGTH = 4000
MEMORY_MAX_CHARS = 2_000_000
PROMPT_MAX_CHARS = 12_000
_SESSION_MAX = 20
CATEGORIES = ("identity", "preferences", "projects", "relationships", "wishes", "notes")


def _empty_memory() -> dict:
    return {**{name: {} for name in CATEGORIES}, "sessions": []}


def load_memory() -> dict:
    if not MEMORY_PATH.exists():
        return _empty_memory()
    with _lock:
        try:
            data = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return _empty_memory()
            base = _empty_memory()
            for key, default in base.items():
                if key not in data:
                    data[key] = default
            return data
        except Exception as exc:
            print(f"[Memory] Load error: {exc}")
            return _empty_memory()


def _all_entries(memory: dict) -> list:
    entries = []
    for category in CATEGORIES:
        items = memory.get(category, {})
        if not isinstance(items, dict):
            continue
        for key, entry in items.items():
            if isinstance(entry, dict) and "value" in entry:
                entries.append((category, key, entry))
    return entries


def _trim_to_limit(memory: dict) -> dict:
    if len(json.dumps(memory, ensure_ascii=False)) <= MEMORY_MAX_CHARS:
        return memory
    entries = _all_entries(memory)
    entries.sort(key=lambda item: (int(item[2].get("importance", 3)), item[2].get("updated", "0000-00-00")))
    for category, key, _ in entries:
        if len(json.dumps(memory, ensure_ascii=False)) <= MEMORY_MAX_CHARS:
            break
        del memory[category][key]
    return memory


def save_memory(memory: dict) -> None:
    if not isinstance(memory, dict):
        return
    memory = _trim_to_limit(memory)
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        MEMORY_PATH.write_text(json.dumps(memory, indent=2, ensure_ascii=False), encoding="utf-8")


def _entry(value, importance=3, tags="") -> dict:
    text = str(value).strip()
    if len(text) > MAX_VALUE_LENGTH:
        text = text[:MAX_VALUE_LENGTH].rstrip() + "…"
    return {
        "value": text,
        "updated": datetime.now().strftime("%Y-%m-%d"),
        "importance": max(1, min(5, int(importance or 3))),
        "tags": str(tags or "").strip(),
    }


def update_memory(memory_update: dict) -> dict:
    if not isinstance(memory_update, dict) or not memory_update:
        return load_memory()
    memory = load_memory()
    changed = False
    for category, items in memory_update.items():
        if category not in CATEGORIES or not isinstance(items, dict):
            continue
        target = memory.setdefault(category, {})
        for key, raw in items.items():
            if isinstance(raw, dict) and "value" in raw:
                value = raw.get("value", "")
                importance = raw.get("importance", 3)
                tags = raw.get("tags", "")
            else:
                value, importance, tags = raw, 3, ""
            if value is None or not str(value).strip():
                continue
            new_entry = _entry(value, importance, tags)
            old = target.get(key, {})
            if not isinstance(old, dict) or old.get("value") != new_entry["value"] or old.get("tags", "") != new_entry["tags"]:
                target[key] = new_entry
                changed = True
    if changed:
        save_memory(memory)
    return memory


def remember(key: str, value: str, category: str = "notes", importance: int = 3, tags: str = "") -> str:
    if category not in CATEGORIES:
        category = "notes"
    update_memory({category: {key: {"value": value, "importance": importance, "tags": tags}}})
    return f"Remembered: {category}/{key}"


def forget(key: str, category: str = "notes") -> str:
    memory = load_memory()
    items = memory.get(category, {})
    if isinstance(items, dict) and key in items:
        del items[key]
        save_memory(memory)
        return f"Forgotten: {category}/{key}"
    return f"Not found: {category}/{key}"


forget_memory = forget


def _norm(text: str) -> str:
    return " ".join(re.findall(r"[\w@.+-]+", (text or "").lower(), flags=re.UNICODE))


def search_memory(query: str, limit: int = 8, category: str = "") -> list:
    q = _norm(query)
    if not q:
        return []
    q_terms = set(q.split())
    scored = []
    for cat, key, entry in _all_entries(load_memory()):
        if category and cat != category:
            continue
        value = str(entry.get("value", ""))
        tags = str(entry.get("tags", ""))
        haystack = _norm(f"{cat} {key} {value} {tags}")
        h_terms = set(haystack.split())
        overlap = len(q_terms & h_terms) / max(1, len(q_terms))
        fuzzy = SequenceMatcher(None, q, haystack[:1200]).ratio()
        importance = int(entry.get("importance", 3))
        score = overlap * 6 + fuzzy * 2 + importance * 0.25
        if overlap > 0 or fuzzy >= 0.18:
            scored.append((score, entry.get("updated", ""), cat, key, value, tags, importance))
    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return [
        {"category": cat, "key": key, "value": value, "tags": tags, "importance": importance, "updated": updated}
        for _, updated, cat, key, value, tags, importance in scored[: max(1, min(50, int(limit or 8)))]
    ]


def memory_stats() -> dict:
    memory = load_memory()
    return {
        "total_memories": len(_all_entries(memory)),
        "sessions": len(memory.get("sessions", [])) if isinstance(memory.get("sessions"), list) else 0,
        "by_category": {category: len(memory.get(category, {})) for category in CATEGORIES},
        "storage": str(MEMORY_PATH),
        "capacity_chars": MEMORY_MAX_CHARS,
    }


def format_memory_for_prompt(memory: dict) -> str:
    if not memory:
        return ""
    labels = {
        "identity": "Identity", "preferences": "Preferences", "projects": "Active Projects / Goals",
        "relationships": "People / Relationships", "wishes": "Plans / Wants", "notes": "Important Notes",
    }
    lines = [
        "[JARVIS LONG-TERM MEMORY — use naturally, never recite everything]",
        "For older/specific details not shown here, call jarvis_memory with action='recall'.",
    ]
    entries = _all_entries(memory)
    entries.sort(key=lambda item: (int(item[2].get("importance", 3)), item[2].get("updated", "")), reverse=True)
    grouped = {category: [] for category in CATEGORIES}
    for category, key, entry in entries:
        grouped[category].append((key, entry))
    for category in CATEGORIES:
        if not grouped[category]:
            continue
        lines.extend(["", labels[category] + ":"])
        for key, entry in grouped[category]:
            lines.append(f"  - {key.replace('_', ' ')}: {entry.get('value', '')}")
            if len("\n".join(lines)) >= PROMPT_MAX_CHARS:
                lines.append("  - [More available through jarvis_memory recall]")
                return "\n".join(lines)[:PROMPT_MAX_CHARS] + "\n"
    return "\n".join(lines)[:PROMPT_MAX_CHARS] + "\n"


def save_session_summary(summary: str, language: str = "") -> None:
    summary = (summary or "").strip()
    if not summary:
        return
    memory = load_memory()
    sessions = memory.get("sessions", [])
    if not isinstance(sessions, list):
        sessions = []
    sessions.append({"date": datetime.now().strftime("%Y-%m-%d"), "summary": summary[:1200], "language": language})
    memory["sessions"] = sessions[-_SESSION_MAX:]
    save_memory(memory)


def pop_last_session():
    with _lock:
        memory = load_memory()
        sessions = memory.get("sessions", [])
        if not isinstance(sessions, list) or not sessions:
            return None
        entry = sessions.pop()
        memory["sessions"] = sessions
        save_memory(memory)
        return entry
