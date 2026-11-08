#!/usr/bin/env bash
# Macht aus einem frischen Klon des Templates ein eigenes Video-Repo.
#
#   git clone <template-url> mein-video && cd mein-video
#   scripts/init.sh "Wie DNS funktioniert" [--format 9:16] [--compositor hyperframes] [--duration 60]
#
# Optionen (zusätzlich zu denen von tools/init_video.py):
#   --keep-origin   origin NICHT in "template" umbenennen
#   --no-install    kein npm install für Remotion
#   --no-commit     nichts committen
set -euo pipefail
cd "$(dirname "$0")/.."

keep_origin=0; install=1; commit=1; args=()
for a in "$@"; do
  case "$a" in
    --keep-origin) keep_origin=1 ;;
    --no-install)  install=0 ;;
    --no-commit)   commit=0 ;;
    -h|--help)     sed -n 2,12p "$0"; exit 0 ;;
    *)             args+=("$a") ;;
  esac
done
[[ ${#args[@]} -ge 1 ]] || { sed -n 2,12p "$0"; exit 1; }

step() { printf "\n\033[1m▶ %s\033[0m\n" "$*"; }

step "Videoordner anlegen"
python3 tools/init_video.py "${args[@]}"

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

if [[ $install == 1 && -d video/remotion ]]; then
  step "Remotion-Abhängigkeiten (video/remotion)"
  (cd video/remotion && npm install --no-audit --no-fund --loglevel=error)
fi

step "Umgebung prüfen"
scripts/doctor.sh || true

cat <<'EOF'

Fertig. Jetzt Claude Code in diesem Ordner starten und z. B. sagen:
  /explainer Erklär Einsteigern in 60 Sekunden, wie DNS funktioniert.
EOF
