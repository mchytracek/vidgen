---
name: storyboard
description: Übersetzt eine Story in ein maschinenlesbares storyboard.json – Szenen mit Sprechtext, Bild-/Video-Prompts für ComfyUI, Bildschirmtext, Komponenten und Renderer. Verwenden in Phase 3 des Explainer-Workflows oder wenn Szenen, Prompts, Reihenfolge oder visuelle Planung eines Videos geändert werden.
---

# Storyboard

Eingabe: `story.md`. Ausgabe: `storyboard.json` gemäß `schemas/storyboard.schema.json`.
Nach jedem Schreiben: `python3 tools/storyboard.py validate`.

## Globale Felder festlegen

- `format`: 1920×1080 (16:9) oder 1080×1920 (9:16), `fps` 30.
- `style.imagePrompt`: **ein** Stil-Suffix, das an jeden Bildprompt gehängt wird –
  das ist der wichtigste Hebel für ein einheitliches Video. Beispiel:
  `"flat vector illustration, clean geometric shapes, soft grain, limited palette of deep navy, coral and cream, generous negative space, no text"`.
- `style.palette`, `style.font`: für Code-Szenen (Titel, Diagramme).
- `voice`, `music`, `compositor` aus dem Brief übernehmen.

## Visual-Arten pro Szene (`visual.kind`)

| kind        | Erzeugt von                         | Gut für |
|-------------|-------------------------------------|---------|
| `image`     | Z-Image Turbo (ComfyUI)              | Illustration/Metapher, im Compositor mit Ken-Burns/Parallax animiert |
| `clip`      | LTX-2.3 i2v (aus dem Szenenbild) oder t2v | echte Bewegung: Atmosphäre, Prozess, Figur |
| `code`      | Compositor-Komponente                | Diagramme, Zahlen, Listen, Code, Typo |
| `hyperframes` / `tesseract` | eigene Engine, als MP4 eingebunden | Spezial-Motion-Graphics, 3D |

Faustregeln: ≥ 40 % `code`-Szenen (Präzision, Lesbarkeit), Clips sparsam
(teuer: mehrere Minuten pro 5-s-Clip), maximal 2 Visual-Arten hintereinander gleich.
`image` und `code` lassen sich kombinieren: Bild als Hintergrund, `component` darüber.

## Prompt-Regeln für ComfyUI

- **Englisch**, konkret, Bildaufbau zuerst: Motiv → Handlung → Umgebung → Licht → Kamera.
- **Kein Text im Bild** anfordern – Schrift kommt immer aus dem Code (scharf, übersetzbar).
- Freiraum für Overlays einplanen: „subject on the left third, empty space on the right“.
- Wiederkehrende Figuren/Objekte mit identischer Beschreibung + gleichem `seed`.
- `visual.motionPrompt` (nur `clip`): **eine** Bewegung + Kamera, z. B.
  „slow dolly-in, gears begin to turn, steam rises gently“. LTX-Clips 5 s, 25 fps, 1280×720.

## Szenen-Felder (Kurzreferenz)

```json
{
  "id": "s03",
  "beat": "Mechanismus",
  "narration": "Sprechtext, exakt so wie er vertont wird.",
  "visual": {
    "kind": "image",
    "prompt": "a giant lighthouse made of server racks …",
    "motionPrompt": null,
    "seed": 7,
    "component": "ImageWithCaption",
    "props": { "headline": "Ein Leuchtturm für Daten" }
  },
  "onScreenText": ["Ein Leuchtturm für Daten"],
  "transition": "fade",
  "padAfter": 0.4
}
```

Dauern (`duration`) und Asset-Pfade (`assets.*`) **nicht** von Hand setzen – die
schreiben `voiceover`/`comfy_assets.py`. Zum Schluss dem User die Szenentabelle zeigen.
