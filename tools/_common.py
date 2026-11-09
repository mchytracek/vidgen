"""Gemeinsame Helfer für die vidgen-Tools (nur Standardbibliothek)."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VIDEO = REPO / "video"
WORKFLOWS = REPO / "comfy" / "workflows"
DEFAULT_COMFY_URL = "http://127.0.0.1:8188"
CONFIG_HOME = Path(os.environ.get("VIDGEN_CONFIG", "~/.config/vidgen")).expanduser()
# Referenzstimmen außerhalb des Repos (personenbezogen → nie versionieren)
VOICE_HOME = Path(os.environ.get("VIDGEN_VOICES", "~/.config/vidgen/voices")).expanduser()


def _read_env_file(path: Path) -> dict[str, str]:
    """Einfache KEY=VALUE-Datei (Kommentare mit #, optionale Anführungszeichen)."""
    out: dict[str, str] = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip("'\"")
    return out


def comfy_url() -> str:
    """ComfyUI-Adresse: $COMFYUI_URL > .vidgen.env (dieser Klon) > ~/.config/vidgen/env > 127.0.0.1:8188."""
    for val in (os.environ.get("COMFYUI_URL"),
                _read_env_file(REPO / ".vidgen.env").get("COMFYUI_URL"),
                _read_env_file(CONFIG_HOME / "env").get("COMFYUI_URL")):
        if val and val.strip():
            url = val.strip().rstrip("/")
            return url if "://" in url else f"http://{url}"
    return DEFAULT_COMFY_URL


def comfy_is_remote(url: str | None = None) -> bool:
    from urllib.parse import urlparse
    host = urlparse(url or comfy_url()).hostname or ""
    return not (host in ("localhost", "::1") or host.startswith("127."))


def comfy_env() -> dict[str, str]:
    """Umgebung für comfy-cli: COMFY_LOCAL_URL lenkt run/upload/download auf den konfigurierten Server."""
    url = comfy_url()
    return {**os.environ, "COMFY_LOCAL_URL": url, "COMFYUI_URL": url}


def die(msg: str, code: int = 1) -> None:
    print(f"✖ {msg}", file=sys.stderr)
    sys.exit(code)


def project_dir(arg: str | None = None) -> Path:
    """Videoordner – Default `video/` im Repo, per --dir überschreibbar."""
    p = Path(arg).expanduser() if arg else VIDEO
    if not p.is_absolute():
        p = Path.cwd() / p
    if not (p / "storyboard.json").exists():
        die(f"Kein storyboard.json in {p} – erst `scripts/init.sh \"<Titel>\"` ausführen")
    return p.resolve()


def voice_file(ref: str) -> Path | None:
    """Referenzstimme finden: erst im Repo (voices/…), dann in VOICE_HOME (~/.config/vidgen/voices)."""
    for cand in (REPO / ref, VOICE_HOME / Path(ref).name):
        if cand.is_file():
            return cand
    return None


def load_sb(pdir: Path) -> dict:
    return json.loads((pdir / "storyboard.json").read_text(encoding="utf-8"))


def save_sb(pdir: Path, sb: dict) -> None:
    (pdir / "storyboard.json").write_text(
        json.dumps(sb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def select_scenes(sb: dict, only: str | None) -> list[dict]:
    if not only:
        return sb["scenes"]
    wanted = {s.strip() for s in only.split(",") if s.strip()}
    unknown = wanted - {s["id"] for s in sb["scenes"]}
    if unknown:
        die(f"Unbekannte Szenen: {', '.join(sorted(unknown))}")
    return [s for s in sb["scenes"] if s["id"] in wanted]


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, **kw)


def comfy(*args: str, timeout: int | None = None) -> dict:
    """Ruft `comfy --json …` auf und gibt das letzte envelope/1-Objekt zurück."""
    if not shutil.which("comfy"):
        die("comfy-cli nicht gefunden (pip install comfy-cli)")
    cp = run(["comfy", "--json", *args], timeout=timeout, env=comfy_env())
    env = None
    for line in cp.stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("type") == "envelope":
                env = obj
    if env is None:
        die(f"comfy {' '.join(args[:2])}: keine JSON-Antwort\n{cp.stderr[-2000:]}")
    return env


def comfy_output(out: str, pdir: Path) -> Path:
    """Ausgabe eines comfy-run als lokale Datei. Lokal liefert comfy-cli einen Pfad im
    ComfyUI-Ordner, bei einem entfernten Server eine /view-URL – die wird nach .work/ geladen."""
    if not out.startswith(("http://", "https://")):
        return Path(out)
    import urllib.request
    from urllib.parse import parse_qs, urlparse
    name = Path(parse_qs(urlparse(out).query).get("filename", ["output.bin"])[0]).name
    dst = pdir / ".work" / "comfy_out" / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(out, timeout=300) as r, open(dst, "wb") as f:
            shutil.copyfileobj(r, f)
    except OSError as exc:
        die(f"Download der ComfyUI-Ausgabe fehlgeschlagen: {out}\n{exc}")
    return dst


def media_duration(path: Path) -> float:
    """Dauer in Sekunden – ffprobe, sonst macOS afinfo."""
    if shutil.which("ffprobe"):
        cp = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                  "-of", "default=nw=1:nk=1", str(path)])
        if cp.returncode == 0 and cp.stdout.strip():
            return float(cp.stdout.strip())
    if shutil.which("afinfo"):
        cp = run(["afinfo", str(path)])
        m = re.search(r"estimated duration:\s*([\d.]+)", cp.stdout)
        if m:
            return float(m.group(1))
    die(f"Dauer von {path} nicht messbar (ffprobe fehlt?)")
    return 0.0


if __name__ == "__main__":
    # für Shell-Skripte: `python3 tools/_common.py comfy-url`
    if sys.argv[1:] == ["comfy-url"]:
        print(comfy_url())
    else:
        die("Aufruf: python3 tools/_common.py comfy-url")
