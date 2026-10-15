"""AccessCut: remove one identity's access to one resource across every modeled route.

Tools (for the agent): inspect_access, evaluate_plan, apply_plan, verify.
Graph state lives in FalkorDB; a (:Meta {rev}) node versions every mutation.
"""
import json

from falkordb import FalkorDB

MAX_DEPTH = 8
# edge type -> (allowed source labels, allowed target labels)
TYPES = {
    "MEMBER_OF": ({"Identity", "Group"}, {"Group"}),
    "CAN_ASSUME": ({"Identity"}, {"Identity"}),
    "GRANTS_ACCESS": ({"Identity", "Group"}, {"Resource"}),
}
PATHS_Q = (
    "MATCH p=(u:Identity {id:$u})-[:MEMBER_OF|CAN_ASSUME|GRANTS_ACCESS*1.."
    f"{MAX_DEPTH}]->(r:Resource {{id:$r}}) "
    "WHERE all(e IN relationships(p) WHERE e.enabled AND NOT e.id IN $cut) "
    "RETURN [e IN relationships(p) | e.id]"
)


def validate(fx):
    """Reject fixtures outside the supported model instead of silently truncating."""
    labels = {}
    for n in fx["nodes"]:
        if n["id"] in labels:
            raise ValueError(f"duplicate node {n['id']}")
        if n["label"] not in ("Identity", "Group", "Resource"):
            raise ValueError(f"bad label {n['label']}")
        labels[n["id"]] = n["label"]
    seen, adj = set(), {}
    for e in fx["edges"]:
        if e["id"] in seen:
            raise ValueError(f"duplicate edge {e['id']}")
        seen.add(e["id"])
        if e["type"] not in TYPES:
            raise ValueError(f"unsupported edge type {e['type']}")
        srcs, dsts = TYPES[e["type"]]
        if labels.get(e["src"]) not in srcs or labels.get(e["dst"]) not in dsts:
            raise ValueError(f"edge {e['id']}: {e['type']} not allowed {e['src']}->{e['dst']}")
        adj.setdefault(e["src"], []).append(e["dst"])

    depth, active = {}, set()

    def longest(n):
        if n in active:
            raise ValueError(f"cycle through {n}")
        if n not in depth:
            active.add(n)
            depth[n] = max((1 + longest(m) for m in adj.get(n, [])), default=0)
            active.discard(n)
        return depth[n]

    worst = max((longest(n) for n in labels), default=0)
    if worst > MAX_DEPTH:
        raise ValueError(f"path depth {worst} exceeds {MAX_DEPTH}")


class AccessCut:
    def __init__(self, graph="accesscut", host="localhost", port=6379):
        self.g = FalkorDB(host=host, port=port).select_graph(graph)

    def _q(self, q, params=None):
        return self.g.query(q, params or {}).result_set

    # ---------- setup ----------
    def seed(self, fx):
        validate(fx)
        try:
            self.g.delete()
        except Exception:
            pass  # graph did not exist yet
        for label in ("Identity", "Group", "Resource"):
            ids = [n["id"] for n in fx["nodes"] if n["label"] == label]
            self._q(f"UNWIND $ids AS i CREATE (:{label} {{id:i}})", {"ids": ids})
        for t in TYPES:
            es = [e for e in fx["edges"] if e["type"] == t]
            self._q(
                f"UNWIND $es AS e MATCH (a {{id:e.src}}), (b {{id:e.dst}}) "
                f"CREATE (a)-[:{t} {{id:e.id, enabled:e.enabled, removable:e.removable, protected:e.protected}}]->(b)",
                {"es": es},
            )
        self._q("CREATE (:Meta {rev:0})")

    # ---------- queries ----------
    def rev(self):
        return self._q("MATCH (m:Meta) RETURN m.rev")[0][0]

    def paths(self, u, r, cut=()):
        return sorted(tuple(row[0]) for row in self._q(PATHS_Q, {"u": u, "r": r, "cut": list(cut)}))

    def edges(self, ids):
        rows = self._q(
            "MATCH (a)-[e]->(b) WHERE e.id IN $ids "
            "RETURN e.id, type(e), a.id, b.id, e.enabled, e.removable, e.protected",
            {"ids": list(ids)},
        )
        keys = ("type", "src", "dst", "enabled", "removable", "protected")
        return {r[0]: dict(zip(keys, r[1:])) for r in rows}

    def prepare(self, req):
        """Request intake: preserved pairs already unreachable cannot be 'kept'; set them aside once,
        so evaluate_plan and verify judge the same pairs."""
        keep = [[u, r] for u, r in req["preserve"] if self.paths(u, r)]
        gone = [[u, r] for u, r in req["preserve"] if [u, r] not in keep]
        return {**req, "preserve": keep, "not_applicable_preserve": gone}

    def snapshot(self):
        """Every edge with its current flags (for display)."""
        rows = self._q("MATCH (a)-[e]->(b) RETURN e.id, type(e), a.id, b.id, e.enabled, e.removable, e.protected")
        keys = ("id", "type", "src", "dst", "enabled", "removable", "protected")
        return [dict(zip(keys, r)) for r in rows]

    # ---------- agent tools ----------
    def inspect_access(self, req):
        """Every enabled route, edge details, and routes no permitted edit can break."""
        rev = self.rev()
        ps = self.paths(req["identity"], req["resource"])
        ed = self.edges({e for p in ps for e in p})
        permitted = sorted(e for e in ed if ed[e]["removable"] and not ed[e]["protected"])
        blocking = [p for p in ps if not any(e in permitted for e in p)]
        # What each permitted edge does if cut ALONE. Combinations can still collide; evaluate_plan checks those.
        keep = [(u, r) for u, r in req["preserve"] if self.paths(u, r)]
        impact = {
            e: {"closes_routes": [p for p in ps if e in p],
                "breaks_preserved": [[u, r] for u, r in keep if not self.paths(u, r, [e])]}
            for e in permitted
        }
        return {"rev": rev, "paths": ps, "edges": ed, "blocking_paths": blocking, "edge_impact": impact}

    def evaluate_plan(self, req, cut, rev):
        """Simulate disabling `cut`; list every reason the plan is unacceptable."""
        reasons = []
        cur = self.rev()
        if rev != cur:
            reasons.append(f"STALE: plan rev {rev}, graph rev {cur}")
        ed = self.edges(cut)
        for e in cut:
            if e not in ed:
                reasons.append(f"UNKNOWN_EDGE: {e}")
            elif ed[e]["protected"] or not ed[e]["removable"]:
                reasons.append(f"PROTECTED: {e}")
        left = self.paths(req["identity"], req["resource"], cut)
        if left:
            reasons.append(f"ROUTES_REMAIN: {left}")
        keep = [(u, r) for u, r in req["preserve"] if self.paths(u, r)]
        for u, r in keep:
            if not self.paths(u, r, cut):
                # Edges whose removal from the plan would restore this pair.
                culprits = [e for e in cut if self.paths(u, r, [c for c in cut if c != e])]
                reasons.append(f"COLLATERAL: {u}->{r} lost; dropping any of {culprits} from the plan restores it")
        # For each route still open: permitted edges that close it without collateral when added to this cut.
        safe = lambda c: all(self.paths(u, r, c) for u, r in keep)
        open_edges = self.edges({e for p in left for e in p})
        permitted = {e for e, d in open_edges.items() if d["removable"] and not d["protected"]}
        extend = {" > ".join(p): [e for e in p if e in permitted and safe(list(cut) + [e])] for p in left}
        return {"ok": not reasons, "rev": cur, "reasons": reasons, "remaining": left,
                "safe_additions_per_open_route": extend}

    def apply_plan(self, req, cut, rev, op_key):
        """Disable `cut` only if valid at `rev`. Same op_key twice is a no-op replay."""
        done = self._q("MATCH (o:Op {key:$k}) RETURN o.result", {"k": op_key})
        if done:
            return json.loads(done[0][0]) | {"replayed": True}
        ev = self.evaluate_plan(req, cut, rev)
        if not ev["ok"]:
            return {"status": "REJECTED", **ev}
        result = {"status": "APPLIED", "cut": list(cut), "from_rev": rev, "to_rev": rev + 1}
        # One query = one atomic write: rev check, edge disable, rev bump, audit record.
        # ponytail: single-writer assumption; a second backend would need a real lock.
        rows = self._q(
            "MATCH (m:Meta {rev:$rev}) SET m.rev = m.rev + 1 "
            "WITH m MATCH ()-[e]->() WHERE e.id IN $cut SET e.enabled = false "
            "WITH DISTINCT m CREATE (:Op {key:$k, identity:$u, resource:$r, cut:$cut, "
            "from_rev:$rev, to_rev:m.rev, result:$res}) RETURN m.rev",
            {"rev": rev, "cut": list(cut), "k": op_key, "u": req["identity"],
             "r": req["resource"], "res": json.dumps(result)},
        )
        if not rows:
            return {"status": "REJECTED", "reasons": [f"STALE: graph moved past rev {rev}"]}
        return result

    def verify(self, req):
        """Postcondition check against current graph state."""
        rev = self.rev()
        left = self.paths(req["identity"], req["resource"])
        lost = [[u, r] for u, r in req["preserve"] if not self.paths(u, r)]
        status = "REVOKED" if not left and not lost else "UNMET"
        return {"status": status, "rev": rev, "remaining": left, "lost_preserved": lost}

    # ---------- independent mutation control (not an agent tool) ----------
    def add_edge(self, edge_id, etype, src, dst):
        if etype not in TYPES:
            raise ValueError(f"unsupported edge type {etype}")
        # ponytail: no cycle/depth recheck on live edits; re-run validate() on an export if edits get rich.
        rows = self._q(
            f"MATCH (a {{id:$s}}), (b {{id:$d}}), (m:Meta) "
            f"CREATE (a)-[:{etype} {{id:$id, enabled:true, removable:true, protected:false}}]->(b) "
            "SET m.rev = m.rev + 1 RETURN m.rev",
            {"s": src, "d": dst, "id": edge_id},
        )
        if not rows:
            raise ValueError(f"unknown endpoint {src} or {dst}")
        return rows[0][0]
