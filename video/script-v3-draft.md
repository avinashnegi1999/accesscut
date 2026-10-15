# AccessCut — film script v3 (draft for approval)

Goal: a judge who has never heard of the project understands what problem it solves, why it needs
a graph, what the agent does, and why we trust the result. Plain language; every term is explained
the first time it appears.

**Pacing:** one sentence, then a pause. Whenever the picture changes, the voice stops so the viewer
can look. `· pause 1s ·` marks a silence. If no pause is marked, there is still a short natural gap
of about 0.6 s.

---

## 1. The problem (~0:00–0:30)
*On screen: a card, "Raj · contractor · last day", then the Payroll permission is deleted.*

· pause 1s · *(let the card appear)*

> When a contractor leaves a company, their access has to be removed.

· pause 1s ·

> Say Raj is leaving today, and must lose access to Payroll.

· pause 1.5s · *(the Payroll permission is crossed out)*

> The obvious fix is to delete the permission that gives them Payroll.

· pause 1.5s ·

> But after you delete it, Raj can still open Payroll.

· pause 2s · *(let that sink in)*

## 2. Why: access has many paths (~0:30–1:20)
*On screen: the access graph. Each route to Payroll lights up as it is named.*

· pause 1.5s · *(the graph appears; give the eye time to take it in)*

> That is because, in a real company, access is not a single switch. It is a network.

· pause 1s ·

> People belong to groups. Groups belong to other groups. Some people can sign in as a service account.

· pause 1s ·

> Every one of those links can lead to Payroll.

· pause 1.5s ·

> Here, Raj reaches Payroll in five different ways.

· pause 1s ·

> A direct permission.

· pause 1.2s · *(route 1 lights up)*

> A chain of nested groups.

· pause 1.5s · *(route 2 lights up)*

> An on-call team, and a service account.

· pause 1.5s · *(routes 3 and 4 light up)*

> And an emergency "break-glass" account.

· pause 1.5s · *(route 5 lights up)*

> To really remove access, all five paths have to be cut.

· pause 2s ·

## 3. The catch: some access must stay (~1:20–1:55)
*On screen: training, warehouse and pager turn green; then Priya and Ayesha.*

> But you cannot just cut everything.

· pause 1s ·

> Raj still needs his training, the data warehouse, and the pager, for the rest of the day.

· pause 1.5s · *(those three turn green)*

> And other people share the same groups. Priya still needs Payroll. Ayesha still needs the warehouse.

· pause 1.5s · *(Priya and Ayesha turn green)*

> So the real question is: which links can we cut, so that Payroll is closed, and nothing else breaks?

· pause 2s ·

## 4. What AccessCut is (~1:55–2:30)
*On screen: "AccessCut", then the four steps: Inspect, Propose, Check, Verify.*

> AccessCut answers that question with an AI agent and a graph database, FalkorDB.

· pause 1s ·

> The company's access is stored in FalkorDB as a graph. People, groups and resources are the points. Every permission is a line between them.

· pause 1.5s ·

> The agent can only do four things. Look at the paths. Propose links to cut. Ask FalkorDB to check the proposal. And apply it.

· pause 1.5s · *(the four steps appear one by one)*

> The agent decides what to try. FalkorDB decides whether it is safe.

· pause 2s ·

## 5. A real run, step by step (~2:30–4:05)
*On screen: the replay of a real recorded run. Each step's card matches the voice.*

> Here is a real run.

· pause 1s ·

> First, FalkorDB finds all five paths from Raj to Payroll.

· pause 2s · *(the five paths light up)*

> The agent proposes cutting four links.

· pause 1.5s · *(the four proposed cuts appear as red dotted lines)*

> FalkorDB rejects it. One of those cuts would also take away Raj's warehouse access.

· pause 1s · *(warehouse turns red)*

> And it tells the agent exactly which two cuts caused that.

· pause 2s ·

> So the agent swaps one cut for a different one.

· pause 1.5s ·

> Now one path to Payroll is still open. So it adds one more cut.

· pause 1.5s ·

> FalkorDB checks again. This time, the plan is accepted.

· pause 2s · *(the card turns green)*

> But before the agent applies it, someone else in the company adds a new permission.

· pause 1.5s · *(the orange link appears)*

> That opens a sixth path to Payroll. The plan is now out of date.

· pause 1s ·

> FalkorDB notices that the graph has changed, and refuses to apply the old plan.

· pause 2s ·

> The agent looks at the graph again, finds the new path, and adds it to the plan.

· pause 1.5s ·

> Now the plan is applied. Six links disabled, all at once.

· pause 2s · *(the cuts turn solid red; Payroll greys out)*

> Finally, FalkorDB checks the result. Raj can no longer reach Payroll. And everything that had to stay is still there.

· pause 2s · *(the kept access turns green)*

> Notice that the final answer comes from the graph, not from the AI's own words.

· pause 2s ·

## 6. It runs live (~4:05–4:25)
*On screen: the live demo page running.*

> This is the same thing running live, in the demo app, on a real FalkorDB database.

· pause · *(silence while the live clip plays, about 11 seconds)*

## 7. It knows when to stop (~4:25–4:50)
*On screen: the path to the wiki, both links locked.*

> Sometimes, removing access safely is impossible.

· pause 1.5s ·

> Here, the only path to the wiki goes through protected links, that nobody is allowed to cut.

· pause 1.5s · *(the locked path lights up)*

> So the agent says it cannot be done, shows why, and changes nothing.

· pause 2s ·

## 8. How the graph does the work (~4:50–5:10)
*On screen: the Cypher query.*

> All of this rests on one graph query.

· pause 1.5s · *(the query appears)*

> It finds every path from a person to a resource. Give it a proposed cut, and it shows what would happen, without changing anything.

· pause 2s ·

## 9. Does it work? (~5:10–5:40)
*On screen: the bars rising, then 15/15.*

> We tested the agent against an independent checker that already knows the right answer.

· pause 1.5s ·

> Each time FalkorDB gave the agent better feedback, it did better. From 11 out of 24 test cases, up to 24 out of 24.

· pause 2s · *(the bars rise)*

> And on new cases it had never seen before, it passed 15 out of 15.

· pause 2s ·

## 10. Close (~5:40–5:55)
*On screen: end card.*

> AccessCut. Remove someone's access. Every path, and nothing else.

· pause 3s · *(end card holds)*

---

Notes
- Estimated length: about 5 minutes; the real voice sets the final timing.
- Same voice (Suzie, default), same real run, same live clip. The words, pauses and visual holds change.
- Visual changes needed: a new opening card (contractor, Payroll permission crossed out); the four
  steps appearing one by one; the route labels and run cards held for the full pause.
