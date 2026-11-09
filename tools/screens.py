#!/usr/bin/env python3
"""Eigene Screenshots für Produktvideos: prüfen, Koordinatenraster, Fokus-Stills.

Screenshots liegen in video/assets/screens/ und werden per
  "visual": {"kind": "code", "component": "ScreenshotFocus", "props": {...}},
  "assets": {"image": "screens/02-dashboard.png"}
in Szenen eingebunden.

  python3 tools/screens.py check             # Größen/Format, Zuordnung zu Szenen, fehlende Dateien
  python3 tools/screens.py grid [datei …]    # Raster-Kopien nach review/screens/ (Koordinaten ablesen)
  python3 tools/screens.py stills [--only s03]   # Remotion-Stills je Fokus → review/screens/
  (alle mit optional --dir <videoordner>)

Raster: dünne Linien alle 5 %, deutliche alle 10 %, dicke Linien bei 50 %.
Koordinaten in ScreenshotFocus sind Anteile (0–1) der Bildbreite/-höhe, Ursprung oben links.
"""
from __future__ import annotations

import argparse
import json
import shutil

from _common import die, load_sb, project_dir, run, select_scenes

EXT = {".png", ".jpg", ".jpeg", ".webp"}
VIDEO_EXT = {".mp4", ".mov", ".webm"}
WORDS_PER_SEC = 2.3
MOVE = 0.9  # muss zu ScreenshotFocus.tsx passen


def dims(path) -> tuple[int, int] | None:
    if not shutil.which("ffprobe"):
        die("ffprobe fehlt (brew install ffmpeg)")
    cp = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
              "stream=width,height", "-of", "json", str(path)])
    try:
        st = json.loads(cp.stdout)["streams"][0]
        return int(st["width"]), int(st["height"])
    except (KeyError, IndexError, ValueError):
        return None


def screen_files(pdir):
    sdir = pdir / "assets" / "screens"
    if not sdir.is_dir():
        return []
    return sorted(p for p in sdir.iterdir() if p.suffix.lower() in EXT | VIDEO_EXT)


def cmd_check(a):
    pdir = project_dir(a.project)
    sb = load_sb(pdir)
    fw, fh = sb["format"]["width"], sb["format"]["height"]
    target = fw / fh
    files = screen_files(pdir)
    used: dict[str, list[str]] = {}
    for s in sb["scenes"]:
        for key in ("image", "clip"):
            rel = (s.get("assets") or {}).get(key) or ""
            if rel.startswith("screens/"):
                used.setdefault(rel, []).append(s["id"])
    problems = 0
    if not files:
        print("Keine Screenshots in assets/screens/.")
    for f in files:
        rel = f"screens/{f.name}"
        d = dims(f)
        note = []
        if not d:
            note.append("Größe nicht lesbar")
        else:
            w, h = d
            if abs(w / h - target) / target > 0.02:
                note.append(f"Seitenverhältnis {w / h:.2f} ≠ Video {target:.2f} → nur mit framed=true sauber")
            if w < fw * 0.88:
                note.append(f"schmaler als {int(fw * 0.88)} px → wird hochskaliert, Zoom unscharf")
        scenes = ",".join(used.get(rel, [])) or "– (unbenutzt)"
        size = f"{d[0]}x{d[1]}" if d else "?"
        print(f"{'⚠' if note else '✔'} {f.name:32} {size:>10}  Szenen: {scenes}")
        for n in note:
            print(f"    {n}")
        problems += bool(note)
    missing = [(rel, ids) for rel, ids in used.items() if not (pdir / "assets" / rel).exists()]
    for rel, ids in missing:
        print(f"✖ {rel} fehlt (benutzt in {','.join(ids)})")
    if missing:
        raise SystemExit(1)
    print(f"\n{len(files)} Datei(en), {problems} mit Hinweisen. Video: {fw}x{fh}")


def cmd_grid(a):
    if not shutil.which("ffmpeg"):
        die("ffmpeg fehlt (brew install ffmpeg)")
    pdir = project_dir(a.project)
    sdir = pdir / "assets" / "screens"
    files = [sdir / n for n in a.files] if a.files else [f for f in screen_files(pdir) if f.suffix.lower() in EXT]
    if not files:
        die("Keine Screenshots gefunden (assets/screens/)")
    out = pdir / "review" / "screens"
    out.mkdir(parents=True, exist_ok=True)
    vf = ("drawgrid=w=iw/20:h=ih/20:t=1:c=magenta@0.35,"
          "drawgrid=w=iw/10:h=ih/10:t=2:c=magenta@0.8,"
          "drawgrid=w=iw/2:h=ih/2:t=5:c=red@0.9")
    for f in files:
        if not f.exists():
            die(f"{f} nicht gefunden")
        dst = out / f"{f.stem}_grid.png"
        cp = run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(f), "-vf", vf, "-frames:v", "1", str(dst)])
        if cp.returncode:
            die(f"ffmpeg: {cp.stderr[-800:]}")
        print(f"✔ {dst.relative_to(pdir)}")
    print("Raster: dünn = 5 %, mittel = 10 %, dick rot = 50 %. Koordinaten = Anteile von Breite/Höhe.")


def scene_seconds(s: dict) -> float:
    # identisch zu sceneSeconds() in remotion/src/types.ts
    return s.get("duration") or max(2.5, len(s["narration"].split()) / WORDS_PER_SEC + 0.4)


def cmd_stills(a):
    pdir = project_dir(a.project)
    sb = load_sb(pdir)
    rdir = pdir / "remotion"
    if not (rdir / "node_modules").is_dir():
        die("video/remotion/node_modules fehlt – erst `npm install` in video/remotion")
    from storyboard import sync, validate
    errs = validate(sb)
    if errs:
        die("Storyboard ungültig:\n" + "\n".join(errs))
    sync(pdir, sb)
    fps = sb["format"]["fps"]
    wanted = {s["id"] for s in select_scenes(sb, a.only)}
    out = pdir / "review" / "screens"
    out.mkdir(parents=True, exist_ok=True)
    start = 0
    count = 0
    for s in sb["scenes"]:
        frames = round(scene_seconds(s) * fps)
        if s["id"] in wanted and s["visual"].get("component") == "ScreenshotFocus":
            foci = (s["visual"].get("props") or {}).get("focus") or []
            foci = foci if isinstance(foci, list) else [foci]
            secs = frames / fps
            times = [f.get("at", 0.5 if len(foci) == 1 else 0.4 + i * (secs - 0.8) / len(foci)) + MOVE + 0.6
                     for i, f in enumerate(foci)] or [secs / 2]
            for i, t in enumerate(times):
                fr = start + min(round(t * fps), frames - 1)
                dst = out / f"{s['id']}_focus{i + 1}.png"
                cp = run(["npx", "remotion", "still", "Explainer", f"--frame={fr}", str(dst)], cwd=rdir)
                if cp.returncode:
                    die(f"remotion still {s['id']}: {cp.stderr[-1500:]}")
                print(f"✔ {dst.relative_to(pdir)}  (Frame {fr})")
                count += 1
        start += frames
    if not count:
        die("Keine ScreenshotFocus-Szenen gefunden")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check")
    p.set_defaults(fn=cmd_check)
    g = sub.add_parser("grid")
    g.add_argument("files", nargs="*", help="Dateinamen in assets/screens/ (Default: alle Bilder)")
    g.set_defaults(fn=cmd_grid)
    st = sub.add_parser("stills")
    st.add_argument("--only", help="Szenen-IDs, kommagetrennt")
    st.set_defaults(fn=cmd_stills)
    for sp in (p, g, st):
        sp.add_argument("--dir", dest="project", help="Videoordner (Default: video/)")
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
