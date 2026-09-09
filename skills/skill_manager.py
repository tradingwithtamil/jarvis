from __future__ import annotations

import re
import sys
from pathlib import Path


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


SKILLS_DIR = get_base_dir() / "skills"


def _parse_skill(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    meta = {"name": path.parent.name, "description": "", "keywords": []}
    body = text
    if text.startswith("---\n"):
        _, front, body = text.split("---\n", 2)
        for line in front.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key, value = key.strip().lower(), value.strip()
            if key == "keywords":
                meta[key] = [item.strip().lower() for item in value.split(",") if item.strip()]
            elif key in {"name", "description"}:
                meta[key] = value
    meta["body"] = body.strip()
    meta["path"] = str(path)
    return meta


def list_skills() -> list:
    skills = []
    if not SKILLS_DIR.exists():
        return skills
    for path in sorted(SKILLS_DIR.glob("*/skill.md")):
        try:
            skills.append(_parse_skill(path))
        except Exception:
            continue
    return skills


def get_skill(name: str):
    wanted = (name or "").strip().lower()
    for skill in list_skills():
        if skill["name"].lower() == wanted or Path(skill["path"]).parent.name.lower() == wanted:
            return skill
    return None


def search_skills(query: str, limit: int = 5) -> list:
    terms = set(re.findall(r"[\w-]+", (query or "").lower()))
    scored = []
    for skill in list_skills():
        hay = " ".join([skill["name"], skill["description"], " ".join(skill["keywords"]), skill["body"][:1800]]).lower()
        score = sum(3 for term in terms if term in skill["keywords"]) + sum(1 for term in terms if term in hay)
        if score:
            scored.append((score, skill))
    scored.sort(key=lambda item: (item[0], item[1]["name"]), reverse=True)
    return [skill for _, skill in scored[: max(1, min(10, int(limit or 5)))]]


def format_skill_index_for_prompt(max_chars: int = 3000) -> str:
    skills = list_skills()
    if not skills:
        return ""
    lines = [
        "[JARVIS SKILLS]",
        "Reusable operating procedures are available through jarvis_skills. Use the relevant skill before complex work.",
    ]
    for skill in skills:
        lines.append(f"- {skill['name']}: {skill['description']}")
    return "\n".join(lines)[:max_chars] + "\n"
