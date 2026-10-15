"""Inline the recorded traces into the film page (file:// pages cannot fetch local JSON).

    python video/build.py   ->  video/film.html  (open it to preview; ?record for the recorder)
"""
from pathlib import Path

HERE = Path(__file__).parent
html = (HERE / "film.template.html").read_text(encoding="utf-8")
for name in ("payroll", "wiki"):
    html = html.replace(f"/*TRACE_{name.upper()}*/null", (HERE / f"trace_{name}.json").read_text(encoding="utf-8"))
(HERE / "film.html").write_text(html, encoding="utf-8")
print("wrote film.html")
