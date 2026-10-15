"""Record real agent runs as JSON traces for the film (the film replays them, it never invents steps).

    python video/capture.py      ->  video/trace_payroll.json, video/trace_wiki.json
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import agent  # noqa: E402

for name, inject in (("payroll", True), ("wiki", False)):
    events = []
    out = agent.run(name, inject=inject, emit=lambda kind, **d: events.append({"kind": kind, **d}))
    path = HERE / f"trace_{name}.json"
    path.write_text(json.dumps({"model": agent.MODEL, "result": out, "events": events}, indent=1, default=list))
    print(path.name, out["status"], len(events), "events")
