"""Try voice settings on the opening lines.

    python video/voice_try.py <out_name> <voice_name_prefix> '<json settings>'
settings: {"model": ..., "stability": ..., "similarity_boost": ..., "style": ..., "speed": ..., "language_code": optional}
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
TEXT = "A contractor's last day. You remove their Payroll access. They still have it."
out, prefix, cfg = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])


def call(path, body=None):
    req = urllib.request.Request("https://api.elevenlabs.io/v1" + path, data=json.dumps(body).encode() if body else None,
                                 headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"})
    try:
        return urllib.request.urlopen(req, timeout=120).read()
    except urllib.error.HTTPError as e:
        sys.exit(f"{e.code}: {e.read()[:300].decode()}")


vid = next(v["voice_id"] for v in json.loads(call("/voices"))["voices"] if v["name"].startswith(prefix))
body = {"text": TEXT, "model_id": cfg["model"],
        "voice_settings": {k: cfg[k] for k in ("stability", "similarity_boost", "style", "speed")} | {"use_speaker_boost": True}}
if cfg.get("language_code"):
    body["language_code"] = cfg["language_code"]
(HERE / "samples").mkdir(exist_ok=True)
(HERE / "samples" / f"{out}.mp3").write_bytes(call(f"/text-to-speech/{vid}?output_format=mp3_44100_128", body))
print("wrote samples/" + out + ".mp3")
