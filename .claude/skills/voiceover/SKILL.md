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

**Standardstimme: Martin** – in `templates/project/storyboard.json` als
`voice.reference: "voices/martin_ref.wav"` gesetzt; jedes neue Video nutzt sie automatisch.
Die Datei (16,7 s, −20 LUFS) ist **nicht** im Repo: `tools/tts.py` sucht Referenzstimmen
erst in `voices/`, dann in `~/.config/vidgen/voices/` (überschreibbar per `VIDGEN_VOICES`).
Fehlt sie auf einem Rechner, den User bitten, sie dort abzulegen – nicht auf `say` ausweichen. Nur auf ausdrücklichen Wunsch des Users eine andere Stimme wählen;
`say` nur als Notlösung, wenn ComfyUI/ChatterBox nicht läuft (dem User sagen).

**Referenzstimme:** `voice.reference` zeigt auf eine Datei in `voices/` bzw. gleichnamig in
`~/.config/vidgen/voices/` (Stimmaufnahmen sind personenbezogen und werden nie versioniert)
(10–20 s, sauber, ohne Musik, gleiche Sprache). `tools/tts.py` lädt sie per
`comfy upload` in ComfyUIs `input/`. Nur Stimmen verwenden, für die der User
die Rechte hat (eigene Stimme oder lizenziert).

## Timing-Regeln

- Szenendauer = Audiodauer + `padAfter` (Default 0.4 s), mindestens `minDuration`.
- `tools/storyboard.py timing` misst mit `ffprobe` und schreibt `duration` und
  `audioDuration` je Szene sowie `totalDuration`.
- Ziel-Länge aus dem Brief um > 15 % überschritten → Sprechtext kürzen, nicht schneller sprechen.

## Qualität prüfen

`tools/tts.py` prüft jeden Take automatisch und versucht bis zu 8 Seeds:

- **Satzweise Erzeugung** (kurze Sätze < 7 Wörter werden zusammengelegt) – ChatterBox
  halluziniert bei langen Texten und sehr kurzen Sätzen.
- **Trimmen:** Stille an Anfang/Ende, kurze Geräusche (Atmer, Klick) nach dem letzten Wort.
- **Plausibilität:** 1,5–3,6 Wörter/s, keine Pause > 0,9 s.
- **Vollständigkeit (whisper-cli):** Transkript wird Wort für Wort und in Reihenfolge
  mit dem Sprechtext verglichen (Kölner Phonetik für Klang-Schreibweisen, Abkürzungen
  exakt). Ist der Satz vollständig und folgt Gebrabbel, wird hinter dem letzten Wort geschnitten.
  Ohne Whisper nur Dauerprüfung – dann `vidgen-setup`.
- „⚠ kein sauberer Take“ → Satz umformulieren (gleiche Aussage, einfacher Satzbau),
  dann `--only <id> --force`.

Aussprache: **`voice.lexicon`** im Storyboard, gilt nur für die Sprachausgabe
(Bildschirmtext und Skript bleiben). Bewährt für Deutsch:
`{"DNS": "Deh-Enn-Ess", "IP-Adresse": "Ih-Peh-Adresse", "Punkt de": "Punkt, Deh-Eh", "Nameserver": "Neim-Server"}`.
Komposita mit Bindestrich als eigener Eintrag (`IP` trifft `IP-Adresse` nicht).
`voice.params` setzt Node-Parameter, z. B. `{"temperature": 0.55}` (weniger Abschweifen).
Pro Szene überschreibt `scene.voice` (`seed`, `params`) die globalen Werte. Endet ein Satz zu
abrupt bzw. ohne fallende Betonung (typisch beim Schlusssatz): `{"params": {"cfg_weight": 0.3,
"exaggeration": 0.35}}` – ruhiger, letzte Silbe gedehnt, Tonhöhe fällt. Mehrere Seeds probieren.
Beim letzten Satz außerdem `padAfter` ≈ 1.5, damit das Video nicht direkt nach dem Wort endet.

Whisper prüft Vollständigkeit, nicht Klang – den User auf Stellen hinweisen,
die er anhören soll (Abkürzungen, Fremdwörter, Satzenden).
- Lautheit wird im Final-Render normalisiert (Skill `video-review`).
