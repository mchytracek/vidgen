---
name: voiceover
description: Vertont die Sprechtexte eines Storyboards – lokal (ChatterBox Multilingual in ComfyUI, Fallback macOS say) oder auf Wunsch mit ElevenLabs (Cloud, große Auswahl deutscher Stimmen), misst die Dauern und schreibt das Timing ins storyboard.json. Verwenden in Phase 4 des Explainer-Workflows, bei neuen Sprechtexten, Stimmwechsel oder Aussprache-Problemen.
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
| `elevenlabs` | sehr gut, große Auswahl deutscher Stimmen | **Cloud, kostet Credits**, API-Key; nur mit `--allow-cloud` |
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

## ElevenLabs (Cloud, nur auf Wunsch des Users)

Mehr und natürlichere deutsche Stimmen. **Sprechtexte verlassen den Rechner und kosten
Credits** – nur verwenden, wenn der User es ausdrücklich will (CLAUDE.md Regel 3).

1. API-Key liegt in `~/.config/vidgen/elevenlabs.env` (`ELEVENLABS_API_KEY=…`, chmod 600)
   oder in der Umgebung – **nie ins Repo, nie im Chat wiederholen**. Fehlt er: User bitten, ihn
   selbst dort einzutragen.
2. Stimme suchen und **Hörproben** laden (kostenlos):
   `python3 tools/elevenlabs.py voices --gender male --use-case informative_educational --previews`
   → `video/review/stimmen/NN_<name>.mp3`. Dem User 3–5 passende Kandidaten nennen
   (Alter, Akzent – für Deutsch „standard“/„german“ bevorzugen, Einsatzzweck) und wählen lassen.
   Aufpreis-Stimmen (`Aufpreis ×…`) nur mit Hinweis.
3. Übernehmen: `python3 tools/elevenlabs.py add <public_owner_id> <voice_id> --name "…"`, dann
   `python3 tools/elevenlabs.py use <voice_id>` (setzt `voice.backend = elevenlabs`,
   `voice.elevenlabs.{voiceId, model, settings}`). Eigene/geklonte Stimmen: `elevenlabs.py mine`.
4. Kosten zeigen: `python3 tools/tts.py` (ohne Flag) nennt Zeichen und freie Credits und bricht ab.
   **Erst nach Zustimmung** `python3 tools/tts.py --allow-cloud`. Erst eine Szene
   (`--only s01 --allow-cloud`) anhören lassen, dann den Rest.

Pro Szene ein Aufruf; die Nachbarszenen gehen als `previous_text`/`next_text` mit (natürliche
Übergänge). Prüfung wie bei ChatterBox (Whisper, Sprechtempo), bis zu 3 Takes – jeder kostet.
`voice.lexicon` gilt auch hier; `seed` macht Takes reproduzierbar (best effort).

| Einstellung (`voice.elevenlabs.settings`) | Wirkung |
|---|---|
| `stability` 0.3–0.8 | höher = gleichmäßiger, sachlicher; niedriger = lebendiger, schwankender |
| `similarity_boost` 0.75 | Nähe zur Originalstimme |
| `style` 0–0.4 | Ausdruck/Betonung (0 = neutral, stabiler) |
| `speed` 0.9–1.1 | Sprechtempo (Ziel ≈ 2,3 Wörter/s) |

Modell (`voice.elevenlabs.model`): `eleven_multilingual_v2` (Default, am stabilsten bei langen
Texten), `eleven_v3`/`eleven_v4` (ausdrucksstärker), `eleven_flash_v2_5` (halber Preis).
Pro Szene: `scene.voice.elevenlabs.settings` (z. B. ruhigerer Schlusssatz: `{"stability": 0.75}`).
Rechte: Stimmen aus der Bibliothek sind für kommerzielle Nutzung im Rahmen des ElevenLabs-Abos
lizenziert – bei Kundenprojekten Abo-Stufe prüfen.

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

**Eigennamen** (Hauptfigur, Firma, Produkt) kommen oft in fast jedem Satz vor – Aussprache
nicht raten, sondern Hörproben vom User wählen lassen:
`python3 tools/tts.py --try "Tobi=Tobie,Tohbie,Tohbi"` → `review/aussprache/alle.mp3`
(n Pieptöne vor Variante n, Variante 1 = ohne Lexikon). Die Wahl ins `voice.lexicon`,
Genitiv/Plural eigens („Tobis“: „Tohbies“). Bewährt für Deutsch: langes i am Ende mit „ie“,
Betonung/Länge auf der ersten Silbe mit Dehnungs-h („Tobi“ → „Tohbie“). Bindestriche
(„Toh-bie“) bringen ChatterBox ins Stolpern.

Whisper prüft Vollständigkeit, nicht Klang – den User auf Stellen hinweisen,
die er anhören soll (Abkürzungen, Fremdwörter, Satzenden).
- Lautheit wird im Final-Render normalisiert (Skill `video-review`).
