"""Join generated voice lines into one listening track, each line after its marked pause.

    python video/assemble_voice.py script_v3.json voice_v3 voiceover-v3.mp3
Also writes <out>.timing.json (start and length of every line) for fitting the film later.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
BIN = Path(r"C:/Users/avina/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-essentials_build/bin")
script_name, voice_dir, out_name = sys.argv[1:4]
script = json.loads((HERE / script_name).read_text(encoding="utf-8"))


def duration(path):
    return float(subprocess.run([str(BIN / "ffprobe.exe"), "-v", "error", "-show_entries", "format=duration",
                                 "-of", "default=nk=1:nw=1", str(path)], capture_output=True, text=True).stdout)


t, timing, args, filters = 0.0, [], [str(BIN / "ffmpeg.exe"), "-y"], []
for i, ln in enumerate(script["lines"]):
    mp3 = HERE / voice_dir / f"line_{i:02d}.mp3"
    start, dur = t + ln["gap"], duration(mp3)
    timing.append({"i": i, "scene": ln["scene"], "start": round(start, 3), "dur": round(dur, 3), "text": ln["text"]})
    args += ["-i", str(mp3)]
    ms = int(start * 1000)
    filters.append(f"[{i}:a]adelay={ms}|{ms},apad[a{i}]")
    t = start + dur
total = t + script.get("tail", 3.0)
mix = "".join(f"[a{i}]" for i in range(len(timing)))
filters.append(f"{mix}amix=inputs={len(timing)}:normalize=0,atrim=0:{total:.3f},loudnorm=I=-16:TP=-1.5:LRA=11[out]")
args += ["-filter_complex", ";".join(filters), "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "192k", str(HERE / out_name)]
subprocess.run(args, check=True, capture_output=True)
(HERE / (out_name + ".timing.json")).write_text(json.dumps({"total": round(total, 3), "lines": timing}, indent=1), encoding="utf-8")
m, s = divmod(total, 60)
print(f"wrote {out_name}: {int(m)}:{s:04.1f}, {len(timing)} lines")
