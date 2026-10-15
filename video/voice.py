"""Generate one ElevenLabs audio file per script line, with neighbouring lines as context for
natural pacing.

    python video/voice.py            ->  video/voice/line_NN.mp3   (skips lines already generated)
    python video/voice.py --redo 5   ->  regenerate line 5 only

Needs ELEVENLABS_API_KEY. ELEVEN_VOICE_ID picks the voice; otherwise the first available of a
few calm, mid-pitch stock voices is used.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
API = "https://api.elevenlabs.io/v1"
KEY = os.environ["ELEVENLABS_API_KEY"]
CALM = ["Suzie", "George", "Brian", "Daniel", "Eric", "Chris", "Will"]


def call(path, body=None):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode() if body else None,
                                 headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def pick_voice(wanted=None):
    if os.environ.get("ELEVEN_VOICE_ID"):
        return os.environ["ELEVEN_VOICE_ID"], os.environ["ELEVEN_VOICE_ID"]
    voices = json.loads(call("/voices"))["voices"]
    by_name = {v["name"].split(" ")[0]: v for v in voices}
    for name in ([wanted] if wanted else []) + CALM:
        if name in by_name:
            return by_name[name]["voice_id"], by_name[name]["name"]
    return voices[0]["voice_id"], voices[0]["name"]


def main():
    script = json.loads((HERE / os.environ.get("VOICE_SCRIPT", "script.json")).read_text(encoding="utf-8"))
    lines, cfg = script["lines"], script["voice"]
    redo = {int(sys.argv[sys.argv.index("--redo") + 1])} if "--redo" in sys.argv else set()
    out_dir = HERE / os.environ.get("VOICE_DIR", "voice")
    out_dir.mkdir(exist_ok=True)
    voice_id, name = pick_voice(cfg.get("name"))
    print("voice:", name)
    for i, ln in enumerate(lines):
        out = out_dir / f"line_{i:02d}.mp3"
        if out.exists() and i not in redo:
            continue
        body = {"text": ln["text"], "model_id": cfg["model"],
                "voice_settings": {"stability": cfg["stability"], "similarity_boost": cfg["similarity_boost"],
                                   "style": cfg["style"], "speed": cfg["speed"], "use_speaker_boost": True},
                "previous_text": lines[i - 1]["text"] if i else None,
                "next_text": lines[i + 1]["text"] if i + 1 < len(lines) else None}
        if cfg.get("language_code"):
            body["language_code"] = cfg["language_code"]
        out.write_bytes(call(f"/text-to-speech/{voice_id}?output_format=mp3_44100_128", body))
        print(f"line {i:02d}: {ln['text']}")


if __name__ == "__main__":
    main()
