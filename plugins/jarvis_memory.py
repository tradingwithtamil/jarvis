from memory.memory_manager import forget, memory_stats, remember, search_memory

PLUGIN = {
    "name": "jarvis_memory",
    "description": "Search, save, forget or inspect Jarvis long-term memory. Use recall when the user refers to prior decisions, settings, projects or earlier work.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "recall, remember, forget, or stats"},
            "query": {"type": "STRING", "description": "What to recall"},
            "category": {"type": "STRING", "description": "identity, preferences, projects, relationships, wishes, or notes"},
            "key": {"type": "STRING"},
            "value": {"type": "STRING"},
            "tags": {"type": "STRING"},
            "importance": {"type": "INTEGER", "description": "1-5; 5 is critical"},
            "limit": {"type": "INTEGER"},
        },
        "required": ["action"],
    },
}


def run(parameters, **kwargs):
    action = str(parameters.get("action", "recall")).lower().strip()
    category = str(parameters.get("category", "") or "").strip().lower()
    if action == "stats":
        return str(memory_stats())
    if action == "remember":
        key = str(parameters.get("key", "") or "").strip()
        value = str(parameters.get("value", "") or "").strip()
        if not key or not value:
            return "Memory save needs both key and value."
        return remember(key, value, category or "notes", int(parameters.get("importance", 3) or 3), str(parameters.get("tags", "") or ""))
    if action == "forget":
        key = str(parameters.get("key", "") or "").strip()
        if not key:
            return "Memory forget needs a key."
        return forget(key, category or "notes")
    query = str(parameters.get("query", "") or "").strip()
    if not query:
        return "Memory recall needs a query."
    rows = search_memory(query, int(parameters.get("limit", 8) or 8), category)
    if not rows:
        return "No matching Jarvis memory found."
    return "\n".join(
        f"[{row['category']}/{row['key']}] {row['value']} (updated {row['updated']}, importance {row['importance']})"
        for row in rows
    )
