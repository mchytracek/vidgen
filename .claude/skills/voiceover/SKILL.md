---
name: voiceover
description: Vertont die Sprechtexte eines Storyboards lokal (ChatterBox Multilingual in ComfyUI, Fallback macOS say), misst die Dauern und schreibt das Timing ins storyboard.json. Verwenden in Phase 4 des Explainer-Workflows, bei neuen Sprechtexten, Stimmwechsel oder Aussprache-Problemen.
---

# Voiceover

```bash
python3 tools/tts.py                       # alle Szenen ohne Audio
python3 tools/tts.py --only s02 --force    # eine Szene neu
python3 tools/tts.py --backend say         # schneller Entwurf ohne ComfyUI
python3 tools/storyboard.py timing         # Dauern messen & eintragen
```

## Backends (`storyboard.voice.backend`)

| Backend | Qualität | Voraussetzung |
|---------|----------|---------------|
| `comfyui-chatterbox` | gut, Voice-Cloning, 23 Sprachen inkl. Deutsch | Custom Node *ComfyUI_Fill-ChatterBox* + Referenzstimme |
| `say` | Entwurf / Timing-Test | macOS, Stimme z. B. `Anna` (de) |

**Referenzstimme:** `voice.reference` zeigt auf eine Datei in `voices/`
(10–20 s, sauber, ohne Musik, gleiche Sprache). `tools/tts.py` lädt sie per
`comfy upload` in ComfyUIs `input/`. Nur Stimmen verwenden, für die der User
die Rechte hat (eigene Stimme oder lizenziert).

## Timing-Regeln

- Szenendauer = Audiodauer + `padAfter` (Default 0.4 s), mindestens `minDuration`.
- `tools/storyboard.py timing` misst mit `ffprobe` und schreibt `duration` und
  `audioDuration` je Szene sowie `totalDuration`.
- Ziel-Länge aus dem Brief um > 15 % überschritten → Sprechtext kürzen, nicht schneller sprechen.

## Qualität prüfen

- Stichprobe anhören lassen ist unmöglich – stattdessen: Dauer vs. Wortzahl prüfen
  (Deutsch ≈ 2,3 Wörter/s; stark abweichend → Halluzination/Abbruch, neu erzeugen
  mit anderem Seed).
- Ausspracheprobleme (Abkürzungen, Anglizismen): Sprechtext phonetisch umschreiben
  (`„Ä-Pi-Ai“` statt „API“), nicht den Bildschirmtext.
- Lautheit wird im Final-Render normalisiert (Skill `video-review`).
