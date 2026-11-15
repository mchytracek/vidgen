#!/usr/bin/env python3
"""ElevenLabs (Cloud) als Stimm-Backend: Stimmen suchen, probehören, übernehmen, Kontingent.

  python3 tools/elevenlabs.py voices                         # deutsche Stimmen der Stimmbibliothek
  python3 tools/elevenlabs.py voices --gender male --use-case informative_educational --previews
        # --previews lädt die (kostenlosen) Hörproben nach video/review/stimmen/
  python3 tools/elevenlabs.py mine                           # Stimmen im eigenen Konto
  python3 tools/elevenlabs.py add <public_owner_id> <voice_id> --name "Erzähler Jonas"
        # Bibliotheksstimme ins eigene Konto übernehmen (nötig vor der Nutzung per API)
  python3 tools/elevenlabs.py use <voice_id> [--model eleven_multilingual_v2]
        # im Storyboard eintragen: voice.backend = elevenlabs
  python3 tools/elevenlabs.py quota                          # verbrauchte/verfügbare Credits

API-Key (nie ins Repo): Umgebungsvariable ELEVENLABS_API_KEY oder Datei
~/.config/vidgen/elevenlabs.env mit `ELEVENLABS_API_KEY=…`. Die Sprechtexte werden an
ElevenLabs übertragen und kosten Credits (≈ 1 Credit pro Zeichen bei Multilingual v2).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from _common import CONFIG_HOME, die, load_sb, patch_sb, project_dir

API = os.environ.get("ELEVENLABS_API_URL", "https://api.elevenlabs.io").rstrip("/")
KEY_FILE = CONFIG_HOME / "elevenlabs.env"
DEFAULT_MODEL = "eleven_multilingual_v2"
# Modelle, die language_code akzeptieren (multilingual_v2 lehnt ihn ab)
LANG_CODE_MODELS = {"eleven_flash_v2_5", "eleven_turbo_v2_5", "eleven_v3", "eleven_v4", "eleven_v4_turbo"}
DEFAULT_SETTINGS = {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True}


def api_key() -> str:
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key and KEY_FILE.is_file():
        for line in KEY_FILE.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("ELEVENLABS_API_KEY="):
                key = line.split("=", 1)[1].strip().strip("'\"")
    if not key:
        die(f"Kein ElevenLabs-API-Key – ELEVENLABS_API_KEY setzen oder in {KEY_FILE} eintragen:\n"
            f"  mkdir -p {KEY_FILE.parent} && echo 'ELEVENLABS_API_KEY=…' > {KEY_FILE} && chmod 600 {KEY_FILE}")
    return key


def has_key() -> bool:
    return bool(os.environ.get("ELEVENLABS_API_KEY") or KEY_FILE.is_file())


def request(method: str, path: str, *, query: dict | None = None, body: dict | None = None,
            raw: bool = False, timeout: int = 180, soft: bool = False):
    """API-Aufruf; bei soft=True liefert ein HTTP-Fehler None statt abzubrechen."""
    url = f"{API}{path}"
    if query:
        url += "?" + urllib.parse.urlencode({k: v for k, v in query.items() if v not in (None, "")}, doseq=True)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "xi-api-key": api_key(), "Content-Type": "application/json",
        "Accept": "audio/mpeg" if raw else "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            payload = r.read()
            return (payload, dict(r.headers)) if raw else json.loads(payload or b"{}")
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:600]
        if soft:
            return None
        if "missing_permissions" in detail:
            die(f"ElevenLabs {method} {path}: dem API-Key fehlt eine Berechtigung – im ElevenLabs-Konto unter "
                f"Developers → API Keys ergänzen (nötig: Text to Speech, Voices lesen/schreiben; optional User lesen)."
                f"\n{detail}")
        hint = {401: " (API-Key falsch?)", 402: " (Kontingent/Abo reicht nicht)",
                429: " (Rate-Limit – später erneut)"}.get(e.code, "")
        die(f"ElevenLabs {method} {path}: HTTP {e.code}{hint}\n{detail}")
    except urllib.error.URLError as e:
        die(f"ElevenLabs nicht erreichbar: {e.reason}")


def synthesize(text: str, voice_id: str, dst: Path, *, model: str = DEFAULT_MODEL, settings: dict | None = None,
               seed: int | None = None, language: str | None = None, previous_text: str | None = None,
               next_text: str | None = None) -> tuple[Path, str | None]:
    """Text → MP3 (44,1 kHz). Gibt Pfad und request-id zurück."""
    body: dict = {"text": text, "model_id": model, "voice_settings": {**DEFAULT_SETTINGS, **(settings or {})}}
    if seed is not None:
        body["seed"] = int(seed) % 4294967295
    if language and model in LANG_CODE_MODELS:
        body["language_code"] = language
    if previous_text:
        body["previous_text"] = previous_text
    if next_text:
        body["next_text"] = next_text
    audio, headers = request("POST", f"/v1/text-to-speech/{voice_id}", query={"output_format": "mp3_44100_128"},
                             body=body, raw=True)
    dst.write_bytes(audio)
    return dst, headers.get("request-id") or headers.get("Request-Id")


def quota() -> tuple[int, int] | None:
    """(verbraucht, Limit) – None, wenn der Key keine user_read-Berechtigung hat."""
    sub = request("GET", "/v1/user/subscription", soft=True)
    if not sub:
        return None
    try:
        return int(sub["character_count"]), int(sub["character_limit"])
    except (KeyError, TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
def cmd_voices(a) -> None:
    res = request("GET", "/v1/shared-voices", query={
        "language": a.language, "gender": a.gender, "age": a.age, "search": a.search,
        "use_cases": a.use_case, "sort": a.sort, "page_size": a.limit, "page": a.page})
    voices = res.get("voices", [])
    if not voices:
        print("Keine Treffer – Filter lockern (z. B. ohne --use-case).")
        return
    prev_dir = None
    if a.previews:
        prev_dir = project_dir(a.project) / "review" / "stimmen"
        prev_dir.mkdir(parents=True, exist_ok=True)
    for n, v in enumerate(voices, 1):
        de = next((x for x in v.get("verified_languages") or [] if x.get("language") == a.language), {})
        accent = de.get("accent") or v.get("accent") or ""
        print(f"{n:2}. {v['name'][:28]:28} {v.get('gender', ''):7} {v.get('age', ''):12} {accent[:14]:14} "
              f"{v.get('use_case', '')[:24]:24} {v.get('descriptive', '')}")
        print(f"    add: {v['public_owner_id']} {v['voice_id']}   "
              f"({v.get('cloned_by_count', 0)}× genutzt{', Aufpreis ×' + str(v['rate']) if (v.get('rate') or 1) != 1 else ''})")
        if v.get("description"):
            print(f"    {v['description'][:140]}")
        url = de.get("preview_url") or v.get("preview_url")
        if prev_dir and url:
            safe = re.sub(r"[^\w-]+", "_", v["name"])[:30]
            dst = prev_dir / f"{n:02d}_{safe}.mp3"
            try:
                with urllib.request.urlopen(url, timeout=60) as r:
                    dst.write_bytes(r.read())
            except OSError as exc:
                print(f"    ⚠ Hörprobe nicht ladbar: {exc}")
    if prev_dir:
        print(f"\n✔ Hörproben (kostenlos, Originaltext der Sprecher): {prev_dir}")
    if res.get("has_more"):
        print(f"… weitere Treffer: --page {a.page + 1}")
    print("Übernehmen: python3 tools/elevenlabs.py add <public_owner_id> <voice_id> --name \"…\"")


def cmd_mine(a) -> None:
    res = request("GET", "/v2/voices", query={"page_size": 100})
    for v in res.get("voices", []):
        labels = ", ".join(f"{k}={val}" for k, val in (v.get("labels") or {}).items())
        print(f"  {v['voice_id']}  {v['name'][:30]:30} {v.get('category', ''):12} {labels}")


def cmd_add(a) -> None:
    res = request("POST", f"/v1/voices/add/{a.public_owner_id}/{a.voice_id}", body={"new_name": a.name})
    vid = res.get("voice_id", a.voice_id)
    print(f"✔ im Konto als „{a.name}“: {vid}")
    print(f"  Im Storyboard nutzen: python3 tools/elevenlabs.py use {vid}")


def cmd_use(a) -> None:
    pdir = project_dir(a.project)

    def apply(sb: dict) -> None:
        v = sb.setdefault("voice", {})
        v["backend"] = "elevenlabs"
        el = v.setdefault("elevenlabs", {})
        el["voiceId"] = a.voice_id
        el["model"] = a.model or el.get("model") or DEFAULT_MODEL
        el.setdefault("settings", dict(DEFAULT_SETTINGS))
        if a.name:
            el["name"] = a.name
    sb = patch_sb(pdir, apply)
    el = sb["voice"]["elevenlabs"]
    print(f"✔ voice.backend = elevenlabs, Stimme {el['voiceId']}, Modell {el['model']}")
    chars = sum(len(s["narration"]) for s in sb["scenes"])
    print(f"  Sprechtext: {chars} Zeichen. Vertonen (kostet Credits): python3 tools/tts.py --allow-cloud")


def cmd_quota(a) -> None:
    q = quota()
    if not q:
        die("Kontingent nicht lesbar – dem API-Key fehlt die Berechtigung „User: Lesen“ (user_read). "
            "Verbrauch dann im ElevenLabs-Konto ansehen.")
    used, limit = q
    print(f"Credits: {used} von {limit} verbraucht, {limit - used} frei")
    try:
        sb = load_sb(project_dir(a.project))
        chars = sum(len(s["narration"]) for s in sb["scenes"])
        print(f"Dieses Video: ≈ {chars} Zeichen pro kompletter Vertonung (+ Wiederholungen bei Fehlern)")
    except SystemExit:
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", dest="project", help="Videoordner (Default: video/)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("voices", help="Stimmbibliothek durchsuchen")
    v.add_argument("--language", default="de")
    v.add_argument("--gender", choices=["male", "female", "neutral"])
    v.add_argument("--age", choices=["young", "middle_aged", "old"])
    v.add_argument("--use-case", help="z. B. narrative_story, informative_educational, conversational, advertisement")
    v.add_argument("--search")
    v.add_argument("--sort", default="usage_character_count_1y",
                   choices=["created_date", "usage_character_count_1y", "trending", "cloned_by_count"])
    v.add_argument("--limit", type=int, default=15)
    v.add_argument("--page", type=int, default=0)
    v.add_argument("--previews", action="store_true", help="Hörproben nach video/review/stimmen/ laden")
    sub.add_parser("mine", help="Stimmen im eigenen Konto")
    d = sub.add_parser("add", help="Bibliotheksstimme ins eigene Konto übernehmen")
    d.add_argument("public_owner_id")
    d.add_argument("voice_id")
    d.add_argument("--name", required=True)
    u = sub.add_parser("use", help="Stimme im Storyboard eintragen")
    u.add_argument("voice_id")
    u.add_argument("--model", help=f"Default {DEFAULT_MODEL}; ausdrucksstärker: eleven_v3, eleven_v4")
    u.add_argument("--name", help="Anzeigename (nur zur Doku im Storyboard)")
    sub.add_parser("quota", help="Credits")
    a = ap.parse_args()
    {"voices": cmd_voices, "mine": cmd_mine, "add": cmd_add, "use": cmd_use, "quota": cmd_quota}[a.cmd](a)


if __name__ == "__main__":
    main()
