#!/usr/bin/env python3
"""Wiederkehrende Figur aus einem Foto: Varianten erzeugen, eine als Referenz wählen.

  python3 tools/character.py ref images/tobi.png              # 3 Varianten → review/character/
  python3 tools/character.py ref images/tobi.png --seeds 4,5 --waist-up
  python3 tools/character.py ref images/tobi.png --prompt "Turn this person into …"
  python3 tools/character.py pick 2                           # → assets/images/character_ref.png + style.characterRef

Ablauf: Qwen Image 2.1 Turbo Edit stilisiert das Foto im Stil von `style.imagePrompt`
(bzw. `style.characterStyle`, falls gesetzt). Der User wählt per Vergleichsbild
`review/character/ref_grid.png`. Danach setzt `comfy_assets.py` die Figur in jede Szene
mit `visual.character` ein (Z-Image liefert nur noch Bildaufbau und Set).

Fotos von Personen nur mit deren Einverständnis verwenden; sie bleiben lokal
(assets/ ist git-ignoriert).
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from _common import die, load_sb, patch_sb, project_dir, run
from comfy_assets import IMAGE_SIZE, QEDIT, orientation, run_workflow, stage

DEFAULT_PROMPT = (
    "Turn the person in this photo into a {framing} character in this visual style: {style}. "
    "Stylize the face the way this style does, but keep the person clearly recognizable: the same face shape, "
    "the same hairstyle and hair colour, the same facial hair, the same eyes, eyebrows and smile, the same body shape "
    "and the same clothing and colours. {pose} Plain softly lit backdrop in matching style."
)
FRAMING = {
    "full": ("full-body", "The character stands facing the camera, the whole figure visible from head to shoes."),
    "waist": ("waist-up", "The character faces the camera, framed from the waist up."),
}


def cmd_ref(pdir: Path, a) -> None:
    sb = load_sb(pdir)
    photo = (pdir / "assets" / a.photo) if not Path(a.photo).is_absolute() else Path(a.photo)
    if not photo.is_file():
        die(f"Foto nicht gefunden: {photo}")
    style = (sb["style"].get("characterStyle") or sb["style"].get("imagePrompt") or "").strip().rstrip(".")
    framing, pose = FRAMING["waist" if a.waist_up else "full"]
    prompt = a.prompt or DEFAULT_PROMPT.format(framing=framing, style=style, pose=pose)
    # Kleine Handyfotos vorher hochskalieren – Qwen Edit ignoriert die Anweisung sonst gern
    big = pdir / ".work" / f"character_src{photo.suffix or '.png'}"
    big.parent.mkdir(exist_ok=True)
    cp = run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(photo), "-vf",
              "scale='if(lt(ih,1024),-2,iw)':'if(lt(ih,1024),1024,ih)':flags=lanczos", str(big)])
    if cp.returncode != 0:
        die(f"ffmpeg: {cp.stderr.strip()}")
    name = stage(pdir, big, f"vidgen_{sb['slug']}_character_src{big.suffix}", a.dry_run)
    w, h = (1024, 1024) if a.waist_up else IMAGE_SIZE[orientation(sb["format"])]
    out_dir = pdir / "review" / "character"
    out_dir.mkdir(parents=True, exist_ok=True)
    seeds = [int(x) for x in a.seeds.split(",")]
    made = []
    for seed in seeds:
        print(f"Variante Seed {seed}")
        out = run_workflow(pdir, f"character_ref_{seed}", QEDIT, {
            "prompt": prompt, "width": w, "height": h, "seed": seed, "image": name,
            "prefix": f"vidgen/{sb['slug']}/character_{seed}"}, timeout=900, dry=a.dry_run)
        if out:
            dst = out_dir / f"ref_{seed}.png"
            shutil.copyfile(out, dst)
            made.append(dst)
    if made:
        grid = out_dir / "ref_grid.png"
        inputs = ["-i", str(photo)] + [x for p in made for x in ("-i", str(p))]
        n = len(made) + 1
        chains = ";".join(f"[{i}]scale=-2:480,pad=iw+16:480:8:0:white[v{i}]" for i in range(n))
        run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex",
             f"{chains};{''.join(f'[v{i}]' for i in range(n))}hstack=inputs={n}", str(grid)])
        print(f"✔ Vergleich (Foto links, dann Seeds {a.seeds}): {grid.relative_to(pdir)}")
        print("  → ansehen, dem User zeigen, dann: python3 tools/character.py pick <seed>")


def cmd_pick(pdir: Path, a) -> None:
    src = pdir / "review" / "character" / f"ref_{a.seed}.png"
    if not src.is_file():
        die(f"{src.relative_to(pdir)} fehlt – erst `character.py ref` ausführen")
    dst = pdir / "assets" / "images" / "character_ref.png"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    patch_sb(pdir, lambda sb: sb["style"].__setitem__("characterRef", "images/character_ref.png"))
    print("✔ style.characterRef = images/character_ref.png")
    print("  Szenen mit der Figur: visual.character = true bzw. {\"wear\": …, \"action\": …} setzen,")
    print("  dann python3 tools/comfy_assets.py --kind image (bestehende Bilder: --reswap bzw. --force)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", dest="project", help="Videoordner (Default: video/)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("ref", help="Figurvarianten aus einem Foto erzeugen")
    r.add_argument("photo", help="Pfad relativ zu assets/ (z. B. images/tobi.png) oder absolut")
    r.add_argument("--seeds", default="1,2,3")
    r.add_argument("--waist-up", action="store_true", help="Brustbild statt ganzer Figur")
    r.add_argument("--prompt", help="eigene Anweisung statt der Vorgabe aus style.imagePrompt")
    r.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("pick", help="Variante als Referenzfigur übernehmen")
    p.add_argument("seed")
    a = ap.parse_args()
    pdir = project_dir(a.project)
    {"ref": cmd_ref, "pick": cmd_pick}[a.cmd](pdir, a)


if __name__ == "__main__":
    main()
