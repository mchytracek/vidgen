#!/usr/bin/env python3
"""Erzeugt fehlende Bild-/Clip-/Musik-Assets eines Storyboards im lokalen ComfyUI.

Nutzt dieselbe Engine wie der MCP-Server comfy-mcp (comfy-cli). Die Vorlagen in
comfy/workflows/ bleiben unverändert; pro Job entsteht eine Arbeitskopie in .work/.

  python3 tools/comfy_assets.py   # alles Fehlende
  python3 tools/comfy_assets.py --only s03,s05 --force
  python3 tools/comfy_assets.py --kind image     # image | clip | music
  python3 tools/comfy_assets.py --dry-run
"""
from __future__ import annotations

import argparse
import math
import shutil
import time
from pathlib import Path

from _common import WORKFLOWS, comfy, die, load_sb, project_dir, save_sb, select_scenes

# Slot-Zuordnung je Workflow (siehe comfy/workflows/README.md)
IMAGE = {"file": "image_z_image_turbo.json", "prompt": "57.text", "width": "57.width",
         "height": "57.height", "seed": "57.seed", "prefix": "9.filename_prefix"}
I2V = {"file": "video_ltx2_3_i2v.json", "image": "269.image", "prompt": "320.value",
       "enhance": "320.value_1", "width": "320.value_2", "height": "320.value_3",
       "seconds": "320.value_4", "fps": "320.value_5", "seed": "320.noise_seed",
       "prefix": "75.filename_prefix"}
MUSIC = {"file": "audio_ace_step1_5_xl_turbo.json", "tags": "94.tags", "lyrics": "94.lyrics",
         "bpm": "94.bpm",
         # 99 ist ein UI-PrimitiveNode: beim Konvertieren ins API-Format zählen die
         # Widget-Werte der Ziel-Nodes, deshalb Dauer zusätzlich direkt in 98/94 setzen.
         "seconds": ["99.value", "98.seconds", "94.duration"], "seed": "109.value", "prefix": "111.filename_prefix"}

IMAGE_SIZE = {"landscape": (1344, 768), "portrait": (768, 1344), "square": (1024, 1024)}
CLIP_SIZE = {"landscape": (1280, 720), "portrait": (720, 1280), "square": (960, 960)}


def orientation(fmt: dict) -> str:
    w, h = fmt["width"], fmt["height"]
    return "landscape" if w > h else "portrait" if h > w else "square"


def run_workflow(pdir: Path, name: str, spec: dict, overrides: dict, timeout: int, dry: bool) -> Path | None:
    work = pdir / ".work" / f"{name}.json"
    work.parent.mkdir(exist_ok=True)
    shutil.copyfile(WORKFLOWS / spec["file"], work)
    pairs = [f"{slot}={v}" for k, v in overrides.items()
             for slot in (spec[k] if isinstance(spec[k], list) else [spec[k]])]
    if dry:
        print(f"  [dry] {spec['file']}: " + "  ".join(p[:70] for p in pairs))
        return None
    env = comfy("workflow", "set-slot", str(work), *pairs)
    if not env["ok"]:
        die(f"set-slot {name}: {env['error']}")
    t0 = time.time()
    env = comfy("run", "--workflow", str(work), "--wait", "--timeout", str(timeout), timeout=timeout + 60)
    if not env["ok"] or (env.get("data") or {}).get("status") != "completed":
        die(f"{name} fehlgeschlagen: {env.get('error') or env.get('data')}\n"
            "→ MCP get_logs / job(action='status') prüfen")
    outs = env["data"].get("outputs") or []
    if not outs:
        die(f"{name}: keine Ausgabedatei gemeldet")
    print(f"  ✔ {name} in {time.time() - t0:.0f} s")
    return Path(outs[0])


def store(src: Path, pdir: Path, sub: str, sid: str) -> str:
    dst = pdir / "assets" / sub / f"{sid}{src.suffix}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return f"{sub}/{dst.name}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", dest="project", help="Videoordner (Default: video/)")
    ap.add_argument("--only", help="Szenen-IDs, kommagetrennt")
    ap.add_argument("--kind", choices=["image", "clip", "music"], help="nur diese Asset-Art")
    ap.add_argument("--force", action="store_true", help="vorhandene Assets neu erzeugen")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--prompt-enhance", action="store_true", help="LTX prompt_enhance einschalten")
    a = ap.parse_args()

    pdir = project_dir(a.project)
    sb = load_sb(pdir)
    ori = orientation(sb["format"])
    style = sb["style"].get("imagePrompt", "").strip()

    def have(s, key):
        rel = (s.get("assets") or {}).get(key)
        return bool(rel) and (pdir / "assets" / rel).exists() and not a.force

    for s in select_scenes(sb, a.only):
        v, sid = s["visual"], s["id"]
        s.setdefault("assets", {})
        needs_image = v["kind"] in ("image", "clip") and a.kind in (None, "image", "clip")
        if needs_image and not have(s, "image"):
            w, h = IMAGE_SIZE[ori]
            prompt = f"{v['prompt'].rstrip('. ')}. {style}" if style else v["prompt"]
            print(f"{sid}: Bild ({w}x{h})")
            out = run_workflow(pdir, f"{sid}_image", IMAGE, {
                "prompt": prompt, "width": w, "height": h, "seed": v.get("seed", 0),
                "prefix": f"vidgen/{sb['slug']}/{sid}"}, timeout=600, dry=a.dry_run)
            if out:
                s["assets"]["image"] = store(out, pdir, "images", sid)
                save_sb(pdir, sb)

        if v["kind"] == "clip" and a.kind in (None, "clip") and not have(s, "clip"):
            img = pdir / "assets" / s["assets"].get("image", "")
            if not a.dry_run and not img.is_file():
                die(f"{sid}: Startbild fehlt – erst Bild erzeugen")
            secs = min(max(math.ceil(s.get("duration") or 5), 3), 10)
            w, h = CLIP_SIZE[ori]
            print(f"{sid}: Clip LTX-2.3 i2v ({w}x{h}, {secs} s) – dauert einige Minuten")
            name_in_input = f"vidgen_{sb['slug']}_{sid}{img.suffix or '.png'}"
            if not a.dry_run:
                staged = pdir / ".work" / name_in_input
                shutil.copyfile(img, staged)
                env = comfy("upload", str(staged), "--overwrite")
                if not env["ok"]:
                    die(f"Upload {staged.name}: {env['error']}")
            out = run_workflow(pdir, f"{sid}_clip", I2V, {
                "image": name_in_input, "prompt": v["motionPrompt"],
                "enhance": str(a.prompt_enhance).lower(), "width": w, "height": h,
                "seconds": secs, "fps": 25, "seed": v.get("seed", 0) or 42,
                "prefix": f"vidgen/{sb['slug']}/{sid}"}, timeout=3600, dry=a.dry_run)
            if out:
                s["assets"]["clip"] = store(out, pdir, "clips", sid)
                save_sb(pdir, sb)

    m = sb.get("music") or {}
    if a.kind in (None, "music") and m.get("enabled") and not a.only:
        if m.get("file") and (pdir / "assets" / m["file"]).exists() and not a.force:
            pass
        else:
            secs = math.ceil((sb.get("totalDuration") or 90) + 2)
            print(f"Musik: ACE-Step ({secs} s)")
            out = run_workflow(pdir, "music", MUSIC, {
                "tags": m.get("tags") or "calm corporate ambient, soft piano, warm pads, instrumental",
                "lyrics": "[instrumental]", "bpm": m.get("bpm", 90), "seconds": secs,
                "seed": m.get("seed", 1), "prefix": f"vidgen/{sb['slug']}/music"},
                timeout=1800, dry=a.dry_run)
            if out:
                m["file"] = store(out, pdir, "music", "music")
                sb["music"] = m
                save_sb(pdir, sb)

    if not a.dry_run:
        from storyboard import sync
        sync(pdir)
    print("Fertig.")


if __name__ == "__main__":
    main()
