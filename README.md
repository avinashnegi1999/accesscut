# AccessCut

**Track:** Agents That Act on Connected Data

AccessCut is an agent that removes one identity's access to one resource. It closes every modeled
route to the resource while keeping the access that must stay, such as other resources the same
person still needs.

Deleting the obvious direct grant is rarely enough. Access also arrives through group memberships,
nested groups and assumable service identities. The agent uses FalkorDB to find every route,
proposes which edges to disable and gets each plan checked against the graph. When a plan is
rejected, it replans. When no allowed edit can close all routes, it refuses with evidence instead
of guessing.

> The product depends on FalkorDB. Every route, every plan check and every final verification is a
> FalkorDB traversal. Without the database, the tools raise an error instead of answering.

## Demo

```bash
python server.py        # then open http://localhost:8000
```

Pick a scenario, optionally tick **Outside change mid-run**, and press **Run agent**. The page
streams each step:

1. `inspect_access` finds the routes to the target (blue).
2. The model proposes edge cuts. `evaluate_plan` accepts or rejects each one with reasons:
   `PROTECTED`, `ROUTES_REMAIN`, `COLLATERAL` or `STALE`.
3. `apply_plan` disables the edges (red, dashed) only if the plan is valid at the current graph
   revision.
4. `verify` checks the final state on the graph.

With **Outside change mid-run**, a new grant (orange) is added right after the agent's first
accepted plan. Applying that plan is then rejected as `STALE`, and the agent re-inspects the graph
and replans.

## Graph data model

| Node | Meaning |
|---|---|
| `Identity {id}` | A person or a service account |
| `Group {id}` | A group; groups can be nested |
| `Resource {id}` | Something to access, such as Payroll |
| `Meta {rev}` | Graph revision; every change increments it |
| `Op {key, identity, resource, cut, from_rev, to_rev, result}` | Audit record of an applied plan |

| Edge | Allowed from → to | Meaning |
|---|---|---|
| `MEMBER_OF` | Identity or Group → Group | Membership; group grants flow to members |
| `CAN_ASSUME` | Identity → Identity | Can act as another identity and inherits its access |
| `GRANTS_ACCESS` | Identity or Group → Resource | Direct permission |

Every edge has `id`, `enabled`, `removable` and `protected` properties. The agent may only disable
edges that are `removable` and not `protected`.

Fixtures are validated before loading: node labels, allowed edge types per node pair, no cycles,
and a maximum route depth of 8. Unsupported input is rejected, never silently truncated.

The data is synthetic: three hand-written fictional organizations in `fixture*.json`.

## Core queries

All routes from an identity to a resource, optionally simulating a set of disabled edges (`$cut`):

```cypher
MATCH p=(u:Identity {id:$u})-[:MEMBER_OF|CAN_ASSUME|GRANTS_ACCESS*1..8]->(r:Resource {id:$r})
WHERE all(e IN relationships(p) WHERE e.enabled AND NOT e.id IN $cut)
RETURN [e IN relationships(p) | e.id]
```

This one query drives everything:

- **`inspect_access`:** lists the current routes, plus per-edge impact: which routes each allowed
  edge closes, and which preserved access it breaks if cut alone.
- **`evaluate_plan`:** re-runs the query with the proposed cut. Any remaining route means
  `ROUTES_REMAIN`; a preserved pair with no route left means `COLLATERAL`. For each lost pair, it
  names the plan edges whose removal would restore it. For each still-open route, it lists the
  allowed edges that would close it safely.
- **`verify`:** re-runs the query on the real, mutated graph.

Applying a plan is one atomic query. It checks the revision, disables the edges, bumps the revision
and writes the audit record:

```cypher
MATCH (m:Meta {rev:$rev}) SET m.rev = m.rev + 1
WITH m MATCH ()-[e]->() WHERE e.id IN $cut SET e.enabled = false
WITH DISTINCT m CREATE (:Op {key:$k, identity:$u, resource:$r, cut:$cut,
                             from_rev:$rev, to_rev:m.rev, result:$res})
RETURN m.rev
```

If the graph changed since the plan was evaluated, `Meta {rev:$rev}` matches nothing and the plan
is rejected as `STALE`. Reusing an operation key returns the stored result without changing
anything.

## Agent design

- The model (default `gpt-5.4-mini`) can act **only** through four tools: `inspect_access`,
  `evaluate_plan`, `apply_plan` and `verify`. It cannot write Cypher or invent grants.
- A deterministic validator decides whether a plan is acceptable. The model chooses which edges to
  cut and reacts to rejections.
- The final outcome is read from the graph, never from the model's own claim: `REVOKED`, or
  `UNMET` with the remaining routes.
- Preserved pairs that were already unreachable when the request arrived are set aside, so they
  are never reported as lost.

## Setup

Requirements: Python 3.10+, Docker and an OpenAI API key. Any OpenAI-compatible endpoint works; see
the docstring at the top of `agent.py`.

```bash
docker run -d --name falkordb -p 6379:6379 -p 3000:3000 falkordb/falkordb:latest
pip install -r requirements.txt
```

Set your key as an environment variable. On Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = "<your key>"
```

On macOS or Linux:

```bash
export OPENAI_API_KEY="<your key>"
```

Then run:

```bash
python check.py                         # deterministic checks against FalkorDB, no model needed
python agent.py payroll --inject        # one agent run in the terminal
python server.py                        # demo UI on http://localhost:8000
python eval.py 3                        # repeated scored runs (costs API credit)
python eval.py 3 fixture_heldout.json   # held-out fixture
```

FalkorDB's own browser on http://localhost:3000 shows the raw graphs. Each agent run uses a graph
named `accesscut_agent_<request>`.

## Evaluation

`eval.py` scores every run against ground truth. The ground truth comes from `oracle.py`, a plain
Python graph search with no database and no model, which tries every subset of allowed edges. A run
**passes** in two cases:

- A valid cut exists, and the graph ends `REVOKED`.
- No valid cut exists, the model answers `INFEASIBLE`, and the graph is unchanged.

Model: `gpt-5.4-mini`, 3 runs per scenario. Raw run records are in `results/`.

| Version | What changed | Built-in scenarios (8) |
|---|---|---|
| v1 | Tools returned routes and rejection reasons only | 11/24 |
| v2 | Added per-edge impact to `inspect_access` | 20/24 |
| v3 | Added safe additions per open route; turn limit raised from 12 to 20 | 23/24 |
| v4 | Collateral reasons name the edges that caused them | **24/24** |

With v1 tools, `gpt-4.1-mini` scored 10/24. In almost every failure, the model wrongly gave up
(`INFEASIBLE`) when a valid cut existed.

**Held-out check.** Versions v1–v4 were tuned on the same 8 scenarios they were scored on. After
tuning stopped, a new fixture (`fixture_heldout.json`, a hospital organization) was written and
used once:

- **First run:** 12/15. All three failures were a bug in `verify`, not model errors: a preserved
  pair that was never reachable was counted as lost. After fixing it, the full held-out set was
  rerun.
- **Second run:** 14/15. The one miss was a correct refusal that began "Potentially infeasible…",
  which the scorer did not count. The parser now accepts `INFEASIBLE` at the start of any line;
  the held-out set has not been rerun since that change.

These are small synthetic fixtures. The results show the agent behaves correctly on them. They are
not evidence about real identity systems.

## Limitations

- **Simplified access model:** no deny rules, conditional grants, expiry or real identity
  provider. "Access revoked" means only within this modeled graph.
- **Single writer:** revision checks protect against stale plans, but the demo server runs one
  agent at a time.
- **Grants added during a run:** these are not re-validated for cycles or depth.
- **Not minimal:** the agent finds a valid cut, not necessarily the smallest one.

## AI disclosure

- **During development:** an AI coding assistant was used to generate and debug code and to draft
  this README.
- **At runtime:** an LLM (OpenAI `gpt-5.4-mini` by default) is the planning component of the
  agent.
- **Results:** every result above came from running the code in this repository.

## Files

| File | Purpose |
|---|---|
| `accesscut.py` | FalkorDB model, validation and the four agent tools |
| `agent.py` | LLM tool-calling loop |
| `oracle.py` | Independent route search used as ground truth |
| `check.py` | Deterministic checks: paths match the oracle, protected/stale/collateral rejection, replay safety, restart, infeasibility, bad fixtures, no database |
| `eval.py` | Repeated scored agent runs |
| `server.py`, `static/index.html` | Demo UI |
| `fixture.json`, `fixture_big.json`, `fixture_heldout.json` | Synthetic organizations and requests |
| `results/` | Raw eval logs and per-run records |
