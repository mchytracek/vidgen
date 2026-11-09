---
name: explainer
description: Orchestriert die komplette Produktion eines Erklärvideos – vom Briefing über Story, Storyboard, Stimme, ComfyUI-Assets und Szenen-Code bis zum gerenderten MP4. Verwenden, sobald der User ein Video/Erklärvideo/Explainer erstellen, fortsetzen oder überarbeiten will („mach ein Video über …“, „/explainer“, „weiter mit dem Video“).
---

# Erklärvideo-Orchestrator

Du führst ein Video durch acht Phasen. Jede Phase hat einen eigenen Skill mit
den Details – lies ihn, bevor du die Phase beginnst. Der Zustand liegt immer in
`video/storyboard.json` (Feld `status`), damit eine Produktion jederzeit
fortgesetzt werden kann.

## 0. Stand feststellen

Dieses Repo ist **ein Video** (Klon des vidgen-Templates). Alles Videospezifische
liegt in `video/`.

- `video/` fehlt → Repo ist noch nicht initialisiert. Titel (und ggf. Format,
  Compositor, Länge) erfragen bzw. aus der Anfrage ableiten, dann
  `scripts/init.sh "<Titel>" [--format 16:9|9:16|1:1] [--compositor remotion|hyperframes|tesseract] [--duration 60] [--comfy-url http://host:8188]`.
  `--comfy-url` nur, wenn der User einen anderen ComfyUI-Rechner nennt; sonst gilt die
  zuletzt gewählte Adresse bzw. lokal. Nach einer Adressänderung Claude Code neu starten.
  Das legt `video/` an, benennt `origin` in `template` um, committet und installiert Remotion.
- `video/` existiert → `python3 tools/storyboard.py show` zeigt Status und Szenen;
  beim ersten nicht erledigten Schritt weitermachen.
- Kurz `server_info` (comfy-mcp) aufrufen. Läuft ComfyUI nicht → `vidgen-setup`.
- Nach jeder abgeschlossenen Phase committen (`git add video && git commit -m "<Phase>: …"`),
  damit der Verlauf des Videos nachvollziehbar bleibt. Generierte Medien sind git-ignoriert.

## 1. Briefing → `brief.md`

Kläre in **einer** Rückfrage-Runde (AskUserQuestion, max. 4 Fragen), was fehlt:
Zielgruppe & Vorwissen · Kernbotschaft / gewünschte Handlung danach ·
Länge (Default 60–90 s) · Format (16:9 / 9:16) · Sprache & Tonalität ·
visueller Stil (z. B. flache Vektor-Illustration, Isometrie, Fotorealismus, Whiteboard) ·
Pflichtinhalte/Quellen · Branding (Farben, Logo, Schrift).
Was der User schon gesagt hat, nicht erneut fragen. Sinnvolle Defaults setzen
und im Brief als „Annahme“ markieren. → **Gate:** Brief kurz zusammenfassen, bestätigen lassen.

**Eigene Screenshots (Produktvideo):** Liegen Dateien in `video/assets/screens/`
oder nennt der User Screenshots/Bildschirmaufnahmen seines Produkts, ist es ein
**Screenshot-Video**: Die Bilder des Ablaufs kommen von dort, nicht aus ComfyUI.
Dann `python3 tools/screens.py check` ausführen, **jeden Screenshot mit `Read`
ansehen** und im Brief festhalten: Liste der Screenshots in Ablaufreihenfolge mit
je einem Satz, was zu sehen ist (Bildschirm, relevante Buttons/Felder mit
wörtlicher Beschriftung). Fehlende Schritte im Ablauf beim User nachfordern statt
sie zu generieren. Format-Warnungen von `check` ansprechen (anderes
Seitenverhältnis → `framed: true` bleibt Default; zu klein → neu aufnehmen).
ComfyUI liefert dann nur Stimme, Musik und ggf. Stimmungsbilder (Intro/Outro).

## 2. Story → `story.md` (Skill `story`)
## 3. Storyboard → `storyboard.json` (Skill `storyboard`) → **Gate**

Zeige dem User das Storyboard als kompakte Tabelle (Szene · Dauer-Schätzung ·
Sprechtext-Anfang · Visual-Art · Bild-Prompt-Kurzform). Erst nach OK generieren.

## 4. Stimme (Skill `voiceover`)

Sprechtexte vertonen, echte Dauern ins Storyboard schreiben
(`python3 tools/storyboard.py timing`).

## 5. Assets (Skill `comfyui`)

Erst **eine** Probe-Szene erzeugen und dem User zeigen (Stil-Check), dann den Rest
im Batch: `python3 tools/comfy_assets.py`. Optional Musik.
Screenshot-Szenen (`kind: "code"`) überspringt `comfy_assets.py` automatisch.
Bei Screenshot-Videos ist der Stil-Check stattdessen ein Fokus-Check:
`python3 tools/screens.py stills --only <id>` und das Ergebnis ansehen.

## 6. Szenen-Code (Skill `scene-coding`)

Je nach `storyboard.compositor` Remotion, Hyperframes oder Tesseract.

## 7. Review (Skill `video-review`) → **Gate**

Kontaktbogen + Stichproben ansehen, Probleme selbst beheben, dann dem User zeigen.

## 8. Final-Render

Render nach `video/renders/final.mp4`, Status `done` setzen und dem
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
