"""Turn the human-readable script (script-v3-draft.md) into timed voice lines.

    python video/script_from_md.py   ->  video/script_v3.json

`> text` is a spoken line. `· pause Ns ·` sets the silence before the next line (default 0.6 s).
`· pause ·` with no number means "hold for the live clip" (12 s). `## N. Title` starts a scene.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SCENES = ["open", "routes", "keep", "meet", "run", "live", "refuse", "query", "proof", "end"]
md = (HERE / "script-v3-draft.md").read_text(encoding="utf-8")

lines, scene, gap = [], None, 0.6
for raw in md.splitlines():
    s = raw.strip()
    if m := re.match(r"## (\d+)\.", s):
        scene = SCENES[int(m.group(1)) - 1]
    elif m := re.match(r"· pause ([\d.]+)s ·", s):
        gap = float(m.group(1))
    elif s.startswith("· pause ·"):
        gap = 12.0
    elif s.startswith("> ") and scene:
        lines.append({"scene": scene, "gap": gap, "text": s[2:].strip()})
        gap = 0.6

base = json.loads((HERE / "script.json").read_text(encoding="utf-8"))
out = {"_note": "Generated from script-v3-draft.md by script_from_md.py; edit the markdown, not this file.",
       "voice": base["voice"], "tail": 3.0, "lines": lines}
(HERE / "script_v3.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(len(lines), "lines,", sum(len(l["text"]) for l in lines), "characters")
