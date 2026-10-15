"""Scenario checks for AccessCut against a live FalkorDB. Run: python check.py"""
import copy
import json
from pathlib import Path

from accesscut import AccessCut, validate
from oracle import routes

FX = json.loads((Path(__file__).parent / "fixture.json").read_text())
PAY, WIKI = FX["requests"]["payroll"], FX["requests"]["wiki"]


def main():
    ac = AccessCut(graph="accesscut_check")
    ac.seed(FX)

    # 1. FalkorDB routes match the independent oracle.
    look = ac.inspect_access(PAY)
    assert look["paths"] == routes(FX, "c.lee", "payroll") == [("e1",), ("e2", "e3", "e4"), ("e5", "e6")], look["paths"]
    assert look["blocking_paths"] == []
    imp = look["edge_impact"]
    assert sorted(imp) == ["e1", "e2", "e3", "e5"], imp
    assert imp["e2"]["breaks_preserved"] == [["c.lee", "training"]] and imp["e3"]["breaks_preserved"] == [], imp
    rev0 = look["rev"]

    # 2. Deleting only the direct grant leaves two routes.
    ev = ac.evaluate_plan(PAY, ["e1"], rev0)
    assert not ev["ok"] and ev["remaining"] == [("e2", "e3", "e4"), ("e5", "e6")], ev
    assert ev["safe_additions_per_open_route"] == {"e2 > e3 > e4": ["e3"], "e5 > e6": ["e5"]}, ev

    # 3. Protected edits rejected.
    ev = ac.evaluate_plan(PAY, ["e1", "e4", "e5"], rev0)
    assert any(r.startswith("PROTECTED: e4") for r in ev["reasons"]), ev

    # 4. Cutting contractor membership kills Training: collateral rejected.
    ev = ac.evaluate_plan(PAY, ["e1", "e2", "e5"], rev0)
    assert ev["reasons"] == ["COLLATERAL: c.lee->training lost; dropping any of ['e2'] from the plan restores it"], ev

    # 5. Good plan passes, applies, verifies; oracle agrees on the mutated fixture.
    good = ["e1", "e3", "e5"]
    assert ac.evaluate_plan(PAY, good, rev0)["ok"]
    res = ac.apply_plan(PAY, good, rev0, op_key="op-1")
    assert res["status"] == "APPLIED" and res["to_rev"] == rev0 + 1, res
    v = ac.verify(PAY)
    assert v["status"] == "REVOKED", v
    cut_fx = copy.deepcopy(FX)
    for e in cut_fx["edges"]:
        if e["id"] in good:
            e["enabled"] = False
    assert routes(cut_fx, "c.lee", "payroll") == ac.paths("c.lee", "payroll") == []
    assert routes(cut_fx, "c.lee", "training") == ac.paths("c.lee", "training") != []

    # 6. Replaying the same operation is neutral.
    again = ac.apply_plan(PAY, good, rev0, op_key="op-1")
    assert again.get("replayed") and ac.rev() == rev0 + 1, again

    # 7. Stale plan rejected.
    stale = ac.apply_plan(PAY, ["e1"], rev0, op_key="op-2")
    assert stale["status"] == "REJECTED" and any("STALE" in r for r in stale["reasons"]), stale

    # 8. Independent new grant reopens access and bumps revision.
    ac.add_edge("e20", "MEMBER_OF", "c.lee", "finance-readers")
    v = ac.verify(PAY)
    assert v["status"] == "UNMET" and v["remaining"] == [("e20", "e4")] and v["rev"] == rev0 + 2, v

    # 9. Restart: fresh client sees the same state and audit.
    ac2 = AccessCut(graph="accesscut_check")
    assert ac2.rev() == rev0 + 2 and ac2.apply_plan(PAY, good, rev0, "op-1").get("replayed")

    # 10. Protected-only route is infeasible, with evidence.
    look = ac.inspect_access(WIKI)
    assert look["blocking_paths"] == [("e7", "e8")], look

    # 11. Unsupported fixtures rejected.
    for bad in (
        {"nodes": [{"id": "a", "label": "Group"}, {"id": "b", "label": "Group"}],
         "edges": [{"id": "x", "type": "MEMBER_OF", "src": "a", "dst": "b"},
                   {"id": "y", "type": "MEMBER_OF", "src": "b", "dst": "a"}]},
        {"nodes": [{"id": "g", "label": "Group"}, {"id": "i", "label": "Identity"}],
         "edges": [{"id": "x", "type": "CAN_ASSUME", "src": "g", "dst": "i"}]},
        {"nodes": [{"id": f"g{i}", "label": "Group"} for i in range(10)],
         "edges": [{"id": f"x{i}", "type": "MEMBER_OF", "src": f"g{i}", "dst": f"g{i+1}"} for i in range(9)]},
    ):
        try:
            validate(bad)
            raise AssertionError(f"accepted bad fixture {bad}")
        except ValueError:
            pass

    # 11b. A preserved pair that was never reachable is set aside at intake, not reported as lost.
    ac.seed(FX)
    req = ac.prepare({**PAY, "preserve": PAY["preserve"] + [["a.kim", "training"]]})
    assert req["not_applicable_preserve"] == [["a.kim", "training"]], req
    ac.apply_plan(req, ["e1", "e3", "e5"], ac.rev(), op_key="op-x")
    assert ac.verify(req)["status"] == "REVOKED"

    # 12. No database: fail visibly.
    try:
        AccessCut(graph="x", port=1).rev()
        raise AssertionError("ran without a database")
    except Exception as e:
        assert not isinstance(e, AssertionError)

    ac.g.delete()
    print("all 12 checks passed")


if __name__ == "__main__":
    main()
