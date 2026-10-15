"""Keep running the real agent until one payroll run shows every behavior worth filming:
a COLLATERAL rejection, the outside change, a STALE rejection, and a verified REVOKED end.

    python video/capture_rich.py [max_tries]   ->  video/trace_payroll.json
Every attempt is real; the film only picks which real run to replay.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import agent  # noqa: E402


def shows_everything(events, out):
    text = json.dumps(events)
    return "COLLATERAL" in text and "STALE" in text and out["status"] == "REVOKED"


for attempt in range(1, int(sys.argv[1]) + 1 if len(sys.argv) > 1 else 9):
    events = []
    out = agent.run("payroll", inject=True, emit=lambda kind, **d: events.append({"kind": kind, **d}))
    ok = shows_everything(events, out)
    print(f"attempt {attempt}: {out['status']}, {len(events)} events, all behaviors: {ok}")
    if ok:
        (HERE / "trace_payroll.json").write_text(
            json.dumps({"model": agent.MODEL, "attempt": attempt, "result": out, "events": events}, indent=1, default=list))
        break
else:
    print("no run showed every behavior; trace_payroll.json unchanged")
