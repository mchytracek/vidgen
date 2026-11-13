#!/usr/bin/env python3
"""Storyboard-Werkzeug für video/storyboard.json: validate | show | timing | sync.

  python3 tools/storyboard.py validate
  python3 tools/storyboard.py show
  python3 tools/storyboard.py timing     # misst Audio, setzt duration
  python3 tools/storyboard.py sync       # kopiert storyboard.json nach assets/
  (alle mit optional --dir <videoordner>)
"""
from __future__ import annotations

import argparse
import re
import shutil

from _common import die, load_sb, media_duration, project_dir, save_sb

KINDS = {"image", "clip", "code", "hyperframes", "tesseract"}
COMPOSITORS = {"remotion", "hyperframes", "tesseract"}
STATUSES = ["brief", "story", "storyboard", "voice", "assets", "scenes", "review", "done"]
WORDS_PER_SEC = 2.3


def validate(sb: dict) -> list[str]:
    errs: list[str] = []
    for key in ("title", "slug", "language", "format", "style", "compositor", "scenes"):
        if key not in sb:
            errs.append(f"Pflichtfeld fehlt: {key}")
    if errs:
        return errs
    if sb["compositor"] not in COMPOSITORS:
        errs.append(f"compositor muss einer von {sorted(COMPOSITORS)} sein")
    if sb.get("status") and sb["status"] not in STATUSES:
        errs.append(f"status unbekannt: {sb['status']}")
    for k in ("width", "height", "fps"):
        if not isinstance(sb["format"].get(k), int):
            errs.append(f"format.{k} muss Ganzzahl sein")
    if not sb["style"].get("imagePrompt"):
        errs.append("style.imagePrompt fehlt")
    ids = set()
    for i, s in enumerate(sb["scenes"]):
        where = f"scenes[{i}] ({s.get('id', '?')})"
        sid = s.get("id", "")
        if not re.fullmatch(r"s\d{2,3}[a-z]?", sid):
            errs.append(f"{where}: id muss wie s01, s02a … aussehen")
        if sid in ids:
            errs.append(f"{where}: doppelte id")
        ids.add(sid)
        if not s.get("narration", "").strip():
            errs.append(f"{where}: narration leer")
        v = s.get("visual") or {}
        kind = v.get("kind")
        if kind not in KINDS:
            errs.append(f"{where}: visual.kind muss einer von {sorted(KINDS)} sein")
        if kind in ("image", "clip") and not v.get("prompt"):
            errs.append(f"{where}: visual.prompt fehlt für kind={kind}")
        if kind == "clip" and not v.get("motionPrompt"):
            errs.append(f"{where}: visual.motionPrompt fehlt für kind=clip")
        if kind == "code" and not v.get("component"):
            errs.append(f"{where}: visual.component fehlt für kind=code")
        if v.get("component") == "ScreenshotFocus":
            errs += _check_screenshot(s, where, kind)
        char = v.get("character")
        if char:
            if not sb["style"].get("characterRef"):
                errs.append(f"{where}: visual.character gesetzt, aber style.characterRef fehlt (tools/character.py)")
            if kind not in ("image", "clip"):
                errs.append(f"{where}: visual.character nur für kind=image/clip")
            if isinstance(char, dict) and set(char) - {"wear", "action", "seed"}:
                errs.append(f"{where}: visual.character kennt nur wear, action, seed")
    return errs


def _check_screenshot(s: dict, where: str, kind) -> list[str]:
    errs = []
    if kind != "code":
        errs.append(f"{where}: ScreenshotFocus braucht kind=code (sonst generiert ComfyUI ein Bild)")
    if not (s.get("assets") or {}).get("image"):
        errs.append(f"{where}: ScreenshotFocus braucht assets.image (z. B. \"screens/01-login.png\")")
    foci = (s["visual"].get("props") or {}).get("focus") or []
    for i, f in enumerate(foci if isinstance(foci, list) else [foci]):
        try:
            x, y, w, h = (float(f[k]) for k in ("x", "y", "w", "h"))
        except (KeyError, TypeError, ValueError):
            errs.append(f"{where}: focus[{i}] braucht x, y, w, h (Anteile 0–1)")
            continue
        if min(x, y) < 0 or w <= 0 or h <= 0 or x + w > 1.001 or y + h > 1.001:
            errs.append(f"{where}: focus[{i}] liegt außerhalb des Bildes (Anteile 0–1, x+w ≤ 1, y+h ≤ 1)")
    return errs



def cmd_validate(a):
    pdir = project_dir(a.project)
    errs = validate(load_sb(pdir))
    if errs:
        print("\n".join(f"✖ {e}" for e in errs))
        raise SystemExit(1)
    print(f"✔ {pdir.name}: storyboard.json gültig")


def cmd_show(a):
    pdir = project_dir(a.project)
    sb = load_sb(pdir)
    total_words = 0
    print(f"# {sb['title']}  [{sb.get('status', '?')}]  {sb['format']['width']}x{sb['format']['height']}"
          f"@{sb['format']['fps']}  compositor={sb['compositor']}\n")
    print(f"{'id':5} {'kind':11} {'dauer':>6}  {'assets':14} sprechtext")
    for s in sb["scenes"]:
        words = len(s["narration"].split())
        total_words += words
        dur = s.get("duration") or round(words / WORDS_PER_SEC + s.get("padAfter", 0.4), 1)
        mark = "" if s.get("duration") else "~"
        have = ",".join(k for k in ("audio", "image", "clip", "render") if (s.get("assets") or {}).get(k))
        print(f"{s['id']:5} {s['visual']['kind']:11} {mark}{dur:>5}s  {have or '-':14} {s['narration'][:60]}")
    est = total_words / WORDS_PER_SEC
    print(f"\nWörter: {total_words}  ≈ {est:.0f} s Sprechzeit  "
          f"| gemessen: {sb.get('totalDuration') or '–'} s  | Ziel: {sb.get('targetDuration') or '–'} s")


def cmd_timing(a):
    pdir = project_dir(a.project)
    sb = load_sb(pdir)
    total = 0.0
    missing = []
    for s in sb["scenes"]:
        rel = (s.get("assets") or {}).get("audio")
        if not rel or not (pdir / "assets" / rel).exists():
            missing.append(s["id"])
            continue
        ad = media_duration(pdir / "assets" / rel)
        s["audioDuration"] = round(ad, 3)
        s["duration"] = round(max(ad + s.get("padAfter", 0.4), s.get("minDuration", 2.5)), 3)
        total += s["duration"]
    if missing:
        die(f"Audio fehlt für: {', '.join(missing)} – erst tools/tts.py laufen lassen")
    sb["totalDuration"] = round(total, 2)
    save_sb(pdir, sb)
    sync(pdir, sb)
    tgt = sb.get("targetDuration")
    note = f" (Ziel {tgt} s, Abweichung {100 * (total - tgt) / tgt:+.0f} %)" if tgt else ""
    print(f"✔ Timing gesetzt: {total:.1f} s gesamt{note}")


def sync(pdir, sb=None):
    sb = sb or load_sb(pdir)
    (pdir / "assets").mkdir(exist_ok=True)
    shutil.copyfile(pdir / "storyboard.json", pdir / "assets" / "storyboard.json")


def cmd_sync(a):
    pdir = project_dir(a.project)
    errs = validate(load_sb(pdir))
    if errs:
        die("Storyboard ungültig:\n" + "\n".join(errs))
    sync(pdir)
    print("✔ assets/storyboard.json aktualisiert")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("validate", cmd_validate), ("show", cmd_show), ("timing", cmd_timing), ("sync", cmd_sync)):
        p = sub.add_parser(name)
        p.add_argument("--dir", dest="project", help="Videoordner (Default: video/)")
        p.set_defaults(fn=fn)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
