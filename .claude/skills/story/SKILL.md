---
name: story
description: Entwickelt Story und Sprechtext eines Erklärvideos aus einem Briefing – Kernaussage, Erzählbogen, Szenen-Grobstruktur und gesprochenes Skript. Verwenden in Phase 2 des Explainer-Workflows oder wenn der User an Skript, Story, Hook oder Formulierungen eines Videos arbeiten will.
---

# Story & Skript

Eingabe: `projects/<slug>/brief.md`. Ausgabe: `projects/<slug>/story.md`.

## Vorgehen

1. **Eine Kernaussage** in einem Satz („Nach dem Video weiß der Zuschauer, dass …“).
   Alles, was diese Aussage nicht stützt, fliegt raus.
2. **Bogen wählen** – passend zum Thema:
   - *Problem → Lösung → Nutzen → Handlung* (Produkt, Prozess)
   - *Frage → Intuition → Mechanismus → Beispiel → Merksatz* (Konzept, Wissenschaft)
   - *Vorher/Nachher* (Veränderung, Migration)
   - *Analogie zuerst* (abstrakte Technik: erst Alltagsbild, dann Übertragung)
3. **Hook in den ersten 5 Sekunden**: überraschende Zahl, konkrete Frage oder
   sichtbarer Konflikt. Kein „In diesem Video …“.
4. **Szenen-Grobstruktur**: 1 Gedanke pro Szene, 4–12 s pro Szene,
   bei 60–90 s also ca. 8–14 Szenen.
5. **Sprechtext schreiben** – für das Ohr, nicht fürs Auge:
   - Sätze ≤ 15 Wörter, aktive Verben, ein Fachbegriff pro Satz, beim ersten Mal erklärt.
   - Tempo: Deutsch ≈ **2,3 Wörter/s** (≈ 140 Wörter/min). Länge damit gegenrechnen.
   - Zahlen so schreiben, wie sie gesprochen werden („zweieinhalb Millionen“),
     Abkürzungen ausschreiben oder lautschriftlich angeben (TTS!).
   - Wiederholung der Kernaussage am Ende, dann eine konkrete Handlung (CTA).
6. **Visuelle Idee je Szene** in einem Halbsatz – *zeigen statt sagen*: Was sieht man,
   das der Text nicht sagt? (Diagramm, Metapher, Vergleich, Zahl groß.)

## Format von `story.md`

```markdown
# <Titel>
**Kernaussage:** …
**Zielgruppe:** …  **Länge:** ~75 s  **Bogen:** Frage → … 

| # | Beat | Sprechtext | Visuelle Idee |
|---|------|------------|---------------|
| 1 | Hook | „…“ | … |
```

Darunter: Wortzahl gesamt und geschätzte Dauer. Abschließend dem User die
Kernaussage, den Hook und die Dauer zeigen und Feedback einholen.
Rechercheaufgaben (Fakten, Zahlen) mit Quelle in einer Liste `## Quellen` belegen.
