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
schreiben `voiceover`/`comfy_assets.py`. Ausnahme: eigene Medien aus `screens/` (s. u.).
Zum Schluss dem User die Szenentabelle zeigen.

## Szenen mit eigenen Screenshots (`assets/screens/`)

Für Produkt-Screenshots **nie** `kind: "image"` (ComfyUI würde ein Bild generieren),
sondern `kind: "code"` + `component: "ScreenshotFocus"` und `assets.image` von Hand:

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
      "highlight": "box",
      "focus": [
        { "x": 0.78, "y": 0.06, "w": 0.16, "h": 0.06, "label": "Neue Rechnung" },
        { "x": 0.30, "y": 0.32, "w": 0.40, "h": 0.08, "label": "Kunde wählen", "at": 2.8 }
      ]
    }
  },
  "assets": { "image": "screens/02-dashboard.png" }
}
```

- **Koordinaten** = Anteile (0–1) der Bildbreite/-höhe, Ursprung oben links,
  Rechteck um das UI-Element mit etwas Luft. Nicht schätzen: `python3 tools/screens.py grid`
  erzeugt Rasterkopien in `review/screens/` (dünn 5 %, mittel 10 %, dick 50 %) –
  ansehen und ablesen.
- `focus` einzeln oder als Liste (mehrere Klicks auf einem Bildschirm, max. 3);
  `at` = Startzeit in s – an die Stelle im Sprechtext legen, an der das Element
  genannt wird (≈ Wörter davor / 2,3). Ohne `at`: gleichmäßig verteilt.
- `highlight`: `box` (Rahmen, Default) für Buttons/Felder, `spotlight` (Rest
  abdunkeln) für Bereiche/Panels, `none` für Übersichten.
- `cursor: false` für Szenen ohne Klick (Ergebnis zeigen); pro Fokus `click: {x,y}`,
  wenn der Klickpunkt nicht die Mitte des Rahmens ist, oder `click: false`.
- `zoom`: max. Vergrößerung (Default 2.2, berechnet aus der Rahmengröße);
  `1` = keine Kamerafahrt (Übersichtsszene am Anfang eines Ablaufs).
- `step`/`steps` → Badge „2/5“; `framed: false` nur, wenn der Screenshot exakt das
  Videoformat hat.
- Gleiche Datei in mehreren Szenen ist erlaubt (verschiedene Fokuspunkte).
- Bildschirmaufnahmen (MP4): `component: "ClipScene"`, `assets.clip: "screens/…mp4"`,
  ebenfalls `kind: "code"`.
- Faustregeln für Screenshot-Videos: Übersicht → Fokus → nächster Schritt; zwischen
  Schritten ruhig eine `code`-Szene (BulletList, BigNumber) für Nutzen/Ergebnis.
  Die 40-%-Code-Regel gilt hier nicht – ScreenshotFocus *ist* Code.
- `style.imagePrompt` bleibt Pflicht (für Intro/Outro-Bilder), auch wenn keines erzeugt wird.

Nach dem Schreiben: `python3 tools/storyboard.py validate` (prüft auch Fokus-Rechtecke)
und `python3 tools/screens.py check`.
