#!/usr/bin/env bash
# Startet comfy-mcp mit der ComfyUI-Adresse dieses Repos (eingetragen in .mcp.json).
# Adresse: $COMFYUI_URL > .vidgen.env > ~/.config/vidgen/env > http://127.0.0.1:8188
# Bei der lokalen Standardadresse bleibt die Umgebung unverändert (comfy-mcp-Default).
set -euo pipefail
cd "$(dirname "$0")/.."
url=$(python3 tools/_common.py comfy-url 2>/dev/null || echo "http://127.0.0.1:8188")
if [[ "$url" != "http://127.0.0.1:8188" ]]; then
  export COMFYUI_URL="$url" COMFY_LOCAL_URL="$url"
fi
exec comfy-mcp "$@"
