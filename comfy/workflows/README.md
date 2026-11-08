# ComfyUI-Workflows

Offizielle ComfyUI-Vorlagen (per `comfy templates fetch` geholt), im UI-Format.
`comfy-cli` (und damit `comfy-mcp`) setzt Werte über **Slot-Adressen**
(`<node-id>.<feld>`, in Subgraphen `<subgraph-id>/<node-id>.<feld>`).
Aktuelle Slots jederzeit nachsehen: MCP `list_workflow_slots` bzw.
`comfy --json workflow slots <datei>`.

Status geprüft am 2026-11-08 gegen die lokale Installation (`comfy workflow validate`).

## `image_z_image_turbo.json` – Text → Bild ✅ lauffähig

| Slot | Bedeutung | Default |
|------|-----------|---------|
| `57.text` | Prompt | – |
| `57.width` / `57.height` | Auflösung | 1024 / 1024 → für 16:9 **1344×768**, 9:16 **768×1344** |
| `57.seed` | Seed | 0 |
| `57.steps` | Schritte | 8 (Turbo: 8 reicht) |
| `9.filename_prefix` | Ausgabename | `z-image-turbo` |

## `video_ltx2_3_i2v.json` – Bild → Video ✅ lauffähig

Eingabebild muss vorher per `upload_file` in ComfyUIs `input/` liegen.

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

## `audio-chatterbox_tts_multilingual.json` – Text → Sprache ⚠️ Custom Node fehlt

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

## `audio_ace_step1_5_xl_turbo.json` – Musik ⚠️ Modelle fehlen

Benötigt `acestep_v1.5_xl_turbo_bf16.safetensors`, `ace_1.5_vae.safetensors`,
`qwen_0.6b_ace15.safetensors`, `qwen_4b_ace15.safetensors`
(Hugging Face: `Comfy-Org/ace_step_1.5_ComfyUI_files`, Download per MCP `download_model`).

| Slot | Bedeutung |
|------|-----------|
| `94.tags` | Stil-Tags, z. B. `ambient corporate, soft piano, warm pads, 90 BPM, instrumental` |
| `94.lyrics` | `[instrumental]` für Hintergrundmusik |
| `94.bpm`, `94.keyscale`, `94.language` | Tempo, Tonart, Sprache |
| `99.value` | Dauer in Sekunden (Primitive, speist `98.seconds` und `94.duration`) |
| `109.value` | Seed |
| `111.filename_prefix` | Ausgabename |

## Neue Workflows hinzufügen

1. `search_templates` / `fetch_template` (MCP) oder eigenen Workflow aus der ComfyUI-Oberfläche exportieren.
2. Hier ablegen, `validate_workflow` laufen lassen, Slot-Tabelle oben ergänzen.
3. In `tools/comfy_assets.py` (`WORKFLOWS`) die Slot-Zuordnung eintragen.
