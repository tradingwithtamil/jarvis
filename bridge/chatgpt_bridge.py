"""Authenticated HTTP bridge exposing Jarvis memory and skills to ChatGPT/custom tools."""
from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from memory.memory_manager import forget, memory_stats, remember, search_memory
from skills.skill_manager import get_skill, list_skills, search_skills

app = FastAPI(
    title="Jarvis ChatGPT Bridge",
    version="1.0.0",
    description="Private bridge for Jarvis long-term memory and reusable skills.",
)


def _auth(authorization: Optional[str] = Header(default=None)) -> None:
    token = os.getenv("JARVIS_BRIDGE_TOKEN", "").strip()
    if not token:
        raise HTTPException(status_code=503, detail="JARVIS_BRIDGE_TOKEN is not configured")
    if authorization != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="Unauthorized")


class MemorySearch(BaseModel):
    query: str = Field(min_length=1)
    category: str = ""
    limit: int = Field(default=8, ge=1, le=50)


class MemoryWrite(BaseModel):
    key: str = Field(min_length=1)
    value: str = Field(min_length=1)
    category: str = "notes"
    importance: int = Field(default=3, ge=1, le=5)
    tags: str = ""


class MemoryDelete(BaseModel):
    key: str = Field(min_length=1)
    category: str = "notes"


class SkillSearch(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=10)


@app.get("/health")
def health():
    return {"ok": True, "service": "jarvis-chatgpt-bridge", "version": "1.0.0"}


@app.get("/v1/memory/stats", dependencies=[Depends(_auth)])
def get_memory_stats():
    return memory_stats()


@app.post("/v1/memory/search", dependencies=[Depends(_auth)])
def find_memory(req: MemorySearch):
    return {"results": search_memory(req.query, req.limit, req.category)}


@app.post("/v1/memory/remember", dependencies=[Depends(_auth)])
def save_memory_item(req: MemoryWrite):
    result = remember(req.key, req.value, req.category, req.importance, req.tags)
    return {"ok": True, "result": result}


@app.post("/v1/memory/forget", dependencies=[Depends(_auth)])
def delete_memory_item(req: MemoryDelete):
    return {"result": forget(req.key, req.category)}


@app.get("/v1/skills", dependencies=[Depends(_auth)])
def get_skills():
    return {"skills": [{"name": s["name"], "description": s["description"], "keywords": s["keywords"]} for s in list_skills()]}


@app.post("/v1/skills/search", dependencies=[Depends(_auth)])
def find_skills(req: SkillSearch):
    skills = search_skills(req.query, req.limit)
    return {"skills": [{"name": s["name"], "description": s["description"], "keywords": s["keywords"]} for s in skills]}


@app.get("/v1/skills/{name}", dependencies=[Depends(_auth)])
def read_skill(name: str):
    skill = get_skill(name)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"name": skill["name"], "description": skill["description"], "keywords": skill["keywords"], "instructions": skill["body"]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("bridge.chatgpt_bridge:app", host="127.0.0.1", port=int(os.getenv("JARVIS_BRIDGE_PORT", "8787")))
