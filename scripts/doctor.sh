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
  [ -d ".claude/skills/$s" ] && ok "Hersteller-Skill $s" || warn "Hersteller-Skill $s fehlt → scripts/setup.sh --skills"
done
command -v tsrct >/dev/null && ok "tsrct (Tesseract CLI)" || warn "tsrct fehlt (nur für Tesseract nötig)"

echo "Projekte"
python3 tools/storyboard.py list | sed 's/^/  /'
