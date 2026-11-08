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
import shutil
import subprocess
import tempfile
from pathlib import Path

from _common import REPO, WORKFLOWS, comfy, die, load_sb, project_dir, run, save_sb, select_scenes

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


def tts_chatterbox(pdir: Path, sb: dict, s: dict, ref_name: str, dst_stem: Path) -> Path:
    v = sb.get("voice") or {}
    work = pdir / ".work" / f"{s['id']}_tts.json"
    work.parent.mkdir(exist_ok=True)
    shutil.copyfile(WORKFLOWS / CHATTERBOX["file"], work)
    env = comfy("workflow", "set-slot", str(work),
                f"{CHATTERBOX['voice']}={ref_name}",
                f"{CHATTERBOX['text']}={s['narration']}",
                f"{CHATTERBOX['language']}={v.get('language', 'German (de)')}",
                f"{CHATTERBOX['seed']}={v.get('seed', 1234)}",
                f"{CHATTERBOX['prefix']}=vidgen/{sb['slug']}/{s['id']}_vo")
    if not env["ok"]:
        die(f"set-slot: {env['error']}\n→ Custom Node installiert? Slots mit "
            f"`comfy --json workflow slots {work}` prüfen und CHATTERBOX in tools/tts.py anpassen.")
    env = comfy("run", "--workflow", str(work), "--wait", "--timeout", "900", timeout=960)
    if not env["ok"] or (env.get("data") or {}).get("status") != "completed":
        die(f"TTS {s['id']} fehlgeschlagen: {env.get('error') or env.get('data')}")
    src = Path(env["data"]["outputs"][0])
    out = dst_stem.with_suffix(src.suffix)
    shutil.copyfile(src, out)
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
        if not ref or not (REPO / ref).is_file():
            die("voice.reference fehlt oder Datei nicht gefunden (z. B. voices/meine-stimme.wav)")
        env = comfy("upload", str(REPO / ref), "--overwrite")
        if not env["ok"]:
            die(f"Upload Referenzstimme: {env['error']}")
        ref_name = Path(ref).name

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
