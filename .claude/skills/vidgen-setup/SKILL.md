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
| ComfyUI-Adresse | `python3 tools/_common.py comfy-url` | `scripts/init.sh --comfy-url …` bzw. `COMFYUI_URL=…` in `.vidgen.env` |
| ComfyUI läuft | `curl -s "$(python3 tools/_common.py comfy-url)/system_stats"` | lokal: User startet ComfyUI (`python main.py`); remote: dort `python main.py --listen 0.0.0.0` |
| comfy-cli zeigt auf richtige Installation (nur lokal) | `comfy --json which` | `comfy set-default <pfad-zu-ComfyUI>` |
| comfy-mcp | `command -v comfy-mcp` | `uv tool install comfy-mcp`, dann Claude Code neu starten |
| FFmpeg/ffprobe | `command -v ffmpeg` | `brew install ffmpeg` |
| Whisper (Sprachprüfung) | `command -v whisper-cli` + Modell `~/.local/share/whisper-cpp/ggml-large-v3-turbo-q5_0.bin` | `brew install whisper-cpp`; Modell (≈ 574 MB) von `huggingface.co/ggerganov/whisper.cpp` (`resolve/main/ggml-large-v3-turbo-q5_0.bin`) laden; anderer Pfad über `VIDGEN_WHISPER_MODEL` |
| Node ≥ 22 | `node --version` | – |
| Hersteller-Skills | `ls .claude/skills` | `scripts/setup.sh --skills` |
| ChatterBox (TTS) | `scripts/doctor.sh` (Abschnitt Workflows; nutzt `comfy validate --input <object_info>`) | MCP `install_node` / ComfyUI-Manager: *ComfyUI_Fill-ChatterBox* |
| ACE-Step (Musik) | dito mit `audio_ace_step1_5_xl_turbo.json` | Modelle per MCP `download_model` (siehe `comfy/workflows/README.md`) |

Installationen und Modell-Downloads **immer erst nach Zustimmung** – Größe nennen
(LTX-/ACE-Modelle sind mehrere GB). Nach Änderungen an `.mcp.json`, `.vidgen.env` oder
neuen Skills muss Claude Code neu gestartet werden (comfy-mcp liest die Adresse beim Start).

**Entfernter ComfyUI-Server:** Modelle und Custom Nodes müssen auf *dem Server*
installiert sein – `download_model`/`install_node` aus dieser Sitzung wirken lokal.
Server-Checkliste: ComfyUI mit `--listen 0.0.0.0` (oder hinter VPN/SSH-Tunnel),
Port 8188 erreichbar, Workflows aus `comfy/workflows/` validieren
(`scripts/doctor.sh` macht das gegen den konfigurierten Server).

## macOS-Hinweis

comfy-mcp und ComfyUI dürfen nicht auf `~/Documents`, `~/Desktop`, `~/Downloads`
zugreifen, ohne dass das startende Programm Festplattenzugriff hat. ComfyUI liegt
deshalb in `~/Applications/ComfyUI`; Dateien gelangen per `upload_file` /
`comfy upload` in dessen `input/`.
