#!/usr/bin/env python3
"""Local CLI used by ChatGPT/Remote Desktop Commander to access Jarvis safely."""
from __future__ import annotations
import json, os, subprocess, sys, urllib.error, urllib.request
BASE = os.getenv("JARVIS_BRIDGE_URL", "http://127.0.0.1:8765")

def token() -> str:
    env = os.getenv("JARVIS_BRIDGE_TOKEN", "").strip()
    if env:
        return env
    return subprocess.check_output([
        "security", "find-generic-password", "-a", os.getenv("USER", ""),
        "-s", "DarkFlowJarvis-ChatGPTBridgeToken", "-w"
    ], text=True).strip()

def request(method: str, path: str, payload=None, auth=True):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if auth:
        headers["Authorization"] = f"Bearer {token()}"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code}: {e.read().decode()}")

def main(argv: list[str]) -> None:
    if not argv or argv[0] in {"help", "-h", "--help"}:
        print("health | stats | recall <query> | remember <category> <key> <value> | forget <category> <key> | skills | skill-search <query> | skill <name>")
        return
    cmd = argv[0]
    if cmd == "health": out = request("GET", "/health", auth=False)
    elif cmd == "stats": out = request("GET", "/v1/memory/stats")
    elif cmd == "recall": out = request("POST", "/v1/memory/search", {"query": " ".join(argv[1:]), "limit": 8})
    elif cmd == "remember": out = request("POST", "/v1/memory/remember", {"category": argv[1], "key": argv[2], "value": " ".join(argv[3:]), "importance": 4})
    elif cmd == "forget": out = request("POST", "/v1/memory/forget", {"category": argv[1], "key": argv[2]})
    elif cmd == "skills": out = request("GET", "/v1/skills")
    elif cmd == "skill-search": out = request("POST", "/v1/skills/search", {"query": " ".join(argv[1:]), "limit": 5})
    elif cmd == "skill": out = request("GET", f"/v1/skills/{argv[1]}")
    else: raise SystemExit(f"Unknown command: {cmd}")
    print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main(sys.argv[1:])
