# vidgen – Erklärvideos lokal mit Claude Code + ComfyUI

Claude Code entwickelt die Story, plant das Storyboard, lässt Bilder, Clips,
Stimme und Musik im **lokalen ComfyUI** erzeugen (über den MCP-Server
[`comfy-mcp`](https://github.com/Comfy-Org/comfy-mcp)) und programmiert die Szenen
mit **Remotion**, **Hyperframes** oder **Tesseract** – bis zum fertigen MP4.
Keine Cloud-GPU, keine Kosten pro Render.

```
Briefing ─▶ Story ─▶ Storyboard ─▶ Stimme ─▶ ComfyUI-Assets ─▶ Szenen-Code ─▶ Review ─▶ MP4
  (Claude)   (Claude)  storyboard.json  ChatterBox   Z-Image / LTX-2.3    Remotion /       Kontakt-
                        = Datenvertrag   (ComfyUI)   ACE-Step (ComfyUI)   Hyperframes /    bögen,
                                                                           Tesseract        LUFS
```

## Schnellstart

```bash
scripts/setup.sh      # comfy-mcp + Hersteller-Skills installieren, danach Prüfung
```

```bash
scripts/doctor.sh     # jederzeit: was läuft, was fehlt
```

Dann Claude Code im Repo starten und z. B. sagen:

> /explainer Mach ein 60-Sekunden-Video, das Einsteigern erklärt, wie DNS funktioniert.

Claude fragt Briefing-Details ab, zeigt Story und Storyboard zur Freigabe, erzeugt
die Assets und rendert nach `projects/<slug>/renders/final.mp4`.

## Voraussetzungen

| Komponente | Zweck |
|------------|-------|
| ComfyUI (lokal, Port 8188) | Bild/Video/Audio-Generierung |
| `comfy-cli` + `comfy-mcp` | Steuerung von ComfyUI durch Claude (MCP) und Skripte |
| Modelle: Z-Image Turbo, LTX-2.3 | Bilder, Clips (✅ vorhanden) |
| Custom Node *ComfyUI_Fill-ChatterBox* | deutsche Stimme mit Voice-Cloning (optional; Fallback macOS `say`) |
| ACE-Step 1.5 Modelle | Hintergrundmusik (optional) |
| Node ≥ 22, FFmpeg | Remotion/Hyperframes-Render, Review |

## Aufbau

```
CLAUDE.md                 Regeln & Pipeline für Claude
.mcp.json                 MCP-Server comfy-mcp
.claude/skills/           eigene Skills (s. u.) + Hersteller-Skills (via setup.sh)
comfy/workflows/          geprüfte ComfyUI-Workflows + Slot-Referenz (README.md)
schemas/                  storyboard.schema.json – Datenvertrag aller Phasen
templates/project/        Projektvorlage inkl. Remotion-Gerüst (rendert direkt aus storyboard.json)
templates/claude-settings.json  empfohlene Permissions (→ .claude/settings.json kopieren)
tools/                    Python-Helfer (nur Stdlib): new_project, storyboard, comfy_assets, tts, review
scripts/                  setup.sh, doctor.sh
projects/<slug>/          ein Ordner pro Video (Medien git-ignoriert)
voices/                   Referenzstimmen für Voice-Cloning (nur mit Rechten!)
```

### Skills

| Skill | Aufgabe |
|-------|---------|
| `explainer` | Orchestrator: führt durch alle Phasen, mit Freigabe-Gates |
| `story` | Kernaussage, Erzählbogen, Sprechtext fürs Ohr |
| `storyboard` | Szenen, ComfyUI-Prompts, Visual-Arten, Komponenten → `storyboard.json` |
| `comfyui` | ComfyUI per MCP steuern: Workflows, Slots, Jobs, Outputs, Fehlerbehebung |
| `voiceover` | Lokale TTS, Timing aus echter Audiodauer |
| `scene-coding` | Umsetzung in Remotion / Hyperframes / Tesseract, Engines mischen |
| `video-review` | Kontaktbögen, Checkliste, Lautheit |
| `vidgen-setup` | Einrichtung & Diagnose |

Hersteller-Skills (von `setup.sh`, nicht im Repo): `remotion-*` (remotion-dev/skills),
`hyperframes*` (heygen-com/hyperframes), `tesseract-*` (mirage-hq/Tesseract).

### Manuell ohne Claude

```bash
python3 tools/new_project.py demo --title "Demo"
python3 tools/tts.py projects/demo --backend say
python3 tools/comfy_assets.py projects/demo
cd projects/demo/remotion && npm install && npx remotion render Explainer ../renders/final.mp4
python3 tools/review.py projects/demo
```

## Recherche: Gibt es das schon? (Stand 2026-11)

| Projekt | Was es ist | Warum nicht einfach das |
|---------|-----------|--------------------------|
| [digitalsamba/claude-code-video-toolkit](https://github.com/digitalsamba/claude-code-video-toolkit) (MIT) | Sehr ähnliches Ziel: Skills/Commands für Claude Code, Remotion, TTS, Musik, LTX-2 | Generierung läuft auf **Cloud-GPUs** (Modal/RunPod), kein ComfyUI – gute Ideenquelle |
| [Comfy-Org/comfy-mcp](https://github.com/Comfy-Org/comfy-mcp) | Offizieller lokaler MCP-Server für ComfyUI | **wird hier verwendet** |
| [artokun/comfyui-mcp](https://github.com/artokun/comfyui-mcp) (MIT) | Sehr umfangreicher MCP-Server (178 Tools) + Sidebar-Agent | Alternative, falls mehr Graph-Editing nötig ist |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) (Apache-2.0) | HTML → Video, mit Agent-Skills | **wird hier verwendet** |
| [remotion-dev/skills](https://github.com/remotion-dev/skills) | Offizielle Remotion-Skills | **wird hier verwendet** |
| [mirage-hq/Tesseract](https://github.com/mirage-hq/Tesseract) | Motion/3D/Schnitt per CLI + Skills (proprietär) | **wird hier verwendet** (optional) |

Ein fertiger ComfyUI-Workflow „Erklärvideo end-to-end“ existiert nicht – ComfyUI
liefert die Bausteine (Bild, Clip, Stimme, Musik), die Dramaturgie und das
Compositing übernimmt hier Claude + Code-Renderer.

## Lizenzen beachten

- **Remotion** ist für Firmen ab 4 Mitarbeitenden lizenzpflichtig (Skill `remotion-license`).
- **comfy-mcp**: AGPL-3.0 oder kommerziell – wird nur als Werkzeug ausgeführt, nicht eingebunden.
- **Tesseract**: proprietäre Nutzungsbedingungen von Mirage.
- Modelle (Z-Image, LTX-2.3, ChatterBox, ACE-Step) haben eigene Lizenzen – vor kommerzieller Nutzung prüfen.
- Voice-Cloning nur mit Stimmen, für die eine Einwilligung vorliegt.
