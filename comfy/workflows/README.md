# ComfyUI-Workflows

Offizielle ComfyUI-Vorlagen (per `comfy templates fetch` geholt), im UI-Format.
`comfy-cli` (und damit `comfy-mcp`) setzt Werte über **Slot-Adressen**
(`<node-id>.<feld>`, in Subgraphen `<subgraph-id>/<node-id>.<feld>`).
Aktuelle Slots jederzeit nachsehen: MCP `list_workflow_slots` bzw.
`comfy --json workflow slots <datei>`.

Status geprüft am 2026-11-09 mit `comfy validate --input <object_info.json>` (comfy-cli 1.13, `scripts/doctor.sh`).

## `image_z_image_turbo.json` – Text → Bild ✅ lauffähig

| Slot | Bedeutung | Default |
|------|-----------|---------|
| `57.text` | Prompt | – |
| `57.width` / `57.height` | Auflösung | 1024 / 1024 → für 16:9 **1344×768**, 9:16 **768×1344** |
| `57.seed` | Seed | 0 |
| `57.steps` | Schritte | 8 (Turbo: 8 reicht) |
| `9.filename_prefix` | Ausgabename | `z-image-turbo` |

## `image_qwen_2_1_turbo_edit.json` / `image_qwen_2_1_turbo_edit_ref.json` – Bild bearbeiten ✅ lauffähig

Qwen Image 2.1 Turbo Edit (Gallery-Vorlage `image_qwen_2_1_turbo_image_edit`, geprüft 2026-11-13 auf
ComfyUI v0.43). Einsatz: **wiederkehrende Figur** – Foto einer Person → Figur im Videostil
(`_edit`, 1 Bild, `tools/character.py`) und Figur in jedes Szenenbild einsetzen
(`_edit_ref`, Bild 1 = Szenenbild aus Z-Image, Bild 2 = Referenzfigur, `tools/comfy_assets.py`).
Im Prompt heißen die Bilder `<image1>`, `<image2>`.

Modelle: `qwen_image_2.1_turbo_int8_convrot.safetensors` (diffusion_models),
`qwen3vl_8b_int8_convrot.safetensors` (text_encoders), `qwen_image_2.1_vae_bf16.safetensors` (vae).

Gegenüber der Gallery-Vorlage gepatcht:
- Prompt-Link geht direkt vom Subgraph-Eingang an `TextEncodeQwenImage21` (Link 743). Die Vorlage
  führt ihn über einen `PreviewAny`-Node, der den Text erst in neueren ComfyUI-Versionen
  durchreicht – sonst kommt der Prompt **leer** an und das Modell gibt nur das Eingangsbild
  (bzw. freigestellt mit lila Hintergrund) zurück.
- Prompt-Enhancer (Qwen 3.5 9B) bleibt aus (`459.switch_1=false`); sein Lader zeigt auf das ohnehin
  nötige `qwen3vl_8b`, damit kein Zusatzmodell gebraucht wird.
- `_edit_ref`: zweiter `LoadImage` (Node 600) auf `images.image_2`. ImageCompare/Notizen entfernt.

| Slot | Bedeutung | Default |
|------|-----------|---------|
| `459.prompt` | Anweisung (englisch, `<image1>`/`<image2>`) | – |
| `459.width` / `459.height` | Ausgabegröße (bei `459.switch=false`) | 1024 / 1024 → 16:9 **1344×768** |
| `459.seed` | Seed | – |
| `470.image` | Bild 1 (Dateiname in `input/`) | `example.png` |
| `600.image` | Bild 2 / Referenz (nur `_edit_ref`) | `example.png` |
| `461.filename_prefix` | Ausgabename | `Qwen_image_2.1` |

Tipps: kleine Handyfotos vorher auf ≥ 1024 px hochskalieren. Beim Figurentausch Mimik/Handlung
und abweichende Kleidung ausdrücklich nennen – sonst übernimmt Qwen den neutralen Ausdruck und
die Kleidung der Referenz (z. B. Imkeranzug wird zum Hemd).

## `video_ltx2_3_i2v.json` – Bild → Video ✅ lauffähig

Eingabebild muss vorher per `upload_file` in ComfyUIs `input/` liegen.
**LTX-2.3 blendet die letzten ~2 s jedes Clips nach Schwarz ab** – `comfy_assets.py` erzeugt
Clips deshalb 3 s länger als die Szene (max. 10 s) und setzt bei längeren Szenen
`visual.props.playbackRate`.

| Slot | Bedeutung | Default |
|------|-----------|---------|
| `269.image` | Eingabebild (Dateiname in `input/`) | – |
| `320.value` | Prompt (Bewegung + Kamera) | – |
| `320.value_1` | prompt_enhance (Gemma erweitert den Prompt) | false |
| `320.value_2` / `320.value_3` | Breite / Höhe | 1280 / 720 |
| `320.value_4` | Dauer in Sekunden | 5 |
| `320.value_5` | fps | 25 |
| `320.noise_seed` | Seed | – |
| `75.filename_prefix` | Ausgabename | `video/LTX_2.3_i2v` |

## `video_ltx2_3_t2v.json` – Text → Video ✅ lauffähig

**Achtung: andere Slot-Namen als i2v!**

| Slot | Bedeutung | Default |
|------|-----------|---------|
| `267.value` | Prompt | – |
| `267.value_5` | prompt_enhance | true |
| `267.value_2` / `267.value_3` | Breite / Höhe | 1280 / 720 |
| `267.value_4` | Dauer in Sekunden | 5 |
| `267.value_1` | fps | 25 |
| `267.noise_seed` | Seed | – |
| `75.filename_prefix` | Ausgabename | `video/LTX_2.3_t2v` |

## `audio-chatterbox_tts_multilingual.json` – Text → Sprache ✅ lauffähig

Benötigt den Custom Node `FL_ChatterboxMultilingualTTS` (Paket *ComfyUI_Fill-ChatterBox*).
Installation: MCP `install_node` (fragt nach) oder ComfyUI-Manager; Modelle lädt der
Node beim ersten Lauf selbst. Danach Slots prüfen – erwartet:

| Slot | Bedeutung |
|------|-----------|
| `2.audio` | Referenzstimme (Datei in `input/`, 10–20 s sauberes Sprachsample) |
| `1.text` | Sprechtext |
| `1.language` | z. B. `German (de)` |
| `1.seed` | Seed (für reproduzierbare Takes fixieren) |
| `3.filename_prefix` | Ausgabename |

## `audio_ace_step1_5_xl_turbo.json` – Musik ✅ lauffähig

Modelle installiert (geprüft 2026-11-08, Größen = Hugging Face). Benötigt `acestep_v1.5_xl_turbo_bf16.safetensors`, `ace_1.5_vae.safetensors`,
`qwen_0.6b_ace15.safetensors`, `qwen_4b_ace15.safetensors`
(Hugging Face: `Comfy-Org/ace_step_1.5_ComfyUI_files`, Download per MCP `download_model`).

| Slot | Bedeutung |
|------|-----------|
| `94.tags` | Stil-Tags, z. B. `ambient corporate, soft piano, warm pads, 90 BPM, instrumental` |
| `94.lyrics` | `[instrumental]` für Hintergrundmusik |
| `94.bpm`, `94.keyscale`, `94.language` | Tempo, Tonart, Sprache |
| `98.seconds`, `94.duration` | Dauer in Sekunden – **beide** setzen. `99` ist ein reiner UI-Primitive (speist beide im Editor), comfy-cli ≥ 1.13 lehnt Slots darauf ab |
| `109.value` | Seed |
| `111.filename_prefix` | Ausgabename |

## Neue Workflows hinzufügen

1. `search_templates` / `fetch_template` (MCP) oder eigenen Workflow aus der ComfyUI-Oberfläche exportieren.
2. Hier ablegen, `validate_workflow` laufen lassen, Slot-Tabelle oben ergänzen.
3. In `tools/comfy_assets.py` (`WORKFLOWS`) die Slot-Zuordnung eintragen.
