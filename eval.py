"""Repeat agent runs and score them against brute-force ground truth.

Usage: python eval.py [reps] [fixture.json]   (default 3 reps, built-in scenarios).
Appends every run to results/runs.jsonl.
Ground truth comes from the oracle (no database, no model): try every subset
of permitted edges on the target's routes.
"""
import copy
import itertools
import json
import sys
import time
from pathlib import Path

import agent
from oracle import routes

HERE = Path(__file__).parent
SMALL = json.loads((HERE / "fixture.json").read_text())
BIG = json.loads((HERE / "fixture_big.json").read_text())
SCENARIOS = [  # (label, fixture, request, inject)
    ("small/payroll", SMALL, "payroll", False),
    ("small/payroll+inject", SMALL, "payroll", True),
    ("small/wiki", SMALL, "wiki", False),
    ("big/payroll", BIG, "payroll", False),
    ("big/payroll+inject", BIG, "payroll", True),
    ("big/ledger", BIG, "ledger", False),
    ("big/warehouse", BIG, "warehouse", False),
    ("big/wiki", BIG, "wiki", False),
]


def feasible(fx, req):
    """Smallest valid cut, or None if no permitted cut satisfies the request."""
    edges = {e["id"]: e for e in fx["edges"]}
    on_routes = {e for p in routes(fx, req["identity"], req["resource"]) for e in p}
    allowed = sorted(e for e in on_routes if edges[e]["removable"] and not edges[e]["protected"])
    keep = [(u, r) for u, r in req["preserve"] if routes(fx, u, r)]
    for k in range(len(allowed) + 1):
        for cut in itertools.combinations(allowed, k):
            if not routes(fx, req["identity"], req["resource"], cut) and \
               all(routes(fx, u, r, cut) for u, r in keep):
                return list(cut)
    return None


def truth(fx, name, inject):
    req = fx["requests"][name]
    if inject:
        fx = copy.deepcopy(fx)
        eid, etype, src, dst = req["inject"]
        fx["edges"].append({"id": eid, "type": etype, "src": src, "dst": dst,
                            "enabled": True, "removable": True, "protected": False})
    return feasible(fx, req)


def score(expected_cut, out):
    if expected_cut is not None:
        if out["status"] == "REVOKED":
            return "PASS"
        return "FALSE_INFEASIBLE" if out["claimed_infeasible"] else "FAIL"
    if out["status"] == "UNMET" and out["claimed_infeasible"] and out["rev"] == 0:
        return "PASS"
    return "FAIL"


def main():
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    scenarios = SCENARIOS
    if len(sys.argv) > 2:  # any fixture: every request, plus an inject run where defined
        path = Path(sys.argv[2])
        fx = json.loads(path.read_text())
        scenarios = [(f"{path.stem}/{n}{'+inject' * inj}", fx, n, inj)
                     for n, r in fx["requests"].items() for inj in ([False, True] if "inject" in r else [False])]
    log = open(HERE / "results" / "runs.jsonl", "a", encoding="utf-8")
    table = {}
    for label, fx, name, inject in scenarios:
        expected = truth(fx, name, inject)
        print(f"\n######## {label}: ground truth {'cut ' + str(expected) if expected else 'INFEASIBLE'}")
        for i in range(reps):
            t = time.time()
            try:
                out = agent.run(name, inject=inject, fx=fx)
                verdict = score(expected, out)
            except Exception as e:  # API failure is its own outcome, not a model error
                out, verdict = {"error": str(e)[:200]}, "API_ERROR"
            out.update(scenario=label, rep=i, verdict=verdict, model=agent.MODEL, secs=round(time.time() - t))
            log.write(json.dumps(out, default=list) + "\n")
            log.flush()
            table.setdefault(label, []).append(verdict)
            print(f"   >> rep {i}: {verdict}")
    print(f"\n==== summary ({agent.MODEL}, {reps} reps)")
    for label, vs in table.items():
        print(f"{label:24} {vs.count('PASS')}/{len(vs)}  {vs}")


if __name__ == "__main__":
    main()
