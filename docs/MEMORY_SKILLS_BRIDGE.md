# Jarvis Strong Memory + Skills + ChatGPT Bridge

## What changed

- Long-term memory capacity increased from 2,200 chars to 2,000,000 chars.
- Individual memory values increased from 380 to 4,000 chars.
- Recent session history increased from 3 to 20 entries.
- `jarvis_memory` plugin adds recall/search, remember, forget and stats actions.
- `jarvis_skills` plugin adds reusable SOP discovery and loading.
- Four starter skills ship in `skills/`: CEO orchestration, production audit, safe deployment and incident recovery.
- `bridge/chatgpt_bridge.py` exposes authenticated memory/skill endpoints for ChatGPT/custom tools.

## Run the bridge

Use the same Python environment that runs Jarvis:

```bash
export JARVIS_BRIDGE_TOKEN='use-a-long-random-secret'
python -m bridge.chatgpt_bridge
```

Default bind: `127.0.0.1:8787`.

## Security

All `/v1/*` routes require `Authorization: Bearer <JARVIS_BRIDGE_TOKEN>`.
The `/health` endpoint is intentionally public and contains no memory data.
Do not expose the bridge publicly without HTTPS and access control.

## ChatGPT connection

For a persistent ChatGPT connection, expose this bridge through a stable private HTTPS endpoint, then register that endpoint as the Jarvis custom integration/plugin. The OpenAPI schema is available at `/openapi.json`.
