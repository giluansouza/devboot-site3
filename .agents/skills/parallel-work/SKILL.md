---
name: parallel-work
description: Use when work in this project can be split across subagents or across branches — independent steps in one plan, a sweep over many files, a risky change that must not disturb the working tree. Covers when parallelism actually pays, how to brief a subagent that shares none of your context, and why the author never verifies their own work. Invoke before spawning the first agent.
ours: "worktree and subagent practice as measured in this park; no source is claimed"
---

# Parallel work

## Does this actually parallelise?

Parallelism costs a briefing per agent and a merge at the end. It pays when the pieces are
**independent** and each is **big enough to be worth the briefing**.

| Parallelise | Do not |
|---|---|
| the same change across many independent files | steps where each needs the previous one's answer |
| author here, verifier elsewhere | anything under five minutes of work |
| a sweep whose work-list is already known | work whose scope you are still discovering |

**The common mistake is fanning out before the shape is known.** Scout first — list the files, find
the call sites — *then* fan out over what you found. Discovery is sequential; execution over a known
list is parallel.

## Briefing a subagent

It starts with **none of your context**. Not the conversation, not the decision you made ten minutes
ago, not what you already ruled out.

```
Goal:        one sentence — what must be true when you are done
Scope:       exact paths. Which directories, which exclusions
Constraints: read-only? do not touch migrations? do not change the test?
Context:     the two or three facts it cannot discover on its own
Return:      the exact shape you want back — table, list, verdict, paths
```

**The `Return` line is the one people skip and the one that costs most.** An agent that answers in
prose when you needed a list forces you to re-read everything, which is the work you were delegating.

**`Context` is where this codebase's traps go.** Dates in views go through the `@dt` directive, not
`->format()`. `vendor/` and `node_modules/` are excluded from every sweep. Caches serve a past
version of reality with total confidence.

## The author never verifies their own work

A writer and a reviewer at the same level fail on the same blind spot. Rereading your own change
finds typos, not wrong assumptions — those are found by **running**, which is evidence, not review.

So for anything that ships or refuses:

```
author  →  failing-test-author (proves it was broken)  →  reviewer, fresh context
```

**An irreversible action gets more care, not less.** A migration, a delete, a deploy — those go to
the most capable reviewer available even when the diff looks trivial.

## Worktrees

A worktree gives an agent its own checkout, so parallel edits do not collide and your working tree
stays untouched.

**Use one when** several agents write to the repository at once, a risky change needs to be
abandonable with no cleanup, or something long is running and you want to keep working.

**Do not** when the work is read-only — a search needs no isolation and pays setup cost for nothing.

Two things that bite: **symlinks with relative targets break when moved**, and a worktree does not
carry your untracked files — including `.env`, which means the app will not boot there until you
copy it.

## Merging what comes back

**Do not trust a summary over the artifact.** Read the diff, run the suite. A confident report of
work that did not happen is indistinguishable from one that did, right up until you look.

**Run the full suite once at the end, over the merged result.** Each agent passing its own slice does
not mean the union passes — that is where a convention guard of the kind `gate-authoring`
describes earns its keep.

## When to take it back

Two agents disagree and you cannot tell which is right from the artifacts; an agent came back with "I
could not" twice; the work turned out not to be independent. Then it was always sequential work, and
finishing it yourself is faster than a third briefing.
