---
name: scene-coding
description: Setzt ein fertiges storyboard.json mit Remotion, Hyperframes oder Tesseract als Code um – Szenen-Komponenten, Animationen, Bild/Clip/Audio-Einbindung, Vorschau und Render. Verwenden in Phase 6/8 des Explainer-Workflows oder wenn Szenen eines Videos programmiert, animiert oder gerendert werden.
---

# Szenen coden

Der Compositor steht in `storyboard.compositor`. Für Engine-Details die
**Hersteller-Skills** laden (installiert von `scripts/setup.sh`):
Remotion → `remotion-best-practices`; Hyperframes → `hyperframes`, `hyperframes-cli`;
Tesseract → `tesseract-motion`, `tesseract-video`, `tesseract-3d`.
Fehlen sie → `vidgen-setup`.

## Gemeinsame Regeln (alle Engines)

- **Daten aus dem Storyboard**, nie hart codiert: Texte, Dauern, Asset-Pfade.
  Szenenstart = Summe der vorherigen `duration`.
- Assets liegen in `video/assets/` (Bilder, Clips, Audio, Musik).
- Typo-Sicherheitsabstand 5 % vom Rand; Schrift ≥ 42 px bei 1080p; max. 7 Wörter
  pro Bildschirmzeile; Text erscheint *mit* dem gesprochenen Wort, nicht davor.
- Bewegung hat Bedeutung: Ken-Burns 1.0→1.08 über die Szene, Ease-out für Eintritte,
  keine Dauer-Wackelanimationen. Palette/Schrift aus `storyboard.style`.
- LTX-Clips stumm einbinden (Sprache liegt drüber); Musik 0.10–0.18 Lautstärke,
  am Ende 1 s ausblenden.

## Remotion (Default) – `video/remotion/`

Vorlage aus `templates/project/remotion/` (kopiert `scripts/init.sh`). Aufbau:

- `src/Root.tsx` – liest `storyboard.json` (über `public/` = `../assets` + Kopie
  des Storyboards), berechnet Gesamtdauer per `calculateMetadata`.
- `src/Explainer.tsx` – legt Szenen als `<Sequence>` hintereinander, Audio je Szene,
  Musik global.
- `src/scenes/*.tsx` – eine Komponente je `visual.component`
  (`TitleCard`, `ImageKenBurns`, `ClipScene`, `BulletList`, `BigNumber`, `ImageWithCaption`).
  Neue Szenentypen hier anlegen und in `src/scenes/index.ts` registrieren.

```bash
cd video/remotion && npm install                      # einmalig (macht init.sh)
npx remotion studio                                   # Live-Vorschau (Browser)
npx remotion still Explainer --frame=120 ../review/f120.png   # Einzelbild prüfen
npx remotion render Explainer ../renders/final.mp4
```

Vor dem Render `python3 tools/storyboard.py sync` (kopiert das
Storyboard nach `assets/storyboard.json`, damit Remotion es lädt).

## Hyperframes – `video/hyperframes/`

HTML-Komposition mit `data-start`/`data-duration`/`data-track-index`, GSAP für
Animationen, deterministischer Render über Headless Chrome + FFmpeg.

```bash
cd video && npx hyperframes init hyperframes
npx hyperframes preview      # im Ordner hyperframes/
npx hyperframes render       # → MP4
```

Pro Szene einen Clip/Track; Startzeiten aus dem Storyboard erzeugen (z. B. ein
kleines Node-Skript, das `index.html` aus `storyboard.json` generiert).
Gut für: Typo-lastige Videos, Charts (`npx hyperframes add data-chart`), Shader-Übergänge.

## Tesseract – `.tsrct`-Projekt

CLI `tsrct` (Mirage, proprietär, lokale Projektdatei). Gut für Motion-Design, 3D-Szenen
und Schnitt mit Musik-Sync. Vor Nutzung prüfen, ob für Render ein Login nötig ist,
und dem User sagen, falls etwas das Gerät verlässt. Szenen als MP4 rendern und als
`visual.kind="tesseract"` mit `assets.render` einbinden – oder Tesseract als
Compositor für das ganze Video nutzen.

## Engines mischen

Haupt-Compositor rendert das Video; Szenen anderer Engines werden vorab einzeln
zu `video/assets/clips/<id>_<engine>.mp4` gerendert (exakt
`duration` Sekunden, gleiche Auflösung/fps) und im Compositor wie ein Clip abgespielt.
