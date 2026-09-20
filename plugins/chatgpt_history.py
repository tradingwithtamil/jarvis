from chatgpt_history import search_history, stats

PLUGIN = {
    "name": "chatgpt_history",
    "description": "Search BOSS's imported ChatGPT archive plus live JARVIS OpenAI conversation history by topic, title, date or keyword. Read-only.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "search or stats"},
            "query": {"type": "STRING", "description": "What to find in prior ChatGPT conversations"},
            "limit": {"type": "INTEGER", "description": "1-20 results"},
        },
        "required": ["action"],
    },
}

def run(parameters, **kwargs):
    action = str(parameters.get("action") or "search").strip().lower()
    if action == "stats":
        s = stats()
        return f"ChatGPT history indexed conversations: {s.get('indexed_conversations',0)}. Last updated: {s.get('updated_at','never')}."
    query = str(parameters.get("query") or "").strip()
    if not query:
        return "ChatGPT history search needs a query."
    rows = search_history(query, int(parameters.get("limit") or 6))
    if not rows:
        return "No matching imported ChatGPT conversation found."
    lines = []
    for row in rows:
        lines.append(f"[{row.get('title')}] {row.get('update_time') or row.get('create_time') or ''}")
        for snip in row.get("snippets") or []:
            text = " ".join(str(snip.get("text") or "").split())
            if text:
                lines.append(f"  {snip.get('role','unknown')}: {text[:700]}")
    return "\n".join(lines)
