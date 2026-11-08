---
name: video-review
description: Qualitätskontrolle eines gerenderten Erklärvideos – Kontaktbögen und Einzelframes ansehen, Timing, Lesbarkeit, Stilkonsistenz und Ton prüfen, Lautheit normalisieren und Fehler beheben. Verwenden in Phase 7 des Explainer-Workflows oder wenn ein Render geprüft/verbessert werden soll.
---

# Video-Review

Du kannst Videos nicht abspielen – du **siehst Frames**. Deshalb systematisch:

```bash
python3 tools/review.py projects/<slug>                 # Kontaktbogen je Szene + Gesamt
python3 tools/review.py projects/<slug> --video renders/draft.mp4
```

Ergebnis in `projects/<slug>/review/`: `contact_all.png` (1 Frame / 2 s),
`scene_<id>.png` (Anfang/Mitte/Ende je Szene) und `report.md` (Dauern, Lautheit, Auflösung).
Alle Bilder mit `Read` ansehen. Alternativ MCP `preview_media` für einzelne Clips.

## Checkliste

1. **Technik:** Auflösung/fps wie `storyboard.format`, Dauer ≈ `totalDuration` (±0,5 s),
   kein Schwarzbild am Anfang/Ende, Ton auf beiden Kanälen.
2. **Lesbarkeit:** Text nicht abgeschnitten, Kontrast ausreichend, nicht zu viel Text
   gleichzeitig, Text liegt nicht auf unruhigen Bildstellen.
3. **Konsistenz:** gleicher Bildstil in allen ComfyUI-Bildern, gleiche Figur sieht gleich aus.
4. **Artefakte:** KI-Fehler (Hände, Pseudotext im Bild, verzerrte Objekte) → Szene mit
   neuem Seed/Prompt neu erzeugen.
5. **Timing:** Bildwechsel passen zu Satzenden; keine Szene < 2,5 s.
6. **Ton:** Lautheit Ziel −16 LUFS (Web) – `report.md` nennt den Messwert;
   `tools/review.py --normalize` erzeugt `renders/final_norm.mp4`.

## Danach

Fehler selbst beheben (Storyboard → Asset → Code), erneut rendern, erneut prüfen.
Dem User erst zeigen, wenn die Checkliste sauber ist; verbleibende Kompromisse benennen.
