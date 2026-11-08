---
name: vidgen-setup
description: Richtet die lokale Videoproduktion ein und diagnostiziert sie – ComfyUI-Verbindung, comfy-mcp, Modelle, Custom Nodes, FFmpeg, Node, Remotion/Hyperframes/Tesseract-Skills. Verwenden bei Ersteinrichtung, wenn Werkzeuge fehlen oder ComfyUI/MCP nicht reagiert.
---

# Setup & Diagnose

1. `scripts/doctor.sh` ausführen und Ausgabe lesen – zeigt für jede Komponente ✅/⚠️/❌.
2. Fehlende Teile mit dem User klären, dann `scripts/setup.sh` (oder einzelne Schritte daraus).

## Komponenten

| Komponente | Prüfen | Einrichten |
|------------|--------|-----------|
| ComfyUI läuft | `curl -s 127.0.0.1:8188/system_stats` | User startet ComfyUI (`python main.py` im ComfyUI-Ordner) |
| comfy-cli zeigt auf richtige Installation | `comfy --json which` | `comfy set-default <pfad-zu-ComfyUI>` |
| comfy-mcp | `command -v comfy-mcp` | `uv tool install comfy-mcp`, dann Claude Code neu starten |
| FFmpeg/ffprobe | `command -v ffmpeg` | `brew install ffmpeg` |
| Node ≥ 22 | `node --version` | – |
| Hersteller-Skills | `ls .claude/skills` | `scripts/setup.sh --skills` |
| ChatterBox (TTS) | `comfy --json workflow validate --workflow comfy/workflows/audio-chatterbox_tts_multilingual.json` | MCP `install_node` / ComfyUI-Manager: *ComfyUI_Fill-ChatterBox* |
| ACE-Step (Musik) | dito mit `audio_ace_step1_5_xl_turbo.json` | Modelle per MCP `download_model` (siehe `comfy/workflows/README.md`) |

Installationen und Modell-Downloads **immer erst nach Zustimmung** – Größe nennen
(LTX-/ACE-Modelle sind mehrere GB). Nach Änderungen an `.mcp.json` oder neuen
Skills muss Claude Code neu gestartet werden.

## macOS-Hinweis

comfy-mcp und ComfyUI dürfen nicht auf `~/Documents`, `~/Desktop`, `~/Downloads`
zugreifen, ohne dass das startende Programm Festplattenzugriff hat. ComfyUI liegt
deshalb in `~/Applications/ComfyUI`; Dateien gelangen per `upload_file` /
`comfy upload` in dessen `input/`.
