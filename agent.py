"""AccessCut agent loop: an LLM proposes edge cuts, FalkorDB-backed tools judge them.

Usage: python agent.py payroll|wiki [--inject] [--fixture path.json]
  --inject  adds a new grant right after the first accepted evaluation,
            so the agent's plan goes stale and it must re-inspect and replan.
Uses any OpenAI-compatible chat API:
  OPENAI_API_KEY (default provider), AGENT_MODEL overrides the model.
  For Gemini: AGENT_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
              OPENAI_API_KEY=<gemini key>, AGENT_MODEL=gemini-3-flash-preview
"""
import json
import os
import sys
import time
import uuid
from pathlib import Path

import openai

from accesscut import AccessCut

MODEL = os.environ.get("AGENT_MODEL", "gpt-5.4-mini")
MAX_TURNS = 20
FX = json.loads((Path(__file__).parent / "fixture.json").read_text())

PLAN_PARAMS = {"type": "object", "required": ["edge_ids", "rev"],
               "properties": {"edge_ids": {"type": "array", "items": {"type": "string"}},
                              "rev": {"type": "integer"}}}
NO_PARAMS = {"type": "object", "properties": {}}


def _tool(name, description, params):
    return {"type": "function", "function": {"name": name, "description": description, "parameters": params}}


TOOLS = [
    _tool("inspect_access", "List every enabled route from the identity to the resource, edge details "
          "(removable/protected), routes that contain no permitted edit, and the graph revision.", NO_PARAMS),
    _tool("evaluate_plan", "Simulate disabling the given edge ids at a revision. Returns ok plus every rejection "
          "reason (PROTECTED, ROUTES_REMAIN, COLLATERAL, STALE, UNKNOWN_EDGE). Changes nothing.", PLAN_PARAMS),
    _tool("apply_plan", "Disable the given edge ids. Accepted only if the plan is valid at that exact revision.",
          PLAN_PARAMS),
    _tool("verify", "Check postconditions on the current graph: target unreachable, preserved pairs intact.",
          NO_PARAMS),
]

SYSTEM = """You remove one identity's access to one resource in a modeled access graph.
Access flows Identity -MEMBER_OF-> Group, Identity -CAN_ASSUME-> Identity, and ends with -GRANTS_ACCESS-> Resource.
You may only act through the tools. Only disable edges that are removable and not protected.
Never break the preserved identity-resource pairs. Always evaluate a plan before applying it,
read rejection reasons and replan, and call verify after applying.
A route is closed by disabling ANY one permitted edge on it; a protected edge elsewhere on the
route does not block that. Only routes listed in blocking_paths have no permitted edit.
inspect_access gives edge_impact: for each permitted edge, the routes it closes and the preserved
pairs it breaks when cut alone. Prefer, for every route, an edge with empty breaks_preserved,
including edges deep inside a route, not only the first hop. Edges safe alone can still break a
preserved pair together (it may rely on two alternative routes); if evaluate_plan reports
COLLATERAL, swap one of the involved edges for another candidate on the same route.
When evaluate_plan reports ROUTES_REMAIN, read safe_additions_per_open_route: edges you can add to
your current plan to close that route without collateral. An empty list for a route means your
current plan blocks every fix for it; then change an earlier choice instead of giving up.
Answer INFEASIBLE only if blocking_paths is non-empty, or after evaluate_plan has rejected every
combination you can form from permitted edges; start that answer with INFEASIBLE and the evidence.
Otherwise finish with a one-paragraph summary."""


def generate(client, messages, tries=6):
    """Retry rate limits and overloads; daily-quota errors fail at once."""
    for i in range(tries):
        try:
            return client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        except (openai.RateLimitError, openai.InternalServerError) as e:
            if "PerDay" in str(e) or "insufficient_quota" in str(e) or i == tries - 1:
                raise
            print(f"   .. model API {e.status_code}, retrying in 20s")
            time.sleep(20)


def print_event(kind, **d):
    """Default event sink: readable console trace."""
    if kind == "request":
        print(f"== request: {d['ask']} (model {d['model']})")
    elif kind == "inject":
        print(f"   !! outside change: grant {d['edge']} {d['src']} -{d['type']}-> {d['dst']} (rev now {d['rev']})")
    elif kind == "model":
        print(f"   model: {d['text']}")
    elif kind == "tool":
        print(f"-> {d['name']}({d['args']})\n   {json.dumps(d['out'])}")
    elif kind == "limit":
        print("!! turn limit reached")
    elif kind == "outcome":
        print(f"== outcome (from graph): {d['status']} at rev {d['rev']}")


def run(name, inject=False, fx=FX, emit=print_event):
    """Run one request; return graph outcome plus a trace summary for scoring.
    `emit(kind, **data)` receives each step; the demo UI streams these."""
    req = fx["requests"][name]
    ac = AccessCut(graph=f"accesscut_agent_{name}")
    ac.seed(fx)
    req = ac.prepare(req)
    client = openai.OpenAI(base_url=os.environ.get("AGENT_BASE_URL") or None)
    injected, pending = False, []
    stats = {"calls": 0, "rejected_applies": 0, "claimed_infeasible": False, "said": ""}

    def call(tool, args):
        nonlocal injected
        stats["calls"] += 1
        if tool == "inspect_access":
            return ac.inspect_access(req)
        if tool == "evaluate_plan":
            out = ac.evaluate_plan(req, list(args["edge_ids"]), int(args["rev"]))
            if inject and out["ok"] and not injected:
                injected = True
                eid, etype, src, dst = req["inject"]
                rev = ac.add_edge(eid, etype, src, dst)
                pending.append(dict(edge=eid, type=etype, src=src, dst=dst, rev=rev))  # shown after this step
            return out
        if tool == "apply_plan":
            out = ac.apply_plan(req, list(args["edge_ids"]), int(args["rev"]), op_key=str(uuid.uuid4()))
            stats["rejected_applies"] += out["status"] == "REJECTED"
            return out
        if tool == "verify":
            return ac.verify(req)
        return {"error": f"unknown tool {tool}"}

    ask = f"Remove {req['identity']}'s access to {req['resource']}. Preserve: {req['preserve']}."
    emit("request", ask=ask, model=MODEL, req=req)
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": ask}]
    for _ in range(MAX_TURNS):
        msg = generate(client, messages).choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if msg.content and msg.content.strip():
            emit("model", text=msg.content.strip())
            stats["said"] = msg.content.strip()
            stats["claimed_infeasible"] = any(
                line.strip().upper().startswith("INFEASIBLE") for line in msg.content.splitlines())
        if not msg.tool_calls:
            break
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
                out = call(tc.function.name, args)
            except (KeyError, ValueError, TypeError) as e:  # malformed tool arguments go back to the model
                out = {"error": f"bad arguments: {e}"}
            text = json.dumps(out)
            emit("tool", name=tc.function.name, args=tc.function.arguments, out=json.loads(text))
            while pending:
                emit("inject", **pending.pop())
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": text})
    else:
        emit("limit")

    # The outcome comes from the graph, never from the model's words.
    final = ac.verify(req)
    emit("outcome", **final, edges=ac.snapshot())
    return {**final, **stats}


if __name__ == "__main__":
    fx = json.loads(Path(sys.argv[sys.argv.index("--fixture") + 1]).read_text()) if "--fixture" in sys.argv else FX
    run(sys.argv[1] if len(sys.argv) > 1 else "payroll", inject="--inject" in sys.argv, fx=fx)
