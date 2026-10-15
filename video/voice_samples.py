"""Speak the same two lines in several voices so they can be compared by ear.

    python video/voice_samples.py Sarah Alice Bella Lily Matilda   ->  video/samples/<name>.mp3
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
TEXT = "A contractor's last day. You remove their Payroll access. They still have it."


def call(path, body=None):
    req = urllib.request.Request("https://api.elevenlabs.io/v1" + path, data=json.dumps(body).encode() if body else None,
                                 headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=120).read()


voices = {v["name"].split(" ")[0]: v["voice_id"] for v in json.loads(call("/voices"))["voices"]}
cfg = json.loads((HERE / "script.json").read_text(encoding="utf-8"))["voice"]
(HERE / "samples").mkdir(exist_ok=True)
for name in sys.argv[1:]:
    audio = call(f"/text-to-speech/{voices[name]}?output_format=mp3_44100_128",
                 {"text": TEXT, "model_id": cfg["model"],
                  "voice_settings": {"stability": cfg["stability"], "similarity_boost": cfg["similarity_boost"],
                                     "style": cfg["style"], "speed": cfg["speed"], "use_speaker_boost": True}})
    (HERE / "samples" / f"{name}.mp3").write_bytes(audio)
    print("wrote samples/" + name + ".mp3")
