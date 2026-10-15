# Evaluation

`eval.py` scores every agent run against ground truth. The ground truth comes from `oracle.py`, a
plain Python graph search with no database and no model, which tries every subset of allowed edges.

A run **passes** in two cases:

- A valid cut exists, and the graph ends `REVOKED`.
- No valid cut exists, the model answers `INFEASIBLE`, and the graph is unchanged.

Model: `gpt-5.4-mini`, 3 runs per scenario. Raw run records are in `results/`.

## Tuning: built-in scenarios (8 scenarios × 3 runs)

| Version | What changed | Pass |
|---|---|---|
| v1 | Tools returned routes and rejection reasons only | 11/24 |
| v2 | Added per-edge impact to `inspect_access` | 20/24 |
| v3 | Added safe additions per open route; turn limit raised from 12 to 20 | 23/24 |
| v4 | Collateral reasons name the edges that caused them | **24/24** |

With v1 tools, `gpt-4.1-mini` scored 10/24. In almost every failure, the model wrongly gave up
(`INFEASIBLE`) when a valid cut existed. Giving the model graph-computed feedback fixed this; a
bigger model did not.

## Held-out: `fixture_heldout.json` (5 scenarios × 3 runs)

Versions v1–v4 were tuned on the same scenarios they were scored on. After tuning stopped, a new
fixture (a hospital organization) was written and used only for testing.

| Run | Result | Note |
|---|---|---|
| 1 | 12/15 | All three failures were a bug in `verify`, not model errors: a preserved pair that was never reachable was counted as lost. Fixed. |
| 2 | 14/15 | The one miss was a correct refusal that began "Potentially infeasible…", which the scorer did not count. The scorer was fixed to accept `INFEASIBLE` at the start of any line. |
| 3 | **15/15** | No tools or prompts changed between runs 2 and 3. |

These are small synthetic fixtures. The results show the agent behaves correctly on them. They are
not evidence about real identity systems.
