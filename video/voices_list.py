"""List the ElevenLabs voices this key can use, and the remaining character quota."""
import json
import os
import urllib.request


def get(path):
    req = urllib.request.Request("https://api.elevenlabs.io/v1" + path, headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read()[:300].decode()}


sub = get("/user/subscription")
print("subscription:", sub.get("tier"), sub.get("character_count"), "/", sub.get("character_limit"), sub.get("body", ""))
voices = get("/voices")
for v in voices.get("voices", []):
    lab = v.get("labels", {})
    print(f"{v['name']:30} {lab.get('gender', ''):7} {lab.get('age', ''):12} {lab.get('accent', ''):12} "
          f"{lab.get('descriptive') or lab.get('description') or ''}")
if "voices" not in voices:
    print(voices)
