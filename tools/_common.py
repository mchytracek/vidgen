"""Gemeinsame Helfer für die vidgen-Tools (nur Standardbibliothek)."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROJECTS = REPO / "projects"
WORKFLOWS = REPO / "comfy" / "workflows"


def die(msg: str, code: int = 1) -> None:
    print(f"✖ {msg}", file=sys.stderr)
    sys.exit(code)


def project_dir(arg: str) -> Path:
    p = Path(arg)
    if not p.is_absolute():
        p = (Path.cwd() / p) if (Path.cwd() / p).exists() else PROJECTS / arg
    if not (p / "storyboard.json").exists():
        die(f"Kein storyboard.json in {p}")
    return p.resolve()


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
    cp = run(["comfy", "--json", *args], timeout=timeout)
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
