---
name: writing-plans
description: Use when work in this project is understood but not yet ordered — several steps, more than one file, or anything that outlives the session. Covers the readability bar a plan must clear, ordering by what unblocks what, and where a plan is allowed to live. Invoke after brainstorming and before the first edit. Skip it for a single reversible change in one file.
ours: "plan structure as practised here; no single source is claimed for it"
---

# Writing a plan

## The bar

**A plan is good enough when an enthusiastic junior with bad taste, no judgement, no context on this
project and an aversion to writing tests could follow it and still produce the right thing.**

That is testable. "Clear plan" is not. Read each step and ask: *could this person choose wrong here?*
Everywhere the answer is yes, make the choice for them, in the plan.

So no step says "handle errors appropriately", "refactor as needed", or "add tests". It says which
errors, which file, which cases.

## Where a plan lives

**Not committed to this repository.** A plan is not a stable category: it became state or it became
history, and while nobody decides which, it rots in between and the next person cannot tell whether
it describes the code or somebody's intention from three months ago.

| What | Where |
|---|---|
| the plan while you work | scratch space, outside the repo |
| what shipped and why | the **commit message** |
| a decision worth keeping | the commit message, with its reversal cost |

If a plan document must exist because the work spans weeks, it lives outside the repository and is
deleted when the work lands.

## Ordering

**By what unblocks what — never by what is easy or interesting.**

Two orderings that pay off and are counter-intuitive at the time:

- **Measure before you change.** If a step exists to tell you whether the work helped, it comes first
  or it does not exist. A baseline taken afterwards measures nothing.
- **Write the failing test before the code that passes it.** Not ceremony — a test written after the
  fact is shaped by the implementation and stops being able to catch it being wrong. Hand it to
  `failing-test-author` and the proof is the run.

And: **the sad paths are steps, not cleanup.** A plan that lists the happy path and ends with "handle
errors" will ship the happy path. Every row of the branch table is its own step.

## Each step

```
N. <what changes> — <the file>
   Done when: <the observation that proves it>
```

**"Done when" is the whole discipline** — verify the effect, not the command. A step whose completion
criterion is "the command ran" will pass while achieving nothing: `config:cache` exits zero while
breaking the app, and a deploy ships old code from a non-empty volume with no error.

Good: *the lookup for a nonexistent plate renders the empty state, and the test for it fails before
this step and passes after.*
Bad: *handle the not-found case.*

## Before executing

- [ ] Every step names a file
- [ ] Every step has a **Done when** that is an observation
- [ ] Ordering is by dependency; anything that measures a baseline is first
- [ ] Every branch-table row is a step
- [ ] Anything on the money path has a test named in the plan, not implied
- [ ] Decisions recorded with their reversal cost
- [ ] The plan itself is not being committed
