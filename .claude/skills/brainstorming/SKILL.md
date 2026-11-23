---
name: brainstorming
description: Use when a request for this project arrives as a wish rather than a specification — "the checkout should be smoother", "we need a dashboard", "let's add WhatsApp". Turns it into something buildable, and decides what to settle alone versus what to bring to the owner. Invoke before writing a plan. Skip it when the request is already specific and reversible.
ours: "turning a wish into a specification as practised here; no single source is claimed"
---

# Brainstorming a change

## Decide, record, proceed

**A wrong execution can be corrected. A day lost waiting for a decision cannot.**

Asking is not free — it costs a day and it makes the owner the bottleneck. So the default is decide
and record, and the test for breaking that default is one question:

**Cheap to reverse → decide. Expensive or irreversible → ask.**

| Ask about | Decide alone |
|---|---|
| anything on the money path | file layout, naming, structure |
| anything a customer sees or reads | which of two equivalent libraries |
| pricing, or what is charged for | the order of the work |
| deleting or migrating data | how to break up a class |
| a commitment to a third party | what to measure first |

Record every decision where the work lands — the commit message:

| | |
|---|---|
| **Decision** | what was chosen |
| **Why** | the reason, in one line |
| **If wrong** | what it costs to reverse |

**The third line does the work.** Naming the reversal cost before you need it is what makes deciding
alone safe. It is also the self-check: if "if wrong" keeps coming out large, the threshold is set too
low and more should be going to the owner.

## Four questions that convert a wish

**1. What breaks today?** Not what would be nice — what fails, and how you know. *"A plate that does
not exist drops the user on a 404 error page"* is a specification. *"Search should be more robust"*
is a mood.

**2. Who drives it, and what do they see?** A real user with a real goal. And whatever text they read
is customer-facing — never an internal codename.

**3. What are all the branches?** Every path a user can drive: the happy one, the empty one, the
invalid one, the one where the third party is down, the one where they already paid. Enumerate them
before building — the `branch-table` skill is the procedure, and it exists because typing code by
hand forced you to reach the `else`, while commanding an agent does not.

**4. How do we know it worked?** Named before building. If the answer is a test count, it is the
wrong answer.

## What to push back on

**A solution presented as a requirement.** "We need a queue" answers a question nobody stated. Ask
what it is for.

**A change on the money path with no branch table.** That is where the expensive failures live: the
suite was green while paying customers could not see what they had paid for.

**Scope that quietly includes a migration or a schema change.** Those are not reversible in the same
way. They go to the owner.

## The output

Four to six lines, not a document:

```
Breaks today:  what fails, with the evidence
Driven by:     who, and what they see
Branches:      how many paths, and whether the sad ones are enumerated
Done when:     the observation that proves it
Decided:       <decision> — <why> — if wrong: <reversal cost>
Asking:        only the expensive or irreversible ones, or "nothing"
```

If `Asking` is empty, go to `writing-plans`. That is the normal case and it should stay the normal
case.
