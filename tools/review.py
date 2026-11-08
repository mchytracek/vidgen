#!/usr/bin/env python3
"""Review-Hilfen für einen Render: Kontaktbögen, Szenen-Frames, Lautheit.

  python3 tools/review.py   # nimmt renders/final.mp4
  python3 tools/review.py --video renders/draft.mp4
  python3 tools/review.py --normalize        # → renders/final_norm.mp4 (-16 LUFS)
"""
from __future__ import annotations

import argparse
import json
import re
import shutil

from _common import die, load_sb, media_duration, project_dir, run


def ff(*args: str):
    cp = run(["ffmpeg", "-y", "-loglevel", "error", *args])
    if cp.returncode:
        die(f"ffmpeg: {cp.stderr[-1500:]}")
    return cp


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", dest="project", help="Videoordner (Default: video/)")
    ap.add_argument("--video", default="renders/final.mp4")
    ap.add_argument("--normalize", action="store_true")
    a = ap.parse_args()
    if not shutil.which("ffmpeg"):
        die("ffmpeg fehlt (brew install ffmpeg)")

    pdir = project_dir(a.project)
    sb = load_sb(pdir)
    video = pdir / a.video
    if not video.exists():
        die(f"{video} nicht gefunden")
    rdir = pdir / "review"
    rdir.mkdir(exist_ok=True)

    dur = media_duration(video)
    probe = json.loads(run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", str(video)]).stdout)
    vs = next((s for s in probe["streams"] if s["codec_type"] == "video"), {})
    aus = [s for s in probe["streams"] if s["codec_type"] == "audio"]

    n = max(1, int(dur // 2))
    cols = 6
    rows = -(-n // cols)
    ff("-i", str(video), "-vf", f"fps=0.5,scale=480:-2,tile={cols}x{rows}:padding=4:color=white",
       "-frames:v", "1", str(rdir / "contact_all.png"))

    t = 0.0
    for s in sb["scenes"]:
        d = s.get("duration") or 0
        if d:
            pts = [t + 0.15, t + d / 2, t + d - 0.15]
            inputs = []
            for p in pts:
                inputs += ["-ss", f"{p:.2f}", "-i", str(video)]
            ff(*inputs, "-filter_complex",
               "[0:v]scale=640:-2[a];[1:v]scale=640:-2[b];[2:v]scale=640:-2[c];[a][b][c]hstack=3",
               "-frames:v", "1", str(rdir / f"scene_{s['id']}.png"))
        t += d

    loud = run(["ffmpeg", "-hide_banner", "-i", str(video), "-af", "ebur128", "-f", "null", "-"]).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", loud)
    lufs = float(m[-1]) if m else None

    fmt = sb["format"]
    lines = [f"# Review {sb['title']}", "",
             f"- Datei: `{a.video}`",
             f"- Dauer: {dur:.2f} s (Storyboard: {sb.get('totalDuration')} s)",
             f"- Video: {vs.get('width')}x{vs.get('height')} @ {vs.get('r_frame_rate')} "
             f"(Soll {fmt['width']}x{fmt['height']} @ {fmt['fps']})",
             f"- Audiospuren: {len(aus)}" + (f", Kanäle {aus[0].get('channels')}" if aus else " ⚠️ kein Ton"),
             f"- Lautheit: {lufs} LUFS (Ziel −16)" if lufs is not None else "- Lautheit: nicht messbar",
             "", "Bilder: `contact_all.png`, `scene_<id>.png` (Anfang | Mitte | Ende)"]
    (rdir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))

    if a.normalize:
        out = video.with_name(video.stem + "_norm.mp4")
        ff("-i", str(video), "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac",
           "-b:a", "192k", str(out))
        print(f"✔ normalisiert: {out.relative_to(pdir)}")


if __name__ == "__main__":
    main()
