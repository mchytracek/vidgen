#!/usr/bin/env python3
"""Erzeugt fehlende Bild-/Clip-/Musik-Assets eines Storyboards im lokalen ComfyUI.

Nutzt dieselbe Engine wie der MCP-Server comfy-mcp (comfy-cli). Die Vorlagen in
comfy/workflows/ bleiben unverändert; pro Job entsteht eine Arbeitskopie in .work/.

  python3 tools/comfy_assets.py   # alles Fehlende
  python3 tools/comfy_assets.py --only s03,s05 --force
  python3 tools/comfy_assets.py --kind image     # image | clip | music
  python3 tools/comfy_assets.py --reswap         # nur Figurentausch neu (Basisbild bleibt)
  python3 tools/comfy_assets.py --dry-run

Wiederkehrende Figur: Ist `style.characterRef` gesetzt (siehe tools/character.py) und hat
eine Szene `visual.character`, wird das Z-Image-Bild als Bildaufbau benutzt
(`images/<id>_base.png`) und Qwen Image 2.1 Edit setzt die Referenzfigur ein.

Das Storyboard wird nach jedem Asset frisch geladen und nur punktuell geändert –
Änderungen, die während eines langen Laufs am Storyboard gemacht werden, bleiben erhalten.
"""
from __future__ import annotations

import argparse
import math
import re
import shutil
import time
from pathlib import Path

from _common import WORKFLOWS, comfy, comfy_output, die, load_sb, patch_sb, patch_scene, project_dir, run, select_scenes

# Slot-Zuordnung je Workflow (siehe comfy/workflows/README.md)
IMAGE = {"file": "image_z_image_turbo.json", "prompt": "57.text", "width": "57.width",
         "height": "57.height", "seed": "57.seed", "prefix": "9.filename_prefix"}
I2V = {"file": "video_ltx2_3_i2v.json", "image": "269.image", "prompt": "320.value",
       "enhance": "320.value_1", "width": "320.value_2", "height": "320.value_3",
       "seconds": "320.value_4", "fps": "320.value_5", "seed": "320.noise_seed",
       "prefix": "75.filename_prefix"}
MUSIC = {"file": "audio_ace_step1_5_xl_turbo.json", "tags": "94.tags", "lyrics": "94.lyrics",
         "bpm": "94.bpm",
         # 99 ist ein reiner UI-PrimitiveNode (nicht in object_info) – comfy-cli ≥ 1.13 lehnt
         # Slots darauf ab. Beim Konvertieren ins API-Format zählen ohnehin die Widget-Werte
         # der Ziel-Nodes, deshalb die Dauer direkt in 98/94 setzen.
         "seconds": ["98.seconds", "94.duration"], "seed": "109.value", "prefix": "111.filename_prefix"}
# Qwen Image 2.1 Turbo Edit: 1 Bild (Umstilen, z. B. Foto → Figur) bzw. 2 Bilder (Szene + Referenzfigur)
QEDIT = {"file": "image_qwen_2_1_turbo_edit.json", "prompt": "459.prompt", "width": "459.width",
         "height": "459.height", "seed": "459.seed", "image": "470.image", "prefix": "461.filename_prefix"}
QEDIT_REF = {**QEDIT, "file": "image_qwen_2_1_turbo_edit_ref.json", "ref": "600.image"}

IMAGE_SIZE = {"landscape": (1344, 768), "portrait": (768, 1344), "square": (1024, 1024)}
CLIP_SIZE = {"landscape": (1280, 720), "portrait": (720, 1280), "square": (960, 960)}

# LTX-2.3 blendet die letzten ~2 s eines Clips nach Schwarz ab (beobachtet bei i2v, 25 fps).
# Clips deshalb länger erzeugen als die Szene; reicht auch das nicht (Szene > ~7,7 s bei
# max. 10 s), spielt der Compositor den Clip leicht verlangsamt (visual.props.playbackRate).
LTX_FADE_TAIL = 2.3
CLIP_EXTRA = 3
CLIP_MAX = 10


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
    return comfy_output(outs[0], pdir)


def store(src: Path, pdir: Path, sub: str, sid: str) -> str:
    dst = pdir / "assets" / sub / f"{sid}{src.suffix}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return f"{sub}/{dst.name}"


def stage(pdir: Path, src: Path, name: str, dry: bool) -> str:
    """Datei unter `name` in ComfyUIs input/ hochladen (lokal oder entfernt)."""
    if not dry:
        staged = pdir / ".work" / name
        staged.parent.mkdir(exist_ok=True)
        shutil.copyfile(src, staged)
        env = comfy("upload", str(staged), "--overwrite")
        if not env["ok"]:
            die(f"Upload {name}: {env['error']}")
    return name


def character_prompt(char) -> str:
    """Anweisung für den Figurentausch: <image1> = Szenenbild, <image2> = Referenzfigur."""
    c = char if isinstance(char, dict) else {}
    wear = c.get("wear") or "The character wears the outfit of <image2>."
    action = c.get("action") or ""
    keep = "pose, action, position and size" if action else "pose, action, facial expression, position and size"
    return ("Replace the main character in <image1> with the character from <image2>, so that it becomes exactly "
            "that character: the same face, the same hairstyle and facial hair, the same body shape. "
            f"{wear} {action} Keep the {keep} from <image1>, and keep everything else in <image1> unchanged: "
            "the set, the props, any other characters, the lighting, the camera framing and the visual style.").replace("  ", " ")


def clip_plan(duration: float) -> tuple[int, float | None]:
    """Clip-Länge in s und ggf. nötige Verlangsamung, damit die LTX-Abblendung nie im Bild ist."""
    secs = min(max(math.ceil(duration) + CLIP_EXTRA, 3), CLIP_MAX)
    usable = secs - LTX_FADE_TAIL
    return secs, (round(usable / duration, 2) if duration > usable else None)


def audible_end(path: Path, noise_db: int = -45) -> float | None:
    """Zeitpunkt, ab dem die Datei bis zum Ende still bleibt (ffmpeg silencedetect); None = durchgehend hörbar."""
    cp = run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", f"silencedetect=noise={noise_db}dB:d=0.5", "-f", "null", "-"])
    starts = re.findall(r"silence_start: ([\d.]+)", cp.stderr)
    ends = re.findall(r"silence_end: ([\d.]+)", cp.stderr)
    if len(starts) > len(ends):  # letzte Stille reicht bis Dateiende (ffmpeg meldet dann kein Ende)
        return float(starts[-1])
    probe = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    total = float(probe.stdout.strip() or 0)
    if starts and ends and abs(float(ends[-1]) - total) < 0.05:
        return float(starts[-1])
    return None


def _set_asset(key: str, rel: str):
    return lambda sc: sc.setdefault("assets", {}).__setitem__(key, rel)


def _set_rate(rate: float | None):
    def apply(sc: dict) -> None:
        props = sc["visual"].setdefault("props", {})
        if rate:
            props["playbackRate"] = rate
        else:
            props.pop("playbackRate", None)
        if not props:
            sc["visual"].pop("props")
    return apply


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", dest="project", help="Videoordner (Default: video/)")
    ap.add_argument("--only", help="Szenen-IDs, kommagetrennt")
    ap.add_argument("--kind", choices=["image", "clip", "music"], help="nur diese Asset-Art")
    ap.add_argument("--force", action="store_true", help="vorhandene Assets neu erzeugen")
    ap.add_argument("--reswap", action="store_true",
                    help="nur den Figurentausch neu (vorhandenes images/<id>_base.png bleibt); Clip danach mit --kind clip --force")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--prompt-enhance", action="store_true", help="LTX prompt_enhance einschalten")
    a = ap.parse_args()

    pdir = project_dir(a.project)
    sb = load_sb(pdir)
    ori = orientation(sb["format"])
    style = sb["style"].get("imagePrompt", "").strip()
    slug = sb["slug"]

    ref_name = None
    ref = sb["style"].get("characterRef")
    if ref and any(s["visual"].get("character") for s in select_scenes(sb, a.only)):
        ref_path = pdir / "assets" / ref
        if not ref_path.is_file():
            die(f"style.characterRef nicht gefunden: assets/{ref} – erst tools/character.py ref/pick")
        ref_name = stage(pdir, ref_path, f"vidgen_{slug}_charref{ref_path.suffix}", a.dry_run)

    def have(s, key):
        rel = (s.get("assets") or {}).get(key)
        return bool(rel) and (pdir / "assets" / rel).exists() and not a.force

    for s in select_scenes(sb, a.only):
        v, sid = s["visual"], s["id"]
        s.setdefault("assets", {})
        char = v.get("character") if ref_name else None
        needs_image = v["kind"] in ("image", "clip") and a.kind in (None, "image", "clip")
        redo_swap = a.reswap and bool(char)
        if needs_image and (not have(s, "image") or redo_swap):
            w, h = IMAGE_SIZE[ori]
            base = pdir / "assets" / "images" / f"{sid}_base.png"
            if not (redo_swap and base.is_file() and not a.force):
                prompt = f"{v['prompt'].rstrip('. ')}. {style}" if style else v["prompt"]
                print(f"{sid}: Bild ({w}x{h})")
                out = run_workflow(pdir, f"{sid}_image", IMAGE, {
                    "prompt": prompt, "width": w, "height": h, "seed": v.get("seed", 0),
                    "prefix": f"vidgen/{slug}/{sid}"}, timeout=600, dry=a.dry_run)
                if out and char:
                    store(out, pdir, "images", f"{sid}_base")
                elif out:
                    rel = store(out, pdir, "images", sid)
                    s["assets"]["image"] = rel
                    patch_scene(pdir, sid, _set_asset("image", rel))
            if char and (a.dry_run or base.is_file()):
                print(f"{sid}: Figurentausch (Qwen Edit, Referenz {ref})")
                img1 = stage(pdir, base, f"vidgen_{slug}_{sid}_base.png", a.dry_run)
                out = run_workflow(pdir, f"{sid}_swap", QEDIT_REF, {
                    "prompt": character_prompt(char), "width": w, "height": h,
                    "seed": (char.get("seed") if isinstance(char, dict) else None) or 1,
                    "image": img1, "ref": ref_name, "prefix": f"vidgen/{slug}/{sid}_swap"},
                    timeout=900, dry=a.dry_run)
                if out:
                    rel = store(out, pdir, "images", sid)
                    s["assets"]["image"] = rel
                    patch_scene(pdir, sid, _set_asset("image", rel))
                    if (pdir / "assets" / s["assets"].get("clip", "-")).is_file():
                        print(f"  ⚠ {sid}: Clip basiert noch auf dem alten Bild → --only {sid} --kind clip --force")

        if v["kind"] == "clip" and a.kind in (None, "clip") and not have(s, "clip"):
            img = pdir / "assets" / s["assets"].get("image", "")
            if not a.dry_run and not img.is_file():
                die(f"{sid}: Startbild fehlt – erst Bild erzeugen")
            secs, rate = clip_plan(s.get("duration") or 5)
            w, h = CLIP_SIZE[ori]
            print(f"{sid}: Clip LTX-2.3 i2v ({w}x{h}, {secs} s) – dauert einige Minuten")
            if rate and rate < 0.85:
                print(f"  ⚠ {sid}: Szene ({s.get('duration')} s) ist für einen Clip zu lang – "
                      f"Wiedergabe auf {rate:.2f}× verlangsamt; besser Szene teilen")
            name_in_input = stage(pdir, img, f"vidgen_{slug}_{sid}{img.suffix or '.png'}", a.dry_run)
            out = run_workflow(pdir, f"{sid}_clip", I2V, {
                "image": name_in_input, "prompt": v["motionPrompt"],
                "enhance": str(a.prompt_enhance).lower(), "width": w, "height": h,
                "seconds": secs, "fps": 25, "seed": v.get("seed", 0) or 42,
                "prefix": f"vidgen/{slug}/{sid}"}, timeout=3600, dry=a.dry_run)
            if out:
                rel = store(out, pdir, "clips", sid)
                s["assets"]["clip"] = rel

                def apply(sc, rel=rel, rate=rate):
                    _set_asset("clip", rel)(sc)
                    _set_rate(rate)(sc)
                patch_scene(pdir, sid, apply)

    m = sb.get("music") or {}
    if a.kind in (None, "music") and m.get("enabled") and not a.only:
        if m.get("file") and (pdir / "assets" / m["file"]).exists() and not a.force:
            pass
        else:
            # ACE-Step komponiert einen Schluss und klingt einige Sekunden vor `seconds` aus –
            # deshalb großzügig länger erzeugen; der Compositor blendet am Videoende aus.
            secs = math.ceil((sb.get("totalDuration") or 90) + 12)
            print(f"Musik: ACE-Step ({secs} s)")
            out = run_workflow(pdir, "music", MUSIC, {
                "tags": m.get("tags") or "calm corporate ambient, soft piano, warm pads, instrumental",
                "lyrics": "[instrumental]", "bpm": m.get("bpm", 90), "seconds": secs,
                "seed": m.get("seed", 1), "prefix": f"vidgen/{slug}/music"},
                timeout=1800, dry=a.dry_run)
            if out:
                rel = store(out, pdir, "music", "music")
                patch_sb(pdir, lambda b, rel=rel: b.setdefault("music", {}).__setitem__("file", rel))
                end = audible_end(pdir / "assets" / rel)
                need = load_sb(pdir).get("totalDuration") or 0
                if end is not None and end < need + 1:
                    print(f"  ⚠ Musik klingt bei {end:.1f} s aus, Video dauert {need:.1f} s – "
                          f"anderen music.seed probieren und mit --kind music --force neu erzeugen")
                elif end is not None:
                    print(f"  Musik hörbar bis {end:.1f} s (Video {need:.1f} s)")

    if not a.dry_run:
        from storyboard import sync
        sync(pdir)
    print("Fertig.")


if __name__ == "__main__":
    main()
