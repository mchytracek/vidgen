#!/usr/bin/env bash
# Einrichtung der lokalen Videoproduktion – einmal pro Rechner (nicht pro Video).
#   scripts/setup.sh            # alles (MCP, Hersteller-Skills, Prüfung)
#   scripts/setup.sh --mcp      # nur comfy-mcp installieren
#   scripts/setup.sh --skills   # nur Hersteller-Skills (Remotion, Hyperframes, Tesseract)
# Große Modell-Downloads und Custom Nodes werden NICHT automatisch installiert
# (siehe comfy/workflows/README.md bzw. Skill vidgen-setup).
set -euo pipefail
cd "$(dirname "$0")/.."
want="${1:-all}"

step() { printf "\n\033[1m▶ %s\033[0m\n" "$*"; }

if [[ "$want" == all || "$want" == --mcp ]]; then
  step "comfy-cli und comfy-mcp (Comfy-Org, lokaler MCP-Server)"
  command -v uv >/dev/null || { echo "uv fehlt: https://docs.astral.sh/uv/"; exit 1; }
  command -v comfy >/dev/null || uv tool install "comfy-cli>=1.14.0"
  command -v comfy-mcp >/dev/null || uv tool install comfy-mcp
  comfy-mcp --version || true
  if [[ -n "${COMFYUI_PATH:-}" ]]; then
    comfy set-default "$COMFYUI_PATH"
  fi
  echo "comfy-cli Workspace: $(comfy --json which | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["workspace_path"])')"
  echo "  (falsch? → COMFYUI_PATH=/pfad/zu/ComfyUI scripts/setup.sh --mcp)"
fi

if [[ "$want" == all || "$want" == --skills ]]; then
  step "Hersteller-Skills global (~/.claude/skills) – gelten für alle Video-Klone"
  npx -y skills add remotion-dev/skills --agent claude-code --global -y \
    --skill remotion-best-practices --skill remotion-render --skill remotion-multimedia \
    --skill remotion-captions --skill remotion-studio --skill remotion-license
  npx -y skills add heygen-com/hyperframes --agent claude-code --global -y \
    --skill hyperframes --skill hyperframes-cli --skill hyperframes-registry --skill media-use
  npx -y skills add mirage-hq/Tesseract --agent claude-code --global -y
  echo "Tesseract-CLI (tsrct): Installationsanleitung im Skill tesseract-video (references/installation.md)."
fi

if [[ "$want" == all ]]; then
  command -v ffmpeg >/dev/null || echo "Hinweis: ffmpeg fehlt → brew install ffmpeg"
  command -v whisper-cli >/dev/null || echo "Hinweis: whisper-cli fehlt → brew install whisper-cpp (+ Modell, siehe Skill vidgen-setup)"
  step "Prüfung"
  scripts/doctor.sh
  echo
  echo "Claude Code neu starten, damit MCP-Server und Skills geladen werden."
fi
