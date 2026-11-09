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
Remotion. Außerdem fragt es nach dem ComfyUI-Server (Enter = lokal bzw. zuletzt
gewählte Adresse). Optionen: `--format 9:16`, `--compositor hyperframes|tesseract`,
`--comfy-url http://host:8188`, `--keep-origin`, `--no-install`, `--no-commit`.

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

## ComfyUI auf einem anderen Rechner

ComfyUI muss nicht auf dem Mac laufen, auf dem Claude Code arbeitet – z. B. auf einer
GPU-Workstation im LAN oder per VPN. Default bleibt `http://127.0.0.1:8188`.

**Auf dem Server:** ComfyUI so starten, dass es von außen erreichbar ist, und die
Modelle/Custom Nodes aus [Voraussetzungen](#voraussetzungen) dort installieren:

```bash
python main.py --listen 0.0.0.0 --port 8188
```

**Im Video-Repo:** Adresse bei `init.sh` angeben (oder bei der Abfrage eintippen):

```bash
scripts/init.sh "Wie DNS funktioniert" --comfy-url http://gpu-box:8188
```

Das schreibt `.vidgen.env` (git-ignoriert, gilt für diesen Klon) und merkt sich die
Adresse in `~/.config/vidgen/env` als Vorschlag für die nächsten Videos. Nachträglich
ändern: `.vidgen.env` editieren und Claude Code neu starten. Reihenfolge:
`$COMFYUI_URL` > `.vidgen.env` > `~/.config/vidgen/env` > lokal.

```bash
python3 tools/_common.py comfy-url    # aktive Adresse
scripts/doctor.sh                     # erreichbar? Workflows auf dem Server lauffähig?
```

Was sich ändert: `comfy-mcp` wird über `scripts/comfy-mcp.sh` mit der Adresse
gestartet, die Python-Tools geben sie an `comfy-cli` weiter. Eingaben
(Startbilder, Referenzstimme) werden hochgeladen, Ergebnisse per HTTP nach
`video/.work/comfy_out/` geladen. Eine lokale ComfyUI-Installation ist dann nicht
nötig, `comfy-cli` und `comfy-mcp` schon.

Grenzen:

- Nur `http://host:port` ohne Pfad und ohne TLS (Grenze von comfy-cli/comfy-mcp).
  ComfyUI hat keine Anmeldung – **nicht ins offene Internet stellen**; über VPN
  (z. B. Tailscale) oder SSH-Tunnel (`ssh -L 8188:127.0.0.1:8188 gpu-box`, dann
  lokale Adresse lassen) zugreifen.
- Modelle und Custom Nodes werden auf dem Server installiert; `download_model` /
  `install_node` aus Claude wirken auf den Mac.

## Produktvideo mit eigenen Screenshots

Soll ein Video einen echten Ablauf im Produkt zeigen (z. B. „In 5 Schritten zur
ersten Rechnung“), kommen die Bilder nicht aus ComfyUI, sondern aus deinen
Screenshots. ComfyUI liefert dann nur noch Stimme, Musik und ggf. einzelne
Stimmungsbilder (Intro, Outro).

**1. Screenshots aufnehmen** – einen pro Prozessschritt, in Ablaufreihenfolge:

- Fenster möglichst im Zielformat aufnehmen (16:9, z. B. Browser auf 1920×1080,
  bzw. hochkant für `--format 9:16`). Andere Seitenverhältnisse gehen auch – der
  Screenshot wird dann gerahmt mit Rand gezeigt.
- Demo-Daten statt echter Kundendaten, Benachrichtigungen aus, gleicher
  Zoom/Theme in allen Aufnahmen, Mauszeiger möglichst ausblenden.
- PNG, sprechend benannt: `01-login.png`, `02-dashboard.png`, …

**2. Ablegen und prüfen** in `video/assets/screens/` (legt `init.sh` an). Der
Ordner ist – anders als `assets/images/` – nicht git-ignoriert: Screenshots sind
nicht reproduzierbar und werden mit dem Video versioniert.

```bash
cp ~/Desktop/Screens/*.png video/assets/screens/
```

```bash
python3 tools/screens.py check     # Größe/Seitenverhältnis, Zuordnung zu Szenen
```

**3. Claude Bescheid geben:**

> /explainer Produktvideo, 90 Sekunden: wie man in MeinProdukt eine Rechnung
> erstellt. Die Screenshots der Schritte liegen in video/assets/screens/.

Die Skills erkennen ein Screenshot-Video: Claude sieht sich jeden Screenshot an,
hält im Brief fest, was darauf zu sehen ist, baut die Story entlang der Schritte
(UI-Beschriftungen wörtlich im Sprechtext) und plant pro Schritt eine Szene mit
der Komponente **`ScreenshotFocus`**:

```json
{
  "id": "s03",
  "beat": "Schritt 2: Kunde wählen",
  "narration": "Klick auf „Neue Rechnung“ und wähl den Kunden aus.",
  "visual": {
    "kind": "code",
    "component": "ScreenshotFocus",
    "props": {
      "step": 2, "steps": 5,
      "focus": [
        { "x": 0.78, "y": 0.06, "w": 0.16, "h": 0.06, "label": "Neue Rechnung" },
        { "x": 0.30, "y": 0.32, "w": 0.40, "h": 0.08, "label": "Kunde wählen", "at": 2.8 }
      ]
    }
  },
  "assets": { "image": "screens/02-dashboard.png" }
}
```

`ScreenshotFocus` zeigt den Screenshot gerahmt auf dem Palettenhintergrund, fährt
die Kamera auf jeden Fokus, markiert ihn (`highlight`: `box`, `spotlight` oder
`none`), lässt einen Mauszeiger hinfahren und klicken (`cursor: false` schaltet
das ab) und blendet ein Schritt-Badge („2/5“) und die Bauchbinde (`label`) ein.
`focus` sind Anteile (0–1) der Bildbreite/-höhe, Ursprung oben links; `at` ist
die Startzeit in Sekunden innerhalb der Szene. Alle Props stehen im Kopfkommentar
von `templates/project/remotion/src/scenes/ScreenshotFocus.tsx`.

`kind: "code"` sorgt dafür, dass `tools/comfy_assets.py` für diese Szene nichts
generiert; der Pfad in `assets.image` ist relativ zu `video/assets/`.
`storyboard.py validate` prüft, dass Bild und Fokus-Rechtecke gültig sind.

**4. Fokus-Positionen treffen.** Die Koordinaten liest Claude aus Rasterkopien
ab, statt sie zu schätzen, und prüft danach das Ergebnis als Einzelbild:

```bash
python3 tools/screens.py grid                # → video/review/screens/*_grid.png (Raster 5/10/50 %)
```

```bash
python3 tools/screens.py stills --only s03   # → video/review/screens/s03_focus1.png …
```

Sitzt ein Rahmen daneben, wird die Koordinate im Storyboard korrigiert, nicht im Code.

**Tipps**

- Ein Schritt = eine Szene. Mehrere Klicks auf demselben Bildschirm → mehrere
  Einträge in `focus` (max. 3) oder dieselbe Datei in mehreren Szenen.
- Bildschirmaufnahmen als Video gehen auch: `kind: "code"`,
  `component: "ClipScene"`, `assets.clip: "screens/03-export.mp4"`
  (nicht `kind: "clip"` – dann würde ComfyUI ein Startbild generieren;
  `*.mp4` ist global git-ignoriert, also separat sichern).
- Screenshots **nicht** per LTX (i2v) animieren lassen – das Modell verzerrt
  UI-Text und Layout. Bewegung kommt aus dem Szenen-Code.
- Screenshots mindestens in Videobreite aufnehmen (bei 16:9 ≥ 1700 px breit),
  sonst wird der Zoom unscharf; Retina-Aufnahmen sind ideal.

## Voraussetzungen

| Komponente | Zweck |
|------------|-------|
| ComfyUI (lokal oder auf anderem Rechner, Port 8188) | Bild/Video/Audio-Generierung |
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
tools/                    Python-Helfer (nur Stdlib): init_video, storyboard, comfy_assets, tts, review, screens
scripts/                  init.sh, update-template.sh, setup.sh, doctor.sh, comfy-mcp.sh (MCP-Start mit ComfyUI-Adresse)
video/                    entsteht erst durch init.sh – das Video dieses Klons
voices/                   Referenzstimmen für Voice-Cloning (nur mit Rechten!, git-ignoriert);
                          projektübergreifend: ~/.config/vidgen/voices/ (Standard: martin_ref.wav)
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
