---
name: explainer
description: Orchestriert die komplette Produktion eines Erklärvideos – vom Briefing über Story, Storyboard, Stimme, ComfyUI-Assets und Szenen-Code bis zum gerenderten MP4. Verwenden, sobald der User ein Video/Erklärvideo/Explainer erstellen, fortsetzen oder überarbeiten will („mach ein Video über …“, „/explainer“, „weiter mit dem Video“).
---

# Erklärvideo-Orchestrator

Du führst ein Video durch acht Phasen. Jede Phase hat einen eigenen Skill mit
den Details – lies ihn, bevor du die Phase beginnst. Der Zustand liegt immer in
`projects/<slug>/storyboard.json` (Feld `status`), damit eine Produktion jederzeit
fortgesetzt werden kann.

## 0. Projekt finden oder anlegen

- `python3 tools/storyboard.py list` zeigt vorhandene Projekte und ihren Status.
- Fortsetzen: Storyboard lesen, beim ersten nicht erledigten Schritt weitermachen.
- Neu: `python3 tools/new_project.py <slug> --title "<Titel>" [--compositor remotion|hyperframes|tesseract] [--format 16:9|9:16|1:1]`
  legt `projects/<slug>/` aus `templates/project/` an.
- Vorher kurz `server_info` (comfy-mcp) aufrufen. Läuft ComfyUI nicht → `vidgen-setup`.

## 1. Briefing → `brief.md`

Kläre in **einer** Rückfrage-Runde (AskUserQuestion, max. 4 Fragen), was fehlt:
Zielgruppe & Vorwissen · Kernbotschaft / gewünschte Handlung danach ·
Länge (Default 60–90 s) · Format (16:9 / 9:16) · Sprache & Tonalität ·
visueller Stil (z. B. flache Vektor-Illustration, Isometrie, Fotorealismus, Whiteboard) ·
Pflichtinhalte/Quellen · Branding (Farben, Logo, Schrift).
Was der User schon gesagt hat, nicht erneut fragen. Sinnvolle Defaults setzen
und im Brief als „Annahme“ markieren. → **Gate:** Brief kurz zusammenfassen, bestätigen lassen.

## 2. Story → `story.md` (Skill `story`)
## 3. Storyboard → `storyboard.json` (Skill `storyboard`) → **Gate**

Zeige dem User das Storyboard als kompakte Tabelle (Szene · Dauer-Schätzung ·
Sprechtext-Anfang · Visual-Art · Bild-Prompt-Kurzform). Erst nach OK generieren.

## 4. Stimme (Skill `voiceover`)

Sprechtexte vertonen, echte Dauern ins Storyboard schreiben
(`python3 tools/storyboard.py timing projects/<slug>`).

## 5. Assets (Skill `comfyui`)

Erst **eine** Probe-Szene erzeugen und dem User zeigen (Stil-Check), dann den Rest
im Batch: `python3 tools/comfy_assets.py projects/<slug>`. Optional Musik.

## 6. Szenen-Code (Skill `scene-coding`)

Je nach `storyboard.compositor` Remotion, Hyperframes oder Tesseract.

## 7. Review (Skill `video-review`) → **Gate**

Kontaktbogen + Stichproben ansehen, Probleme selbst beheben, dann dem User zeigen.

## 8. Final-Render

Render nach `projects/<slug>/renders/final.mp4`, Status `done` setzen und dem
User Pfad, Laufzeit und eine Liste offener Punkte nennen.

## Arbeitsweise

- Nach jeder Phase `status` im Storyboard aktualisieren
  (`brief → story → storyboard → voice → assets → scenes → review → done`).
- Lange Generierungen (Video-Clips: mehrere Minuten pro Clip auf MPS) im
  Hintergrund laufen lassen und währenddessen Szenen-Code schreiben.
- Fehler aus ComfyUI: `get_logs` lesen, `job` mit `action="status"` prüfen,
  bei Speicherproblemen `free_memory` und Auflösung/Dauer reduzieren.
- Änderungswünsche des Users immer zuerst ins Storyboard, dann neu erzeugen –
  nur betroffene Szenen (`--only s03,s05`).
