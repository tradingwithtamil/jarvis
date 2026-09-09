from skills.skill_manager import get_skill, list_skills, search_skills

PLUGIN = {
    "name": "jarvis_skills",
    "description": "Load Jarvis reusable operating procedures. Search for a relevant skill before complex multi-step work, audits, incidents, deployments or agent coordination.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "list, search, or get"},
            "query": {"type": "STRING"},
            "name": {"type": "STRING"},
            "limit": {"type": "INTEGER"},
        },
        "required": ["action"],
    },
}


def run(parameters, **kwargs):
    action = str(parameters.get("action", "list")).lower().strip()
    if action == "list":
        skills = list_skills()
        return "\n".join(f"{s['name']}: {s['description']}" for s in skills) or "No Jarvis skills installed."
    if action == "get":
        skill = get_skill(str(parameters.get("name", "") or ""))
        if not skill:
            return "Skill not found."
        return f"# {skill['name']}\n{skill['description']}\n\n{skill['body']}"
    query = str(parameters.get("query", "") or "").strip()
    skills = search_skills(query, int(parameters.get("limit", 5) or 5))
    return "\n".join(f"{s['name']}: {s['description']}" for s in skills) or "No matching skill found."
