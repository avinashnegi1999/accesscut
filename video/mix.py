"""Lay each voice line at its start time and mux it under the silent film.

    python video/mix.py   ->  video/accesscut-film-final.mp4   (needs accesscut-film-v2.mp4 and voice/)
Start times come from build2.py, the same numbers the film was timed to.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from build2 import timing  # noqa: E402

FFMPEG = r"C:/Users/avina/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-essentials_build/bin/ffmpeg.exe"

tm = timing()
assert tm["measured"] == len(tm["lines"]), "generate every voice line first (voice.py), then rebuild and re-record"
args = [FFMPEG, "-y", "-i", str(HERE / "accesscut-film-v2.mp4")]
filters, labels = [], []
for k, ln in enumerate(tm["lines"], start=1):
    args += ["-i", str(HERE / "voice" / f"line_{ln['i']:02d}.mp3")]
    ms = int(ln["start"] * 1000)
    filters.append(f"[{k}:a]adelay={ms}|{ms},apad[a{k}]")
    labels.append(f"[a{k}]")
filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0,atrim=0:{tm['total']},loudnorm=I=-16:TP=-1.5:LRA=11[aout]")
args += ["-filter_complex", ";".join(filters), "-map", "0:v", "-map", "[aout]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
         str(HERE / "accesscut-film-final.mp4")]
subprocess.run(args, check=True)
print("wrote accesscut-film-final.mp4")
