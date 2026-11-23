---
name: gate-authoring
description: Use when writing anything in this project that refuses — a test that enforces a convention, a lint rule, a CI step, a check in the release script. Covers proving the guard fires AND stays quiet, and the failure that makes guards worthless. Invoke before writing the check, and when an existing one produces a finding you suspect is wrong.
ours: "written from the park's own gates and the false accusations they produced; no source is claimed"
---

# Writing a guard

A convention that lives in someone's head is not a convention. It is a thing the next person breaks,
and the next person is often an agent that never read your documentation.

## The proof this works

One project in this park has one, and it is the shape to copy — not the file. Its
`DateDisplayConventionTest` is 23 lines: it walks the blade views and
refuses any `_at->format(`, because formatting a raw datetime in a view prints UTC and reintroduces a
mismatch that once had the invoice showing one month and the screen another.

On 18 Aug 2026 an agent used `->format('m/Y')` in a view, the test refused it, and the agent switched
to the `@dt` directive on its own. It said afterwards that it had not known the convention.

**That is the point.** Nobody wrote a paragraph asking for `@dt`. Twenty-three lines of test bound an
agent that had read no documentation about it, in a session nobody was watching. A skill has to be
loaded and read; a test just exits non-zero.

So: **when you learn a rule this codebase must follow, ask whether it can be a test.** Only what
cannot becomes prose.

## The one rule

**A guard does not ship until it runs clean against the whole codebase. If it accuses on its first
run, suspect the guard.**

A guard that fires wrongly teaches people to wave it through — and once that reflex exists it covers
the true positives too. You will have built something that now actively hides what it was meant to
catch.

The park has the proof: a release script with four permanently-failing gates gets run with
`--skip-gates` every single time. Green-field correct, operationally dead.

## Prove it four ways

On a fixture, never by adjusting the codebase to fit:

```
1) the offending shape           → fails, and the message says what to do instead
2) the same shape, corrected     → passes
3) the legitimate lookalike      → passes
4) nothing it could read         → never a finding, and never a silent pass
```

**Case 3 is the one that gets skipped and the one that matters.** For the date guard, the lookalike
is a project whose app timezone is *not* UTC — there `->format()` already prints local time and the
same pattern is correct code. A guard copied without that check would refuse 25 correct files.

**Case 4 is not optional, and it fails two ways.** A guard that fires on its own confusion — no
views directory, an unparseable file, an empty result — is a guard that gets deleted. A guard that
passes green over what it could not read is worse, because nobody deletes it: it reports health it
never measured, and the next reader repeats it as fact.

So in case 4 the guard says what it could not read and does **not** pass: a test marks itself
skipped with the reason, a script exits 3 — "could not measure" — and whoever calls it counts that as
not passed. Out of scope is different: a file the guard has no question about is not case 4, and
silence there is correct. The test is *was there something to judge, and did the guard judge it?*

## Keep it narrow on purpose

The date guard matches `_at?->format(` and nothing else. That misses a date field not named `_at`.
That is a deliberate trade: a broader pattern catches more and accuses more, and one false accusation
costs more than several missed catches, because it destroys trust in every future finding.

**Narrow and trusted beats broad and ignored.**

## What the message must say

The reader is interrupted and wants out. Give them the exit:

- **what** it found, and **where** — the file and line
- **why it matters here**, in one clause — not the general principle
- **what to do instead**, named — the directive, the helper, the method
- **what not to do** — usually *do not delete the check to make this pass*

The date guard's docblock does all four in five lines. Copy that shape.

## Before you ship

- [ ] It fails on the offending shape
- [ ] It passes once corrected
- [ ] It passes on the legitimate lookalike
- [ ] On empty or malformed input it says so and does not pass — skipped with a reason, or exit 3
- [ ] It ran clean against the whole codebase
- [ ] The message names what to do instead
- [ ] It runs on its own — in the suite, in CI, or in the release script. A guard nobody invokes is
      a file

## Where it lives

**In the test suite**, whenever it can be. A test runs on every push without anyone remembering it,
it fails loudly, and it travels with the code.

A convention about how the codebase is written is a legitimate test even when it asserts nothing
about behaviour. That date guard calls no application code — it reads files. That is
still the right place for it.
