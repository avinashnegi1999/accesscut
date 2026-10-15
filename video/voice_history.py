"""Find which ElevenLabs voice spoke a given line, from the account's generation history.

    python video/voice_history.py "Three hundred and fifteen"
"""
import json
import os
import sys
import urllib.request

needle = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
url, seen = "https://api.elevenlabs.io/v1/history?page_size=1000", {}
req = urllib.request.Request(url, headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]})
items = json.loads(urllib.request.urlopen(req, timeout=60).read()).get("history", [])
for it in items:
    if needle in (it.get("text") or "").lower():
        key = (it.get("voice_name"), it.get("voice_id"), it.get("model_id"))
        seen.setdefault(key, []).append(it.get("text", "")[:70])
print(f"{len(items)} history items searched")
for (name, vid, model), texts in seen.items():
    print(f"{name} ({vid}, {model}): {len(texts)} matches, e.g. {texts[0]!r}")
if not seen:
    print("no match")
