#!/bin/zsh
set -euo pipefail
cd /Users/tamizhtrader/jarvis
export JARVIS_BRIDGE_TOKEN="$(security find-generic-password -a "$USER" -s 'DarkFlowJarvis-ChatGPTBridgeToken' -w)"
exec /Users/tamizhtrader/jarvis/.venv/bin/python -m uvicorn bridge.chatgpt_bridge:app --host 127.0.0.1 --port 8765
