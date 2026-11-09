---
name: comfyui
description: Steuert das lokale ComfyUI über den MCP-Server comfy-mcp – Bilder (Z-Image Turbo), Videoclips (LTX-2.3), Sprache (ChatterBox) und Musik (ACE-Step) erzeugen, Jobs überwachen, Ergebnisse abholen und prüfen, Workflows anpassen. Verwenden, wenn Assets für ein Video erzeugt werden, ein ComfyUI-Workflow ausgeführt/angepasst werden soll, oder bei ComfyUI-Fehlern.
---

# ComfyUI über MCP

Alle Werkzeuge kommen vom MCP-Server **`comfy-mcp`** (Comfy-Org, baut auf `comfy-cli`).
Er spricht mit dem ComfyUI, das für dieses Repo konfiguriert ist – Default lokal
`127.0.0.1:8188`, sonst ein anderer Rechner (siehe „Entfernter ComfyUI-Server“ unten).
Workflows und ihre
Slot-Adressen: `comfy/workflows/README.md` – **vor dem ersten Lauf lesen.**

## Standard-Ablauf für ein Asset

1. `server_info` – läuft ComfyUI? (Einmal pro Sitzung.)
2. **Arbeitskopie** anlegen – `set_workflow_slot` schreibt *in place*, die Vorlagen in
   `comfy/workflows/` dürfen nie verändert werden:
   `cp comfy/workflows/image_z_image_turbo.json video/.work/s03_image.json`, dann
   `set_workflow_slot(workflow_path="video/.work/s03_image.json",
   overrides={"57.text": "<prompt>, <style.imagePrompt>", "57.width": 1344, "57.height": 768, "57.seed": 7, "9.filename_prefix": "vidgen/<storyboard.slug>/s03"})`.
3. `run_workflow(workflow_path=<kopie>, wait=true, timeout_seconds=…)`
   – Bild: 60–120 s, LTX-Clip 5 s: **600–1200 s** auf Apple Silicon.
   Bei langen Jobs `wait=false` und später `job(action="watch", prompt_id=…)`.
4. `fetch_outputs(prompt_id, out_dir="video/assets/images")`.
5. **Ansehen:** Bilder mit `Read` öffnen; Videos mit
   `preview_media(media_path=…)` als Kontaktbogen. Passt Stil/Motiv nicht →
   Prompt schärfen oder Seed wechseln, nicht weiterbauen.
6. Pfad ins Storyboard schreiben (`assets.image` / `assets.clip`).

## Batch für ein ganzes Storyboard

```bash
python3 tools/comfy_assets.py                                 # alle fehlenden Assets
python3 tools/comfy_assets.py                 --only s03,s07  # gezielt neu
python3 tools/comfy_assets.py                 --kind image    # nur Bilder
python3 tools/comfy_assets.py                 --dry-run       # nur zeigen, was liefe
```

Das Skript nutzt dieselbe Engine (`comfy` CLI) wie der MCP-Server, wendet
`style.imagePrompt` an, erzeugt für `clip`-Szenen zuerst das Startbild (Z-Image)
und dann den LTX-i2v-Clip, und trägt alle Pfade ins Storyboard ein.
Bei vielen Clips im Hintergrund starten (`run_in_background`).

## Modelle & Auflösungen

| Zweck | Workflow | Auflösung | Hinweis |
|-------|----------|-----------|---------|
| Standbild 16:9 | Z-Image Turbo | 1344×768 | 8 Steps; kein Text im Bild anfordern |
| Standbild 9:16 | Z-Image Turbo | 768×1344 | |
| Clip | LTX-2.3 i2v | 1280×720, 5 s, 25 fps | aus dem Szenenbild → konsistenter Look |
| Clip ohne Bild | LTX-2.3 t2v | 1280×720 | Slot-Namen weichen ab! |
| Sprache | ChatterBox Multilingual | – | siehe Skill `voiceover` |
| Musik | ACE-Step 1.5 XL Turbo | – | `[instrumental]`, Lautstärke im Mix 0.10–0.18 |

Ausgaben des Compositors werden auf Zielauflösung skaliert (Bilder `cover`).

## Prompting

- **Z-Image Turbo**: natürlichsprachige, dichte Beschreibung (Englisch; Chinesisch geht auch).
  Reihenfolge Motiv → Komposition → Stil → Licht. Keine Negativ-Prompts (cfg 1).
- **LTX-2.3**: Beschreibe *Bewegung über Zeit* in 1–3 Sätzen, eine Kamerabewegung.
  `prompt_enhance` an, wenn der Prompt kurz ist. LTX erzeugt auch Ton –
  im Compositor stumm schalten, wenn Sprache drüberliegt.

## Fehlerbehebung

| Symptom | Maßnahme |
|---------|----------|
| `server_info` meldet nichts erreichbar | User bitten, ComfyUI zu starten, oder `launch_comfyui` (fragt nach) |
| `unknown_class_type` | Custom Node fehlt → `workflow_deps`, dann `install_node` (User fragen) |
| `unknown_enum_value` bei Modell | `search_models`, ggf. `download_model` (User fragen, große Downloads) |
| MPS Out-of-Memory / sehr langsam | `free_memory`, Auflösung/Dauer senken, Jobs nacheinander |
| Job hängt | `job(action="status")`, `get_logs(tail=200)`, ggf. `job(action="cancel")` |

**Nie ohne Zustimmung:** `partner_generate`, `confirm_spend=true`, `install_node`,
`download_model`, `update_comfyui`, `restart_comfyui`.
Neue Workflows: Ablauf in `comfy/workflows/README.md` („Neue Workflows hinzufügen“).

## Entfernter ComfyUI-Server

Die Adresse kommt aus `$COMFYUI_URL` > `.vidgen.env` (pro Klon, von `scripts/init.sh`,
git-ignoriert) > `~/.config/vidgen/env` > `http://127.0.0.1:8188`;
`python3 tools/_common.py comfy-url` zeigt die aktive. `scripts/comfy-mcp.sh` startet
comfy-mcp damit (`COMFYUI_URL`), die Python-Tools geben sie als `COMFY_LOCAL_URL` an comfy-cli.

- `server_info` zeigt dann einen `comfy_target`-Block mit dem Host. **Hardware-Angaben
  in `server_info` beschreiben diesen Mac, nicht den GPU-Rechner** – Speicher-/Dauer-
  Abschätzungen nicht daraus ableiten, im Zweifel den User fragen.
- Ausgaben liegen auf dem anderen Rechner: immer `fetch_outputs(prompt_id, out_dir=…)`
  benutzen (lädt per HTTP), nie Pfade im ComfyUI-Ordner annehmen. Die Tools
  (`comfy_assets.py`, `tts.py`) laden `/view`-URLs automatisch nach `video/.work/comfy_out/`.
- Eingaben (Startbilder, Referenzstimme) gehen per `upload_file` / `comfy upload` – das
  funktioniert remote unverändert.
- `download_model`, `install_node`, `restart_comfyui`, `update_comfyui` wirken auf
  **diesen** Rechner, nicht auf den Server – Modelle/Custom Nodes auf dem Server selbst
  installieren (User bitten) und danach `validate_workflow` erneut prüfen.
- Nur `http://host:port` ohne Pfad/TLS (Grenze von comfy-cli/comfy-mcp). Für Zugriff von
  außen VPN/Tailscale oder SSH-Tunnel (`ssh -L 8188:127.0.0.1:8188 gpu-box`, dann lokal lassen).
- Ein eigener Rechner im LAN/VPN ist **kein** Cloud-Dienst – Regel „Lokal-first“ bleibt
  erfüllt; Partner-/Cloud-Modelle brauchen weiterhin ausdrückliche Zustimmung.

