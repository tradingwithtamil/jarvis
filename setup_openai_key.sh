#!/bin/zsh
set -euo pipefail

SERVICE='DarkFlowJarvis-OpenAIAPIKey'
ACCOUNT="$USER"
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$BASE_DIR/config/api_keys.json"

echo
echo 'JARVIS — ChatGPT Mode Setup'
echo 'OpenAI API billing/key is separate from ChatGPT Plus.'
echo 'Paste the API key below. It will be stored in macOS Keychain, not in GitHub.'
echo
read -s "OPENAI_KEY?OpenAI API key: "
echo

if [[ -z "${OPENAI_KEY:-}" ]]; then
  echo 'No key entered. Nothing changed.'
  read "?Press Enter to close..."
  exit 1
fi

TMP="$(mktemp)"
HTTP="$(curl -sS -o "$TMP" -w '%{http_code}' https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_KEY" || true)"
if [[ "$HTTP" != "200" ]]; then
  echo "Key validation failed (HTTP $HTTP)."
  python3 - "$TMP" <<'PY'
import json, sys
try:
    data=json.load(open(sys.argv[1]))
    print((data.get('error') or {}).get('message') or 'OpenAI rejected the key.')
except Exception:
    print('OpenAI rejected the key.')
PY
  rm -f "$TMP"
  unset OPENAI_KEY
  read "?Press Enter to close..."
  exit 1
fi
rm -f "$TMP"

security add-generic-password -U -a "$ACCOUNT" -s "$SERVICE" -w "$OPENAI_KEY" >/dev/null
unset OPENAI_KEY

python3 - "$CONFIG" <<'PY'
import json, sys
from pathlib import Path
p=Path(sys.argv[1])
try: data=json.loads(p.read_text())
except Exception: data={}
data['ai_provider']='chatgpt'
p.write_text(json.dumps(data, indent=4))
PY
echo 'OpenAI API key saved securely.'
echo 'AI provider set to ChatGPT.'

if launchctl print "gui/$UID/com.darkflow.jarvis" >/dev/null 2>&1; then
  launchctl kickstart -k "gui/$UID/com.darkflow.jarvis" >/dev/null 2>&1 || true
fi

echo 'JARVIS is restarting in ChatGPT mode.'
sleep 2
