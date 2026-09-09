#!/bin/zsh
set -euo pipefail
TS_DIR="$HOME/Library/Application Support/DarkFlowJarvis/Tailscale"
SOCK="$TS_DIR/tailscaled.sock"
STATE="$TS_DIR/tailscaled.state"
mkdir -p "$TS_DIR"
exec /opt/homebrew/bin/tailscaled \
  --tun=userspace-networking \
  --socket="$SOCK" \
  --state="$STATE" \
  --socks5-server=127.0.0.1:1055
