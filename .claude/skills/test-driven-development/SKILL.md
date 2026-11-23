---
name: test-driven-development
description: Use before writing any implementation code in this project — a feature, a bugfix, a branch-table row. Covers the red-green-refactor cycle, which is required here and not optional, what makes a red state real, and the one legitimate exception. Also use when a test was written after the code and nobody can say whether it would have caught the bug.
sources: [engineering-practice/tdd-red-green]
ours: the manual-mutation section comes from this park's own commit practice, Sep-Oct 2026 - no source claimed
---

# Test-driven development

## Red, green, refactor — and red is not a formality

```
RED       write the test. RUN IT. WATCH IT FAIL.
GREEN     write the least code that passes it. Run it. Watch it pass.
REFACTOR  clean it up. Stay green.
```

**The cycle is required in this project.** Not a preference, not "where it makes sense".

## Why red is the step that carries the value

A test written after the implementation is shaped by the implementation. It asserts what the code
does, not what it should do — so it passes on the broken version too, and it will keep passing while
the thing it claims to protect is broken.

That is not hypothetical here. **Every test passed while paying customers could not see what they had
paid for.** The suite was green. It had always been green. It was green about the wrong things.

So the red state is the only moment you can prove the test has power. Once the implementation exists,
that proof is gone forever and cannot be reconstructed by reading the test.

**A test that has never been seen to fail is not a test. It is a comment that runs.**

## Red has to be red for the right reason

Watch the failure message. It must be an **assertion failure about the behaviour** — the value was
this, expected that.

If it fails with a missing class, a syntax error, an undefined method or a 500, the test has not
reached the behaviour yet. That is a broken test, not a red test. Fix it until it fails saying the
right thing.

## Green means the smallest thing

Write the least code that turns it green. Not the general solution, not the abstraction you can
already see, not the next three cases.

The next case gets its own red first. That is what stops a plan's step 4 from quietly containing
steps 5 through 9, and it is why the cycle produces small reversible commits instead of one large
one nobody can review.

## Where the tests come from

Not from imagination — from the **branch table**. Invoke `branch-table` first: input → condition →
response, one row per path. Every row is a test, and the sad rows are the ones that get skipped by
everybody, which is why they are the ones that break.

Then hand the table to **`failing-test-author`**. Its contract is one test per row **plus the
evidence that each fails** — it returns the actual failure output, not a claim.

### Who owns which step

| | Owner |
|---|---|
| **the cycle** — and the decision not to write implementation first | **you**, the main agent |
| **RED** — writing tests that fail for the right reason | `failing-test-author` |
| **GREEN and REFACTOR** | **you**. The subagent never writes implementation and never makes a test pass |

This skill is yours, not the subagent's. The decision that matters — *do not write the
implementation yet* — is taken **before** any subagent exists, so a skill loaded inside one would
arrive after the moment it was needed.

`failing-test-author` is deliberately **self-contained**: it carries "fail for the right reason" in
its own prompt and does not depend on loading this. A subagent that needs a skill to know its own
rule loses that rule silently whenever the skill is not there.

## The one legitimate exception

**Characterization tests on code that already exists.** Backfilling coverage for legacy behaviour is
good work, and such a test passes immediately by definition — there is no red to see, because
nothing is being added.

That is allowed and it must be **declared**, not assumed. Mark it so, in whatever way this project's
test framework supports (a group, an attribute, a comment convention that the check recognises).
An undeclared test that passes on the parent commit is indistinguishable from a test written after
the fact, and it gets treated as one.

## What this looks like in a commit

The test and the implementation may land in the same commit. What must be true is that **the test
fails when run against the previous commit's code.**

That is mechanically checkable, and it is checked. `check-red-green` runs each new test against the
parent commit and refuses the ones that pass — because a test that passes without your change is a
test that would not have caught its absence.

## After green, break it on purpose

Red proves a test fails when the code is **absent**. It says nothing about when the code is
**wrong**: a test that went red on a missing method can still pass on every wrong version of that
method. So once the change is green, mutate it by hand.

```
PICK     a line that carries a decision: a condition, a boundary, a guard, a call with an effect.
BREAK    it the way a real bug would: negate the condition, > to >=, remove the call, return early.
RUN      the tests that cover it. One must fail, on an assertion about the behaviour.
RESTORE  the line, and read the diff to confirm the mutation is gone.
```

One mutation per decision the change introduces — not every line, and not the whole file. It needs
no coverage driver and no plugin, so it works on any stack this project uses.

**If nothing fails, the line is unprotected.** With the mutation still in place, write the missing
test and watch it go red; restore the line and watch it go green. If no test can be written because
no behaviour depends on the line, delete the line.

A mutation left behind is a bug you wrote on purpose, so **restore before anything else happens**:
before a commit, before another file, and before handing over to anyone.

Say what was done in the commit body — which line was broken and which test caught it. That is
evidence. The number of mutations is not.

## Before you write a line of implementation

- [ ] The branch table exists, sad paths included
- [ ] The test is written
- [ ] **You ran it and watched it fail**
- [ ] It failed on an assertion about behaviour, not on a missing class or a 500
- [ ] You can say, in one sentence, what breaks in production if this test is deleted

If the last one is hard to answer, the test is asserting the implementation rather than the
behaviour. Rewrite it before continuing.

## Before you commit

- [ ] Each decision the change introduces was broken by hand, and a test failed
- [ ] Every mutation is restored, and the diff shows only what you meant
- [ ] The commit body names what was broken and what caught it
