#!/usr/bin/env bash
# Prüft alle Komponenten der lokalen Videoproduktion. Ändert nichts.
set -u
cd "$(dirname "$0")/.."
COMFY_URL="${COMFYUI_URL:-http://127.0.0.1:8188}"
ok()   { printf "  \033[32m✔\033[0m %s\n" "$*"; }
warn() { printf "  \033[33m⚠\033[0m %s\n" "$*"; }
bad()  { printf "  \033[31m✖\033[0m %s\n" "$*"; }

echo "System"
for b in node npm python3 git; do
  command -v "$b" >/dev/null && ok "$b $($b --version 2>&1 | head -1)" || bad "$b fehlt"
done
node -e 'process.exit(+process.versions.node.split(".")[0] >= 22 ? 0 : 1)' 2>/dev/null || warn "Node < 22 (Hyperframes braucht ≥ 22)"
command -v ffmpeg >/dev/null && ok "ffmpeg" || bad "ffmpeg fehlt → brew install ffmpeg (Hyperframes, Review, MP3)"
command -v ffprobe >/dev/null && ok "ffprobe" || warn "ffprobe fehlt (Fallback: afinfo)"
WHISPER_MODEL="${VIDGEN_WHISPER_MODEL:-$HOME/.local/share/whisper-cpp/ggml-large-v3-turbo-q5_0.bin}"
if command -v whisper-cli >/dev/null && [ -f "$WHISPER_MODEL" ]; then ok "whisper-cli + Modell (Sprachprüfung)"
else warn "whisper-cli/Modell fehlt → Vollständigkeit der Sprachaufnahmen ungeprüft (siehe vidgen-setup)"; fi

VOICE_REF=$(python3 -c 'import json;print(json.load(open("templates/project/storyboard.json"))["voice"].get("reference") or "")' 2>/dev/null)
if [ -n "$VOICE_REF" ]; then
  VOICE_HOME="${VIDGEN_VOICES:-$HOME/.config/vidgen/voices}"
  if [ -f "$VOICE_REF" ] || [ -f "$VOICE_HOME/$(basename "$VOICE_REF")" ]; then ok "Standardstimme $(basename "$VOICE_REF")"
  else warn "Standardstimme $(basename "$VOICE_REF") fehlt → nach $VOICE_HOME/ kopieren (nicht im Repo)"; fi
fi

echo "ComfyUI"
if stats=$(curl -s -m 3 "$COMFY_URL/system_stats"); then
  ver=$(printf '%s' "$stats" | python3 -c 'import json,sys;print(json.load(sys.stdin)["system"]["comfyui_version"])' 2>/dev/null)
  [ -n "$ver" ] && ok "läuft auf $COMFY_URL (v$ver)" || bad "$COMFY_URL antwortet, aber nicht wie ComfyUI"
else
  bad "nicht erreichbar auf $COMFY_URL – ComfyUI starten"
fi
if command -v comfy >/dev/null; then
  ws=$(comfy --json which 2>/dev/null | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["workspace_path"])' 2>/dev/null)
  [ -d "$ws" ] && ok "comfy-cli → $ws" || bad "comfy-cli zeigt auf '$ws' (existiert nicht) → comfy set-default <pfad>"
else
  bad "comfy-cli fehlt → uv tool install comfy-cli"
fi
command -v comfy-mcp >/dev/null && ok "comfy-mcp installiert" || bad "comfy-mcp fehlt → scripts/setup.sh --mcp"

echo "Workflows (gegen laufendes ComfyUI)"
for f in comfy/workflows/*.json; do
  r=$(comfy --json workflow validate --workflow "$f" 2>/dev/null | python3 -c '
import json,sys
d=json.load(sys.stdin); x=d.get("data") or {}
if d.get("ok") and x.get("valid", True): print("ok")
else:
  e=(x.get("errors") or [{}])[0]; print(e.get("code","?")+": "+e.get("message","")[:90])' 2>/dev/null)
  name=$(basename "$f" .json)
  [ "$r" = "ok" ] && ok "$name" || warn "$name – ${r:-nicht prüfbar}"
done

echo "Skills"
for s in explainer story storyboard comfyui voiceover scene-coding video-review vidgen-setup; do
  [ -f ".claude/skills/$s/SKILL.md" ] || bad "eigener Skill fehlt: $s"
done
ok "eigene Skills vorhanden"
for s in remotion-best-practices hyperframes hyperframes-cli tesseract-video tesseract-motion; do
  if [ -d ".claude/skills/$s" ] || [ -d "$HOME/.claude/skills/$s" ]; then ok "Hersteller-Skill $s"
  else warn "Hersteller-Skill $s fehlt → scripts/setup.sh --skills"; fi
done
command -v tsrct >/dev/null && ok "tsrct (Tesseract CLI)" || warn "tsrct fehlt (nur für Tesseract nötig)"

echo "Video"
if [ -f video/storyboard.json ]; then
  python3 tools/storyboard.py show | head -1 | sed 's/^# /  /'
  [ -d video/remotion ] && { [ -d video/remotion/node_modules ] && ok "Remotion installiert" || warn "cd video/remotion && npm install"; }
else
  warn "noch nicht initialisiert → scripts/init.sh \"<Titel>\""
fi
git remote get-url template >/dev/null 2>&1 && ok "Template-Remote: $(git remote get-url template)" \
  || warn "kein Remote 'template' (Updates: git remote add template <url>)"
