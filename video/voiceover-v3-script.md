# AccessCut voiceover v3 (5:56)

Each line starts at the time shown. The gaps between lines are pauses.


## 1. The problem

**0:01.0**  When a contractor leaves a company, their access has to be removed.  
**0:05.8**  Say Raj is leaving today, and must lose access to Payroll.  
**0:12.9**  The obvious fix is to delete the permission that gives them Payroll.  
**0:20.4**  But after you delete it, Raj can still open Payroll.  

## 2. Why: access has many paths

**0:26.6**  That is because, in a real company, access is not a single switch. It is a network.  
**0:34.0**  People belong to groups. Groups belong to other groups. Some people can sign in as a service account.  
**0:43.3**  Every one of those links can lead to Payroll.  
**0:48.6**  Here, Raj reaches Payroll in five different ways.  
**0:54.5**  A direct permission.  
**0:57.2**  A chain of nested groups.  
**1:00.1**  An on-call team, and a service account.  
**1:05.3**  And an emergency "break-glass" account.  
**1:09.7**  To really remove access, all five paths have to be cut.  

## 3. The catch: some access must stay

**1:15.9**  But you cannot just cut everything.  
**1:18.6**  Raj still needs his training, the data warehouse, and the pager, for the rest of the day.  
**1:26.1**  And other people share the same groups. Priya still needs Payroll. Ayesha still needs the warehouse.  
**1:36.6**  So the real question is: which links can we cut, so that Payroll is closed, and nothing else breaks?  

## 4. What AccessCut is

**1:46.9**  AccessCut answers that question with an AI agent and a graph database, FalkorDB.  
**1:55.7**  The company's access is stored in FalkorDB as a graph. People, groups and resources are the points. Every permission is a line between them.  
**2:08.7**  The agent can only do four things. Look at the paths. Propose links to cut. Ask FalkorDB to check the proposal. And apply it.  
**2:22.8**  The agent decides what to try. FalkorDB decides whether it is safe.  

## 5. A real run, step by step

**2:30.8**  Here is a real run.  
**2:33.8**  First, FalkorDB finds all five paths from Raj to Payroll.  
**2:40.2**  The agent proposes cutting four links.  
**2:44.2**  FalkorDB rejects it. One of those cuts would also take away Raj's warehouse access.  
**2:52.0**  And it tells the agent exactly which two cuts caused that.  
**2:58.8**  So the agent swaps one cut for a different one.  
**3:04.1**  Now one path to Payroll is still open. So it adds one more cut.  
**3:10.4**  FalkorDB checks again. This time, the plan is accepted.  
**3:17.8**  But before the agent applies it, someone else in the company adds a new permission.  
**3:25.9**  That opens a sixth path to Payroll. The plan is now out of date.  
**3:32.7**  FalkorDB notices that the graph has changed, and refuses to apply the old plan.  
**3:40.9**  The agent looks at the graph again, finds the new path, and adds it to the plan.  
**3:49.2**  Now the plan is applied. Six links disabled, all at once.  
**3:56.8**  Finally, FalkorDB checks the result. Raj can no longer reach Payroll. And everything that had to stay is still there.  
**4:10.2**  Notice that the final answer comes from the graph, not from the AI's own words.  

## 6. It runs live

**4:18.7**  This is the same thing running live, in the demo app, on a real FalkorDB database.  
*(12 s silence for the live demo clip)*  

## 7. It knows when to stop

**4:38.0**  Sometimes, removing access safely is impossible.  
**4:43.9**  Here, the only path to the wiki goes through protected links, that nobody is allowed to cut.  
**4:53.2**  So the agent says it cannot be done, shows why, and changes nothing.  

## 8. How the graph does the work

**5:02.1**  All of this rests on one graph query.  
**5:06.2**  It finds every path from a person to a resource. Give it a proposed cut, and it shows what would happen, without changing anything.  

## 9. Does it work?

**5:19.0**  We tested the agent against an independent checker that already knows the right answer.  
**5:26.8**  Each time FalkorDB gave the agent better feedback, it did better. From 11 out of 24 test cases, up to 24 out of 24.  
**5:39.5**  And on new cases it had never seen before, it passed 15 out of 15.  

## 10. Close

**5:47.5**  AccessCut. Remove someone's access. Every path, and nothing else.  
