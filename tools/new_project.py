#!/usr/bin/env python3
"""Legt ein neues Videoprojekt unter projects/<slug>/ an.

  python3 tools/new_project.py wie-dns-funktioniert --title "Wie DNS funktioniert" \
      [--compositor remotion|hyperframes|tesseract] [--format 16:9|9:16|1:1] [--lang de]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil

from _common import PROJECTS, REPO, die

FORMATS = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--title", required=True)
    ap.add_argument("--compositor", default="remotion", choices=["remotion", "hyperframes", "tesseract"])
    ap.add_argument("--format", default="16:9", choices=list(FORMATS))
    ap.add_argument("--lang", default="de")
    a = ap.parse_args()

    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", a.slug):
        die("slug: nur a-z, 0-9 und Bindestrich")
    dst = PROJECTS / a.slug
    if dst.exists():
        die(f"{dst} existiert bereits")

    tpl = REPO / "templates" / "project"
    shutil.copytree(tpl, dst, ignore=shutil.ignore_patterns("remotion", "node_modules"))
    if a.compositor == "remotion":
        shutil.copytree(tpl / "remotion", dst / "remotion", ignore=shutil.ignore_patterns("node_modules"))
    for d in ("assets/images", "assets/clips", "assets/audio", "assets/music", "renders", "review", ".work"):
        (dst / d).mkdir(parents=True, exist_ok=True)

    sbf = dst / "storyboard.json"
    sb = json.loads(sbf.read_text(encoding="utf-8"))
    w, h = FORMATS[a.format]
    sb.update(title=a.title, slug=a.slug, language=a.lang, compositor=a.compositor, status="brief")
    sb["format"].update(width=w, height=h)
    sbf.write_text(json.dumps(sb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    brief = dst / "brief.md"
    brief.write_text(brief.read_text(encoding="utf-8").replace("{{TITLE}}", a.title), encoding="utf-8")
    shutil.copyfile(sbf, dst / "assets" / "storyboard.json")

    print(f"✔ Projekt angelegt: {dst.relative_to(REPO)}  ({a.format}, {a.compositor})")
    if a.compositor == "remotion":
        print(f"  Remotion: cd {dst.relative_to(REPO)}/remotion && npm install")
    elif a.compositor == "hyperframes":
        print(f"  Hyperframes: cd {dst.relative_to(REPO)} && npx hyperframes init hyperframes")


if __name__ == "__main__":
    main()
