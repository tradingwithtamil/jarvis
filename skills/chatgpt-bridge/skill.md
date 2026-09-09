---
name: chatgpt-bridge
description: Share Jarvis memory and reusable operating procedures with ChatGPT through the private local bridge.
keywords: chatgpt, bridge, memory, skills, remote desktop, recall
---
# ChatGPT Bridge

1. Keep the bridge bound to `127.0.0.1:8765`; do not expose it publicly by default.
2. Store the bridge bearer token only in macOS Keychain under `DarkFlowJarvis-ChatGPTBridgeToken`.
3. ChatGPT reaches Jarvis through the already-authorized Remote Desktop Commander connection and `scripts/jarvis_chatgpt.py`.
4. Before asking BOSS to repeat prior project context, search Jarvis memory first.
5. Save stable preferences, project decisions, versions, blockers and outcomes; do not store passwords, tokens or secrets in memory.
6. Load the relevant Jarvis skill before complex audits, deployments, incidents or specialist-agent coordination.
7. Treat successful tool output as evidence; never claim a deploy, fix or connection is complete without verification.
