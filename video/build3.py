"""Build film3.html timed to voiceover-v3.mp3.

    python video/build3.py            full film
    python video/build3.py --demo 6   only the first 6 voice lines (a short preview), plus a cut of the audio
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
FFMPEG = r"C:/Users/avina/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-essentials_build/bin/ffmpeg.exe"

tm = json.loads((HERE / "voiceover-v3.mp3.timing.json").read_text(encoding="utf-8"))
audio = HERE / "voiceover-v3.mp3"
if "--demo" in sys.argv:
    n = int(sys.argv[sys.argv.index("--demo") + 1])
    tm["lines"] = tm["lines"][:n]
    last = tm["lines"][-1]
    tm["total"] = round(last["start"] + last["dur"] + 0.8, 3)
    audio = HERE / "voiceover-v3-demo.mp3"
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", str(HERE / "voiceover-v3.mp3"), "-t", str(tm["total"]),
                    "-af", f"afade=t=out:st={tm['total'] - 0.5}:d=0.5", str(audio)], check=True)

html = (HERE / "film3.template.html").read_text(encoding="utf-8")
inline = {"TIMING": tm, "FIXTURE": json.loads((HERE.parent / "fixture_big.json").read_text(encoding="utf-8")),
          "RUN": json.loads((HERE / "trace_big_payroll.json").read_text(encoding="utf-8")),
          "REFUSE": json.loads((HERE / "trace_big_wiki.json").read_text(encoding="utf-8"))}
for key, val in inline.items():
    assert f"/*{key}*/null" in html
    html = html.replace(f"/*{key}*/null", json.dumps(val))
(HERE / "film3.html").write_text(html, encoding="utf-8")
print(f"film3.html: {tm['total']:.1f}s, {len(tm['lines'])} lines; audio {audio.name}")
