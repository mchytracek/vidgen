#!/usr/bin/env bash
# Macht aus einem frischen Klon des Templates ein eigenes Video-Repo.
#
#   git clone https://github.com/mchytracek/vidgen.git mein-video && cd mein-video
#   scripts/init.sh "Wie DNS funktioniert" [--format 9:16] [--compositor hyperframes] [--duration 60]
#
# Optionen (zusätzlich zu denen von tools/init_video.py):
#   --keep-origin   origin NICHT in "template" umbenennen
#   --no-install    kein npm install für Remotion
#   --no-commit     nichts committen
#   --comfy-url URL ComfyUI-Server, z. B. http://gpu-box:8188 (Default: lokal 127.0.0.1:8188).
#                   Ohne Option wird interaktiv gefragt; Vorschlag = zuletzt gewählte Adresse.
#                   Gespeichert in .vidgen.env (git-ignoriert) und ~/.config/vidgen/env.
set -euo pipefail
cd "$(dirname "$0")/.."

keep_origin=0; install=1; commit=1; comfy_url=""; args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep-origin) keep_origin=1 ;;
    --no-install)  install=0 ;;
    --no-commit)   commit=0 ;;
    --comfy-url)   comfy_url="${2:?--comfy-url braucht eine URL}"; shift ;;
    --comfy-url=*) comfy_url="${1#*=}" ;;
    -h|--help)     sed -n 2,15p "$0"; exit 0 ;;
    *)             args+=("$1") ;;
  esac
  shift
done
[[ ${#args[@]} -ge 1 ]] || { sed -n 2,15p "$0"; exit 1; }

step() { printf "\n\033[1m▶ %s\033[0m\n" "$*"; }

[[ -d video ]] && { echo "✖ video/ existiert bereits – dieses Repo ist schon initialisiert"; exit 1; }

step "ComfyUI-Server"
config_home="${VIDGEN_CONFIG:-$HOME/.config/vidgen}"
suggest=$(python3 tools/_common.py comfy-url)   # $COMFYUI_URL / .vidgen.env / letzte Wahl / lokal
if [[ -z "$comfy_url" ]]; then
  if [[ -t 0 ]]; then
    read -r -p "  ComfyUI-URL [$suggest]: " comfy_url || true
  else
    echo "  (nicht interaktiv – nutze $suggest; ändern mit --comfy-url)"
  fi
fi
comfy_url="${comfy_url:-$suggest}"
[[ "$comfy_url" == *://* ]] || comfy_url="http://$comfy_url"
comfy_url="${comfy_url%/}"
if [[ "$comfy_url" != http://* ]] || [[ "${comfy_url#http://}" == */* ]]; then
  echo "  ✖ Nur http://host:port ohne Pfad wird unterstützt (comfy-cli/comfy-mcp): $comfy_url"; exit 1
fi
printf '# ComfyUI-Server dieses Video-Repos (von scripts/init.sh, git-ignoriert)\nCOMFYUI_URL=%s\n' "$comfy_url" > .vidgen.env
mkdir -p "$config_home"
printf '# Vorschlag für scripts/init.sh (zuletzt gewählter ComfyUI-Server)\nCOMFYUI_URL=%s\n' "$comfy_url" > "$config_home/env"
if curl -s -m 5 "$comfy_url/system_stats" | grep -q comfyui_version; then
  echo "  ✔ $comfy_url erreichbar"
else
  echo "  ⚠ $comfy_url antwortet nicht – läuft ComfyUI dort mit --listen? (später: scripts/doctor.sh)"
fi

step "Videoordner anlegen"
python3 tools/init_video.py "${args[@]}"

if [[ $install == 1 && -d video/remotion ]]; then
  step "Remotion-Abhängigkeiten (video/remotion)"
  (cd video/remotion && npm install --no-audit --no-fund --loglevel=error)
fi

if git rev-parse --git-dir >/dev/null 2>&1; then
  if [[ $keep_origin == 0 ]] && git remote get-url origin >/dev/null 2>&1 \
     && ! git remote get-url template >/dev/null 2>&1; then
    step "Git: origin → template (für spätere Template-Updates)"
    git remote rename origin template
    echo "  Template-Updates holen:   scripts/update-template.sh"
    echo "  Eigenes Remote anlegen:   git remote add origin <url> && git push -u origin HEAD"
  fi
  if [[ $commit == 1 ]]; then
    title=$(python3 -c 'import json;print(json.load(open("video/storyboard.json"))["title"])')
    git add video
    git commit -q -m "Video initialisiert: $title" && echo "  ✔ commit: Video initialisiert: $title"
  fi
fi

step "Umgebung prüfen"
scripts/doctor.sh || true

cat <<'EOF'

Fertig. Jetzt Claude Code in diesem Ordner starten und z. B. sagen:
  /explainer Erklär Einsteigern in 60 Sekunden, wie DNS funktioniert.
EOF
