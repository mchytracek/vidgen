#!/usr/bin/env python3
"""Vertont die Sprechtexte eines Storyboards und misst das Timing.

  python3 tools/tts.py   # Backend aus storyboard.voice
  python3 tools/tts.py --backend say        # Entwurf mit macOS-Stimme
  python3 tools/tts.py --only s02 --force

Backends:
  comfyui-chatterbox  ChatterBox Multilingual in ComfyUI (Custom Node nötig, Referenzstimme)
  say                 macOS-Sprachausgabe (Entwurf, keine Abhängigkeiten)
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from _common import (VOICE_HOME, WORKFLOWS, comfy, die, load_sb, project_dir, run, save_sb,
                     select_scenes, voice_file)

# Slots nach Installation von ComfyUI_Fill-ChatterBox mit list_workflow_slots verifizieren!
CHATTERBOX = {"file": "audio-chatterbox_tts_multilingual.json", "voice": "2.audio",
              "text": "1.text", "language": "1.language", "seed": "1.seed",
              "prefix": "3.filename_prefix"}


def tts_say(text: str, voice: str, dst_stem: Path) -> Path:
    with tempfile.TemporaryDirectory() as td:
        aiff = Path(td) / "a.aiff"
        cp = run(["say", "-v", voice, "-o", str(aiff), text])
        if cp.returncode:
            die(f"say: {cp.stderr} (Stimmen: say -v '?')")
        if shutil.which("ffmpeg"):
            out = dst_stem.with_suffix(".mp3")
            cp = run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(aiff), "-ar", "44100",
                      "-b:a", "192k", str(out)])
        else:
            out = dst_stem.with_suffix(".m4a")
            cp = run(["afconvert", "-f", "m4af", "-d", "aac", str(aiff), str(out)])
        if cp.returncode:
            die(f"Konvertierung: {cp.stderr}")
    return out


def drop_reference(work: Path) -> None:
    """Entfernt den LoadAudio-Node samt Link: ChatterBox nutzt dann seine eingebaute Stimme."""
    node_id = int(CHATTERBOX["voice"].split(".")[0])
    w = json.loads(work.read_text())
    dead = {l[0] for l in w["links"] if l[1] == node_id}
    w["nodes"] = [n for n in w["nodes"] if n["id"] != node_id]
    w["links"] = [l for l in w["links"] if l[0] not in dead]
    for n in w["nodes"]:
        for i in n.get("inputs", []):
            if i.get("link") in dead:
                i["link"] = None
    work.write_text(json.dumps(w, ensure_ascii=False, indent=2))


# Plausibilität je Satz (Deutsch ≈ 2,3 Wörter/s): außerhalb → anderer Seed.
WPS_RANGE = (1.5, 3.6)
MAX_GAP = 0.9          # längere Pause mitten im Satz = Aussetzer/Halluzination
MAX_TRIES = 8
SENTENCE_PAUSE = 0.3   # Atempause zwischen Sätzen


MIN_CHUNK_WORDS = 7    # kürzere Sätze lässt ChatterBox oft nicht enden → mit Nachbarsatz verbinden


def split_sentences(text: str) -> list[str]:
    """Sätze, wobei zu kurze Sätze mit dem folgenden (am Ende: vorherigen) verbunden werden."""
    parts = [p for p in re.split(r"(?<=[.?!])\s+", text.strip()) if p]
    chunks: list[str] = []
    buf = ""
    for p in parts:
        buf = f"{buf} {p}".strip()
        if len(buf.split()) >= MIN_CHUNK_WORDS:
            chunks.append(buf)
            buf = ""
    if buf:
        if chunks:
            chunks[-1] = f"{chunks[-1]} {buf}"
        else:
            chunks.append(buf)
    return chunks


def ffmpeg_ok() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def audio_seconds(path: Path) -> float:
    cp = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    return float(cp.stdout.strip() or 0)


def trim_silence(src: Path, dst: Path) -> None:
    """Stille (und leise Reste) an Anfang und Ende entfernen, als 24-kHz-Mono-WAV."""
    f = ("silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.08,"
         "areverse,silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.2,areverse,"
         "apad=pad_dur=0.1")
    cp = run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ac", "1", "-ar", "24000", "-af", f, str(dst)])
    if cp.returncode:
        die(f"ffmpeg trim: {cp.stderr}")


def drop_trailing_blob(src: Path, dst: Path, gap: float = 0.3, max_blob: float = 0.6) -> bool:
    """Kurzes Geräusch (Atmer, Klick, Schmatzer) nach dem letzten Wort entfernen.

    Sucht den letzten Schallblock (> −45 dB); liegt davor eine Stille ≥ `gap` s (< −50 dB)
    und ist der Block kürzer als `max_blob` s, wird kurz nach Beginn der Stille geschnitten.
    Ein echtes letztes Wort würde danach in der Whisper-Prüfung als fehlend auffallen.
    """
    import math
    import struct
    sr, win = 16000, 800  # 50-ms-Fenster
    raw = run_bytes(["ffmpeg", "-v", "error", "-i", str(src), "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"])
    n = len(raw) // 2
    if n < win * 4:
        return False
    s = struct.unpack(f"<{n}h", raw[: n * 2])
    db = [20 * math.log10(math.sqrt(sum(x * x for x in s[i:i + win]) / win) / 32768 + 1e-9)
          for i in range(0, n - win + 1, win)]
    loud = [i for i, d in enumerate(db) if d > -45]
    if not loud:
        return False
    last, need = loud[-1], round(gap / 0.05)
    j = last
    while j >= need and not all(d < -50 for d in db[j - need:j]):
        j -= 1
    if j < need or (last - j + 1) * 0.05 >= max_blob:
        return False
    k = j - need  # Beginn der Stille
    if not any(d > -45 for d in db[:k]):
        return False  # davor keine Sprache – nichts abschneiden
    end = (k + 2) * 0.05  # 0,1 s Ausklang
    cp = run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-af",
              f"atrim=end={end:.3f},afade=t=out:st={max(0.0, end - 0.05):.3f}:d=0.05",
              *(["-ar", "44100", "-b:a", "192k"] if dst.suffix == ".mp3" else []), str(dst)])
    return cp.returncode == 0


def run_bytes(cmd: list[str]) -> bytes:
    return subprocess.run(cmd, capture_output=True).stdout


def longest_gap(path: Path) -> float:
    cp = run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "silencedetect=n=-40dB:d=0.3", "-f", "null", "-"])
    gaps = [float(x) for x in re.findall(r"silence_duration: ([0-9.]+)", cp.stderr)]
    return max(gaps, default=0.0)


WHISPER_MODEL = Path(os.environ.get(
    "VIDGEN_WHISPER_MODEL", Path.home() / ".local/share/whisper-cpp/ggml-large-v3-turbo-q5_0.bin"))


def apply_lexicon(text: str, lexicon: dict | None) -> str:
    """Aussprache-Lexikon (voice.lexicon) anwenden – nur für die Sprachausgabe, nicht für Bildschirmtext."""
    for src, dst in (lexicon or {}).items():
        text = re.sub(rf"(?<![\w-]){re.escape(src)}(?![\w-])", dst, text, flags=re.IGNORECASE)
    return text


def stt_available() -> bool:
    return shutil.which("whisper-cli") is not None and WHISPER_MODEL.is_file()


def transcribe_words(path: Path, lang: str = "de") -> list[tuple[str, float, float]]:
    """Whisper mit Zeitstempel je Wort: [(wort, start_s, ende_s), …]."""
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "a.wav"
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-ar", "16000", "-ac", "1", str(wav)])
        cp = run(["whisper-cli", "-m", str(WHISPER_MODEL), "-l", lang, "-np", "-ml", "1", "-sow", "-f", str(wav)])
    out = []
    for line in cp.stdout.splitlines():
        m = re.match(r"\[(\d+):(\d+):([\d.]+) --> (\d+):(\d+):([\d.]+)\][ \t]*(.*)$", line.strip())
        if not m or not m.group(7).strip():
            continue
        h1, m1, s1, h2, m2, s2, w = m.groups()
        out.append((w.strip(), int(h1) * 3600 + int(m1) * 60 + float(s1), int(h2) * 3600 + int(m2) * 60 + float(s2)))
    return out


def transcribe(path: Path, lang: str = "de") -> str:
    return " ".join(w for w, _, _ in transcribe_words(path, lang))


def lexicon_may_explain(problems: list[str], lexicon: dict | None) -> bool:
    """Lautschrift-Fassung nur gelten lassen, wenn ausschließlich Lexikon-Wörter fehlen – nie bei Abkürzungen."""
    lex_words = {w for k in (lexicon or {}) if not re.fullmatch(r"[A-ZÄÖÜ]{2,}", k) for w in _words(k)}
    missing = [w for p in problems if p.startswith("fehlt: ") for w in p[7:].split(", ")]
    only_missing = all(p.startswith("fehlt: ") for p in problems)
    return only_missing and bool(missing) and set(missing) <= lex_words


def cut_after_last_word(src: Path, dst: Path, words: list[tuple[str, float, float]],
                        sentence: str, spoken: str, lexicon: dict | None) -> bool:
    """Schneidet Gebrabbel nach dem Satzende ab: am Ende des kürzesten Präfixes, das das Skript vollständig enthält."""
    for k in range(len(words)):
        prefix = " ".join(w for w, _, _ in words[:k + 1])
        ok, probs = check_transcript(sentence, prefix)
        if not ok and spoken != sentence and lexicon_may_explain(probs, lexicon):
            ok = check_transcript(spoken, prefix)[0]
        if ok:
            end = words[k][2] + 0.15
            cp = run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-t", f"{end:.3f}",
                      "-af", "afade=t=out:st={:.3f}:d=0.1".format(max(0.0, end - 0.1)), str(dst)])
            return cp.returncode == 0
    return False


def _words(text: str) -> list[str]:
    text = re.sub(r"(?<=[a-zA-ZäöüÄÖÜ])\.(?=[a-zA-Z])", " punkt ", text)  # „beispiel.de“ = gesprochen „punkt“
    return re.findall(r"[a-zäöüß0-9]+", text.lower().replace("-", " "))


def koelner_phonetik(word: str) -> str:
    """Kölner Phonetik: gleich klingende deutsche Wörter → gleicher Code (Road ≈ Root, Haus ≠ raus)."""
    w = word.lower().replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "s")
    w = re.sub(r"[^a-z]", "", w)
    codes = []
    for i, ch in enumerate(w):
        prev = w[i - 1] if i else "#"
        nxt = w[i + 1] if i + 1 < len(w) else "#"  # „#“ statt "", weil "" in "abc" immer True ist
        if ch in "aeijouy":
            c = "0"
        elif ch == "h":
            c = ""
        elif ch == "b" or (ch == "p" and nxt != "h"):
            c = "1"
        elif ch in "dt":
            c = "8" if nxt in "csz" else "2"
        elif ch in "fvw" or (ch == "p" and nxt == "h"):
            c = "3"
        elif ch in "gkq":
            c = "4"
        elif ch == "c":
            if i == 0:
                c = "4" if nxt in "ahkloqrux" else "8"
            else:
                c = "8" if prev in "sz" or nxt not in "ahkoqux" else "4"
        elif ch == "x":
            c = "8" if prev in "ckq" else "48"
        elif ch == "l":
            c = "5"
        elif ch in "mn":
            c = "6"
        elif ch == "r":
            c = "7"
        elif ch in "sz":
            c = "8"
        else:
            c = ""
        codes.append(c)
    out = ""
    for c in "".join(codes):
        if not out or c != out[-1]:
            out += c
    return out[0] + out[1:].replace("0", "") if out else ""


def _similar(a: str, b: str) -> bool:
    if len(a) >= 4 and len(b) >= 3 and koelner_phonetik(a) == koelner_phonetik(b):
        return True
    if len(a) <= 3 and (not b or a[0] != b[0]):  # „dir“ ≠ „ihr“, aber „von“ ≈ „vom“
        return False
    need = 0.8 if len(a) > 3 else 0.66
    return difflib.SequenceMatcher(None, a, b).ratio() >= need


_ONES = ["null", "eins", "zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht", "neun", "zehn",
         "elf", "zwölf", "dreizehn", "vierzehn", "fünfzehn", "sechzehn", "siebzehn", "achtzehn", "neunzehn"]
_TENS = ["", "", "zwanzig", "dreißig", "vierzig", "fünfzig", "sechzig", "siebzig", "achtzig", "neunzig"]


def zahl_de(n: int) -> str:
    """Ganzzahl → deutsches Zahlwort (bis 999 999 999), z. B. 37 → „siebenunddreißig“."""
    if n < 20:
        return _ONES[n]
    if n < 100:
        one = "ein" if n % 10 == 1 else _ONES[n % 10]
        return (one + "und" if n % 10 else "") + _TENS[n // 10]
    if n < 1000:
        rest = n % 100
        return ("ein" if n // 100 == 1 else _ONES[n // 100]) + "hundert" + (zahl_de(rest) if rest else "")
    if n < 1_000_000:
        rest = n % 1000
        head = "ein" if n // 1000 == 1 else zahl_de(n // 1000)
        return head + "tausend" + (zahl_de(rest) if rest else "")
    if n < 1_000_000_000:
        mio, rest = divmod(n, 1_000_000)
        head = "eine million" if mio == 1 else zahl_de(mio) + " millionen"
        return head + (" " + zahl_de(rest) if rest else "")
    return str(n)


def _spell_numbers(words: list[str]) -> list[str]:
    """Whisper schreibt Zahlen als Ziffern („37“) – für den Vergleich mit dem Skript ausschreiben."""
    out: list[str] = []
    for w in words:
        out.extend(zahl_de(int(w)).split() if w.isdigit() and len(w) <= 9 else [w])
    return out


def check_transcript(expected: str, heard: str) -> tuple[bool, list[str]]:
    """Jedes Wort (≥ 2 Zeichen) des Skripts muss in Reihenfolge vorkommen; keine Wiederholung, nichts Überzähliges."""
    exp, got = _spell_numbers(_words(expected)), _spell_numbers(_words(heard))
    acronyms = {a.lower() for a in re.findall(r"\b[A-ZÄÖÜ]{2,}\b", expected)}  # DNS, IP: exakt prüfen
    missing, cur = [], 0
    for w in exp:
        if len(w) < 2:
            continue
        hit = None
        if len(w) == 2:  # kurze Wörter nur in unmittelbarer Nähe suchen (oft in Komposita verschluckt)
            for j in range(cur, min(cur + 3, len(got))):
                if _similar(w, got[j]) or w in got[j]:
                    hit = j
                    break
            if hit is None:
                missing.append(w)
            continue
        for j in range(cur, len(got)):
            for n in (1, 2, 3):
                if j + n > len(got):
                    break
                c = "".join(got[j:j + n])
                if (c == w) if w in acronyms else (_similar(w, c) or (len(w) >= 4 and w in c)):
                    hit = j + n - 1  # Position des letzten beteiligten Wortes
                    break
            if hit is not None:
                break
        if hit is None:
            missing.append(w)
        else:
            cur = hit  # gleiche Position darf erneut passen (Komposita wie „beispielpunkt“)
    problems = [f"fehlt: {', '.join(missing)}"] if missing else []
    if len(got) > len(exp) * 1.25 + 1:
        problems.append(f"zu viele Wörter ({len(got)} statt {len(exp)})")
    tail = " ".join(got[-3:])
    if len(got) >= 6 and tail in " ".join(got[:-3]):
        problems.append(f"Wiederholung: „{tail}“")
    return not problems, problems


def chatterbox_once(pdir: Path, sb: dict, key: str, text: str, ref_name: str | None, seed: int) -> Path:
    v = sb.get("voice") or {}
    work = pdir / ".work" / f"{key}_tts.json"
    work.parent.mkdir(exist_ok=True)
    shutil.copyfile(WORKFLOWS / CHATTERBOX["file"], work)
    slots = [f"{CHATTERBOX['voice']}={ref_name}"] if ref_name else []
    if not ref_name:
        drop_reference(work)
    env = comfy("workflow", "set-slot", str(work), *slots,
                f"{CHATTERBOX['text']}={text}",
                f"{CHATTERBOX['language']}={v.get('language', 'German (de)')}",
                f"{CHATTERBOX['seed']}={seed}",
                f"{CHATTERBOX['prefix']}=vidgen/{sb['slug']}/{key}_vo",
                # optionale Sampling-Parameter aus voice.params, z. B. {"temperature": 0.55}
                *[f"{CHATTERBOX['text'].split('.')[0]}.{k}={val}" for k, val in (v.get("params") or {}).items()])
    if not env["ok"]:
        die(f"set-slot: {env['error']}\n→ Custom Node installiert? Slots mit "
            f"`comfy --json workflow slots {work}` prüfen und CHATTERBOX in tools/tts.py anpassen.")
    env = comfy("run", "--workflow", str(work), "--wait", "--timeout", "900", timeout=960)
    if not env["ok"] or (env.get("data") or {}).get("status") != "completed":
        die(f"TTS {key} fehlgeschlagen: {env.get('error') or env.get('data')}")
    return Path(env["data"]["outputs"][0])


def with_scene_voice(sb: dict, s: dict) -> dict:
    """Szenen-Override `scene.voice` ({"seed": …, "params": {…}}) über `storyboard.voice` legen.

    Beispiel: ruhigeres, am Ende fallendes Schluss-Statement mit
    {"seed": 2025, "params": {"cfg_weight": 0.3, "exaggeration": 0.35}}.
    """
    sv = s.get("voice") or {}
    if not sv:
        return sb
    v = sb.get("voice") or {}
    merged = {**v, **{k: val for k, val in sv.items() if k != "params"},
              "params": {**(v.get("params") or {}), **(sv.get("params") or {})}}
    return {**sb, "voice": merged}


def tts_chatterbox(pdir: Path, sb: dict, s: dict, ref_name: str | None, dst_stem: Path) -> Path:
    """Satzweise erzeugen, Stille trimmen, Dauer/Aussetzer prüfen (sonst neuer Seed), zusammensetzen.

    ChatterBox Multilingual neigt bei mehreren Sätzen am Stück zu langen Pausen und
    Gebrabbel nach dem Satzende – einzeln erzeugte Sätze sind deutlich stabiler.
    """
    sb = with_scene_voice(sb, s)
    base_seed = int((sb.get("voice") or {}).get("seed", 1234))
    if not ffmpeg_ok():  # ohne ffmpeg: ein Take, ungeprüft
        src = chatterbox_once(pdir, sb, s["id"], s["narration"], ref_name, base_seed)
        out = dst_stem.with_suffix(src.suffix)
        shutil.copyfile(src, out)
        return out

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        pieces: list[Path] = []
        lexicon = (sb.get("voice") or {}).get("lexicon")
        use_stt = stt_available()
        if not use_stt:
            print("    Hinweis: whisper-cli/Modell fehlt – nur Dauerprüfung, Vollständigkeit ungeprüft")
        for i, sentence in enumerate(split_sentences(s["narration"])):
            spoken = apply_lexicon(sentence, lexicon)
            words = len(sentence.split())
            best: tuple[float, Path] | None = None
            for t in range(MAX_TRIES):
                seed = base_seed + 1000 * t + i
                raw = chatterbox_once(pdir, sb, f"{s['id']}_{i}", spoken, ref_name, seed)
                cut = tdp / f"{i}_{t}.wav"
                trim_silence(raw, cut)
                deblob = tdp / f"{i}_{t}_db.wav"
                if drop_trailing_blob(cut, deblob):
                    cut = deblob
                dur, gap = audio_seconds(cut), longest_gap(cut)
                wps = words / dur if dur else 99
                problems = []
                if not WPS_RANGE[0] <= wps <= WPS_RANGE[1]:
                    problems.append(f"{wps:.1f} W/s")
                if gap > MAX_GAP:
                    problems.append(f"Pause {gap:.2f} s")
                heard = ""
                if use_stt:
                    lang = (sb.get("language") or "de")[:2]
                    words_t = transcribe_words(cut, lang)
                    heard = " ".join(w for w, _, _ in words_t)
                    ok_text, probs = check_transcript(sentence, heard)
                    if not ok_text and spoken != sentence and lexicon_may_explain(probs, lexicon):
                        ok_text = check_transcript(spoken, heard)[0]  # Lautschrift-Fassung erkannt
                    if not ok_text or problems:
                        # Rettungsversuch: Satz vollständig, danach Gebrabbel/Pause → hinter dem letzten Wort schneiden
                        salvaged = tdp / f"{i}_{t}_cut.wav"
                        if cut_after_last_word(cut, salvaged, words_t, sentence, spoken, lexicon):
                            d2, g2 = audio_seconds(salvaged), longest_gap(salvaged)
                            w2 = words / d2 if d2 else 99
                            if WPS_RANGE[0] <= w2 <= WPS_RANGE[1] and g2 <= MAX_GAP:
                                cut, dur, gap, wps = salvaged, d2, g2, w2
                                problems, ok_text = [], True
                                heard += "  → hinter dem Satzende geschnitten"
                    if not ok_text:
                        problems += probs
                ok = not problems
                print(f"    Satz {i + 1} Take {t + 1}: {dur:.2f} s – {'✔' if ok else '✖ ' + '; '.join(problems)}"
                      + (f"\n      gehört: {heard}" if heard else ""))
                score = len(problems) * 10 + abs(wps - 2.3) + max(0.0, gap - MAX_GAP) * 3
                if best is None or score < best[0]:
                    best = (score, cut)
                if ok:
                    break
            else:
                print(f"    ⚠ Satz {i + 1}: kein sauberer Take nach {MAX_TRIES} Versuchen – bester genommen, bitte anhören")
            pieces.append(best[1])

        pause = tdp / "pause.wav"
        run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-t", str(SENTENCE_PAUSE),
             "-i", "anullsrc=r=24000:cl=mono", str(pause)])
        lst = tdp / "list.txt"
        seq = []
        for j, p in enumerate(pieces):
            if j:
                seq.append(pause)
            seq.append(p)
        lst.write_text("".join(f"file '{p}'\n" for p in seq))
        out = dst_stem.with_suffix(".mp3")
        cp = run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                  "-ar", "44100", "-b:a", "192k", str(out)])
        if cp.returncode:
            die(f"ffmpeg concat: {cp.stderr}")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", dest="project", help="Videoordner (Default: video/)")
    ap.add_argument("--backend", choices=["comfyui-chatterbox", "say"])
    ap.add_argument("--only")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    pdir = project_dir(a.project)
    sb = load_sb(pdir)
    voice = sb.get("voice") or {}
    backend = a.backend or voice.get("backend") or "say"
    audio_dir = pdir / "assets" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    ref_name = None
    if backend == "comfyui-chatterbox":
        ref = voice.get("reference")
        if ref:  # ohne Referenz: eingebaute ChatterBox-Stimme
            ref_path = voice_file(ref)
            if not ref_path:
                die(f"voice.reference nicht gefunden: {ref} – weder im Repo noch in {VOICE_HOME}/ "
                    f"(Referenzstimmen werden nicht versioniert, Datei dort ablegen)")
            env = comfy("upload", str(ref_path), "--overwrite")
            if not env["ok"]:
                die(f"Upload Referenzstimme: {env['error']}")
            ref_name = Path(ref).name
        else:
            print("Hinweis: keine voice.reference – ChatterBox nutzt seine eingebaute Stimme.")

    for s in select_scenes(sb, a.only):
        cur = (s.get("assets") or {}).get("audio")
        if cur and (pdir / "assets" / cur).exists() and not a.force:
            continue
        stem = audio_dir / s["id"]
        print(f"{s['id']}: {backend} – {s['narration'][:60]}…")
        if backend == "say":
            out = tts_say(s["narration"], voice.get("sayVoice", "Anna"), stem)
        else:
            out = tts_chatterbox(pdir, sb, s, ref_name, stem)
        s.setdefault("assets", {})["audio"] = f"audio/{out.name}"
        save_sb(pdir, sb)

    subprocess.run(["python3", str(Path(__file__).with_name("storyboard.py")), "timing", "--dir", str(pdir)], check=False)


if __name__ == "__main__":
    main()
