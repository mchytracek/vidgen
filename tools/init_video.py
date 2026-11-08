#!/usr/bin/env python3
"""Legt in einem frisch geklonten Repo den Videoordner video/ an.

Normalerweise über scripts/init.sh aufgerufen (macht zusätzlich git + npm).

  python3 tools/init_video.py "Wie DNS funktioniert" \
      [--slug wie-dns-funktioniert] [--compositor remotion|hyperframes|tesseract] \
      [--format 16:9|9:16|1:1] [--lang de] [--duration 75]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import unicodedata

from _common import REPO, VIDEO, die

FORMATS = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080)}


def slugify(title: str) -> str:
    t = title.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(a, b)
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:48] or "video"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("title")
    ap.add_argument("--slug")
    ap.add_argument("--compositor", default="remotion", choices=["remotion", "hyperframes", "tesseract"])
    ap.add_argument("--format", default="16:9", choices=list(FORMATS))
    ap.add_argument("--lang", default="de")
    ap.add_argument("--duration", type=float, default=75, help="Ziellänge in Sekunden")
    a = ap.parse_args()

    slug = a.slug or slugify(a.title)
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        die("slug: nur a-z, 0-9 und Bindestrich")
    if VIDEO.exists():
        die(f"{VIDEO.relative_to(REPO)}/ existiert bereits – dieses Repo ist schon initialisiert")

    tpl = REPO / "templates" / "project"
    shutil.copytree(tpl, VIDEO, ignore=shutil.ignore_patterns("remotion", "node_modules"))
    if a.compositor == "remotion":
        shutil.copytree(tpl / "remotion", VIDEO / "remotion", ignore=shutil.ignore_patterns("node_modules"))
    for d in ("assets/images", "assets/clips", "assets/audio", "assets/music", "renders", "review"):
        (VIDEO / d).mkdir(parents=True, exist_ok=True)

    sbf = VIDEO / "storyboard.json"
    sb = json.loads(sbf.read_text(encoding="utf-8"))
    w, h = FORMATS[a.format]
    sb.update(title=a.title, slug=slug, language=a.lang, compositor=a.compositor,
              status="brief", targetDuration=a.duration)
    sb["format"].update(width=w, height=h)
    sbf.write_text(json.dumps(sb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    brief = VIDEO / "brief.md"
    brief.write_text(brief.read_text(encoding="utf-8").replace("{{TITLE}}", a.title), encoding="utf-8")
    shutil.copyfile(sbf, VIDEO / "assets" / "storyboard.json")

    print(f"✔ video/ angelegt: „{a.title}“ (slug {slug}, {a.format}, {a.compositor})")


if __name__ == "__main__":
    main()
