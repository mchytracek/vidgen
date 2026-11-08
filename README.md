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

## Prinzip: ein Klon = ein Video

Dieses Repo ist ein **Template**. Für jedes neue Video klonst du es in einen
eigenen Ordner und initialisierst es. Der Klon wird dann zum Git-Repo *dieses*
Videos – Brief, Story, Storyboard und Szenen-Code sind versioniert, generierte
Medien (Bilder, Clips, Audio, Renders) sind git-ignoriert.

```
vidgen (Template)                     mein-video (Klon)
├── .claude/skills/  ─┐               ├── .claude/ tools/ comfy/ …   ← Template-Code
├── tools/            │  git clone    │                                 (Updates per
├── comfy/workflows/  ├────────────▶  │                                  update-template.sh)
├── templates/        │  init.sh      └── video/                     ← gehört dem Video
└── scripts/         ─┘                   ├── brief.md  story.md  storyboard.json
                                          ├── remotion/   (Szenen-Code)
                                          ├── assets/     (ComfyUI-Output, ignoriert)
                                          └── renders/    (final.mp4, ignoriert)
```

## Schnellstart: neues Video

Einmalig pro Rechner (comfy-mcp, Hersteller-Skills):

```bash
scripts/setup.sh
```

Pro Video:

```bash
git clone https://github.com/mchytracek/vidgen.git wie-dns-funktioniert
```

```bash
cd wie-dns-funktioniert && scripts/init.sh "Wie DNS funktioniert" --duration 60
```

`init.sh` legt `video/` an, benennt `origin` in `template` um (damit du später
Updates holen und ein eigenes Remote anlegen kannst), committet und installiert
Remotion. Optionen: `--format 9:16`, `--compositor hyperframes|tesseract`,
`--keep-origin`, `--no-install`, `--no-commit`.

Dann Claude Code im Ordner starten:

> /explainer Erklär Einsteigern in 60 Sekunden, wie DNS funktioniert.

Claude fragt Briefing-Details ab, zeigt Story und Storyboard zur Freigabe, erzeugt
die Assets, committet nach jeder Phase und rendert nach `video/renders/final.mp4`.

Eigenes Remote für das Video (optional):

```bash
git remote add origin <url-des-video-repos> && git push -u origin HEAD
```

Verbesserungen aus dem Template übernehmen (Skills, Tools, Workflows):

```bash
scripts/update-template.sh
```

Diagnose jederzeit:

```bash
scripts/doctor.sh
```

> **Hinweis:** Verbesserst du Skills oder Tools in einem Video-Klon, übertrage sie
> ins Template-Repo – sonst profitieren künftige Videos nicht davon.

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
.claude/skills/           eigene Skills (s. u.)
comfy/workflows/          geprüfte ComfyUI-Workflows + Slot-Referenz (README.md)
schemas/                  storyboard.schema.json – Datenvertrag aller Phasen
templates/project/        Vorlage für video/ inkl. Remotion-Gerüst (rendert direkt aus storyboard.json)
templates/claude-settings.json  empfohlene Permissions (→ .claude/settings.json kopieren)
tools/                    Python-Helfer (nur Stdlib): init_video, storyboard, comfy_assets, tts, review
scripts/                  init.sh, update-template.sh, setup.sh, doctor.sh
video/                    entsteht erst durch init.sh – das Video dieses Klons
voices/                   Referenzstimmen für Voice-Cloning (nur mit Rechten!); martin_ref.wav = Standard
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

Hersteller-Skills (von `setup.sh` global nach `~/.claude/skills`, nicht im Repo): `remotion-*` (remotion-dev/skills),
`hyperframes*` (heygen-com/hyperframes), `tesseract-*` (mirage-hq/Tesseract).

### Manuell ohne Claude

```bash
scripts/init.sh "Demo"
python3 tools/tts.py --backend say      # Entwurfsstimme, setzt Timing
python3 tools/comfy_assets.py           # Bilder/Clips/Musik aus ComfyUI
(cd video/remotion && npx remotion render Explainer ../renders/final.mp4)
python3 tools/review.py                 # Kontaktbögen, Lautheit (braucht ffmpeg)
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
