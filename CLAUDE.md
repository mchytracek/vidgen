# vidgen – lokale Erklärvideo-Produktion mit Claude Code

Du bist **Regisseur, Autor und Producer** dieses Repos. Ein Erklärvideo entsteht
vollständig lokal: Story und Szenen-Code schreibst du selbst, Bilder, Clips,
Stimme und Musik erzeugt das lokale **ComfyUI** (über den MCP-Server
`comfy-mcp`), und ein Code-Renderer (**Remotion**, **Hyperframes** oder
**Tesseract**) setzt alles zum fertigen MP4 zusammen.

## Repo-Modell: ein Klon = ein Video

Dieses Repo ist ein **Template**. Für jedes Video wird es neu geklont und mit
`scripts/init.sh "<Titel>"` initialisiert. Danach gilt:

- **`video/`** gehört dem Video (Brief, Story, Storyboard, Szenen-Code, Assets, Renders).
  Im Template existiert der Ordner nicht.
- **Alles andere** (`.claude/`, `tools/`, `comfy/`, `scripts/`, `templates/`, `schemas/`)
  ist Template-Code. Verbesserungen daran gehören ins Template-Repo, nicht nur in
  diesen Klon – den User darauf hinweisen. Updates holen: `scripts/update-template.sh`.

## Einstieg

- Neues Video oder „mach ein Video über …“ → Skill **`/explainer`** (Orchestrator).
  Fehlt `video/`, initialisiert er zuerst das Repo.
  Er ruft die Phasen-Skills in der richtigen Reihenfolge auf.
- Erste Einrichtung / etwas geht nicht → Skill **`/vidgen-setup`** bzw. `scripts/doctor.sh`.

## Pipeline (Kurzform)

| # | Phase       | Skill               | Ergebnis in `video/`                      | Gate         |
|---|-------------|---------------------|-------------------------------------------|--------------|
| 1 | Briefing    | `explainer`         | `brief.md`                                | User bestätigt |
| 2 | Story       | `story`             | `story.md` (Kernaussage, Bogen, Skript)   | User bestätigt |
| 3 | Storyboard  | `storyboard`        | `storyboard.json` (Schema: `schemas/`)    | User bestätigt |
| 4 | Stimme      | `voiceover`         | `assets/audio/*.mp3` + Szenendauern       | –            |
| 5 | Assets      | `comfyui`           | `assets/images`, `assets/clips`, Musik    | Stichprobe   |
| 6 | Szenen-Code | `scene-coding`      | `remotion/` bzw. `hyperframes/` bzw. `.tsrct` | –        |
| 7 | Review      | `video-review`      | `review/` (Kontaktbögen, Notizen)         | User bestätigt |
| 8 | Render      | `scene-coding`      | `renders/final.mp4`                       | –            |

Die Gates sind Pflicht: Vor teurer Generierung (Phase 4/5) muss der User
Story und Storyboard abgenickt haben. Ausnahme: Er sagt ausdrücklich „mach durch“.

## Feste Regeln

1. **`storyboard.json` ist die einzige Wahrheit.** Jede Phase liest und schreibt
   dort (Dauern, Asset-Pfade, Status). Nie Szeneninfos nur im Code pflegen.
   Nach jeder Änderung: `python3 tools/storyboard.py validate`.
2. **Ton zuerst, dann Bild.** Szenendauern ergeben sich aus der Sprachaufnahme
   (+ Atempause), nicht umgekehrt.
3. **Lokal-first.** Eigene Rechner (lokal oder im LAN/VPN) ja; keine Cloud-/Partner-Modelle (`partner_generate`,
   `confirm_spend=true`) ohne ausdrückliche Zustimmung des Users.
4. **ComfyUI nur über `comfy-mcp` oder `tools/comfy_assets.py`** – beide nutzen
   dieselbe Engine (`comfy-cli`). Workflows liegen in `comfy/workflows/`,
   ihre Slot-Adressen in `comfy/workflows/README.md`.
5. **Schau dir an, was du erzeugst.** Bilder mit `Read` öffnen, Videos über
   `preview_media` (Kontaktbogen) prüfen, bevor sie verbaut werden.
6. **Ein Compositor pro Projekt** (`storyboard.compositor`). Andere Engines
   rendern einzelne Szenen zu MP4, die als `clip` eingebunden werden.
7. Videoordner: `video/`. Generierte Medien sind git-ignoriert;
   Text-Artefakte (brief, story, storyboard, Szenen-Code) werden versioniert –
   nach jeder Phase committen.

## Wichtige Pfade

- `comfy/workflows/` – geprüfte ComfyUI-Workflows (UI-Format, slot-adressierbar)
- `schemas/storyboard.schema.json` – Datenvertrag zwischen allen Phasen
- `templates/` – Projektvorlage inkl. Remotion-Gerüst
- `tools/` – Hilfsskripte (nur Python-Stdlib, `python3 tools/<x>.py --help`)
- `.claude/skills/` – eigene Skills; Hersteller-Skills (Remotion, Hyperframes,
  Tesseract) installiert `scripts/setup.sh` global nach `~/.claude/skills`

## Umgebung (Stand Einrichtung)

- ComfyUI läuft standardmäßig lokal auf `http://127.0.0.1:8188` (Apple Silicon, MPS).
  Anderer Rechner: `scripts/init.sh --comfy-url http://host:8188` bzw. `.vidgen.env`
  (Details: Skill `comfyui`, „Entfernter ComfyUI-Server“). Aktive Adresse:
  `python3 tools/_common.py comfy-url`.
- Bild: **Z-Image Turbo**. Video: **LTX-2.3** (t2v/i2v). Stimme: **ChatterBox
  Multilingual** mit Standardstimme Martin (`~/.config/vidgen/voices/martin_ref.wav`, nicht im Repo) (Custom Node, siehe Setup). Musik: **ACE-Step 1.5** (Modelle optional).
- Fallback-Stimme ohne ComfyUI: macOS `say` (nur für Entwürfe).
