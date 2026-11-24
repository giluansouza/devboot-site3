# blog

<!-- UNFILLED: this project has not described itself — the factory wrote this form and nothing in it. Fill it and delete this
     comment. Everything outside the markers below is yours and is never touched.

     Keep it SHORT. This file is injected into every session and every turn, so every line
     is paid forever. It is not the README: what this is, how to install it and how it is
     deployed go there. Only what an agent would get WRONG goes here — and if the rule is
     checkable, write a test instead and leave this file alone. -->

**In one line:** what this is, only so an agent recognises what it is touching.

## Traps

What looks fine here and is not. Each line earns its place by naming a defect it prevents,
and each one is a confession that we have not managed to make it a test yet.

- <!-- e.g. the dev container must be up before any artisan command -->
- <!-- e.g. dates in views print UTC — use the @dt directive, never ->format() -->

## The money path

Where payment becomes delivery in this codebase, and what must never break silently.
Delete this section only if this project takes no money.

---

<!-- BEGIN foundation:standard -->
## Standard — projected from `foundation`, do not edit here

Edit `~/dev/foundation/standards/project-agents.md` and run `tools/push-standards`. Changes made
directly in this block are overwritten without warning.

### Where harness files go — discovery is asymmetric

| File | Discovered | Consequence of getting it wrong |
|---|---|---|
| `.claude/agents/` | **upward only**, cwd → repository root | an agent *below* your starting directory never loads |
| `.claude/skills/` | that directory and its parents; from the root, downward on demand | a skill far from its code burns context in sessions that never need it |
| `CLAUDE.md` | cwd and every ancestor at launch, subdirectories on demand | composes safely — split it per subproject |
| `AGENTS.md` | **the only file Codex, OpenCode, Cursor and Gemini CLI read** | a rule that lives only in `CLAUDE.md` binds one harness out of five |
| `.claude/settings.json` | **starting directory only**, never inherited | a root file does not apply when you start in a package |

So: **agents as high as still makes sense, skills next to the code they describe, settings copied
per starting directory.** Opening at the repository root is *not* a superset of opening in a
package — the asymmetry is the trap.

Anything under `.claude/` that a teammate would need must be **tracked by git**. Inside a
repository but gitignored is the same outcome as outside one: gone with the disk, absent from a
clone.

Ignore the local and the ephemeral, not the directory:

```gitignore
.claude/settings.local.json    # personal by design — the .local suffix says so
.claude/worktrees/             # a full checkout inside the repo; 24 MB in confereplaca
```

Ignoring `.claude/` wholesale hides `agents/` and `skills/` from everyone but you. Un-ignoring it
wholesale offers git a checkout of the repository inside itself.

**Verify instead of assuming — from this project's root:**

```bash
~/dev/foundation/tools/check-harness-layout .
```

### What goes in this file, and what does not

`README.md` and `AGENTS.md` are separated by **cost, not by audience**. A README is read once, by
someone who chose to open it — length there is nearly free. This file is injected into every session
and every turn, so **every line is paid forever**.

So the admission test is not *is this true about the project*. It is:

> **Would an agent get this wrong if it were not written here?**

"This is a fleet SaaS" is true and prevents nothing. "The dev container must be up before any artisan
command" prevents a wasted session. The first belongs in the README, the second belongs here.

| If it is… | It goes to |
|---|---|
| checkable | a **gate** — a test, a hook, a CI step. Binds every harness, cannot be skipped |
| always true and not checkable | **here**, in one line |
| true only sometimes | a **skill** — loaded on demand |
| orientation for a person | **`README.md`** |

**Every line here is a confession that we could not turn that rule into a gate.** This file is not
documentation; it is the queue of what has not become a test yet. A growing `AGENTS.md` is a bad
sign, not a thorough one — and the first question about any line in it is *why is this not a test?*

### What the factory installed here, and when it loads

Under `.claude/skills/` and `.claude/agents/`. Do not edit them in place — they are projections, and
the next `push-standards` overwrites the change. Fix them in the factory and redistribute.

| Reach for | When |
|---|---|
| `brainstorming` | the request is a wish, not a specification |
| `branch-table` | before implementing anything a user can drive |
| `flow-map` | the product is defined and no application exists yet — which screens, what leads where, and the states nobody draws |
| `visual-proposal` | before the first screen is coded, or a redesign — one page the owner approves, phone first, before any interface work |
| `writing-plans` | more than one step, more than one file, or it outlives the session |
| `parallel-work` | splitting across subagents or worktrees |
| `test-driven-development` | **before any implementation.** Red-green is required here. It is *checked* only where `.githooks/config` declares `TEST_CMD` — run `~/dev/foundation/tools/check-red-green .` to see whether this project is one of them |
| `gate-authoring` | writing anything that **refuses** — a convention test, a lint rule, a release check |
| `systematic-debugging` | something is broken and the cause is unknown, or the second fix failed |
| `shipping-to-production` | before any deploy, and whenever production is wrong |

## Reaching the VPS: use your own identity

Reconnaissance on production goes over **your own identity**, never `ssh vps222` and never another
agent's.

| You are | Your alias |
|---|---|
| Claude Code | `ssh vps222-claude` |
| Codex | `ssh vps222-codex` |
| anything else | **stop and ask.** Do not borrow one from this table |

`vps222` is the owner's account. It is in the `docker` group, which is root-equivalent, and this
park's settled decision is that no AI identity belongs there. Each alias above is a separate uid with
no docker access, whose verbs are gated by sudoers and logged per agent — so `ps`, `ls -l`, the
journal and `/var/log/sudo-io/` say *which agent* did a thing, not merely that someone did.

Borrowing another agent's alias destroys exactly that, and silently: the trail then names the wrong
agent, which is worse than no trail, because someone will trust it. This already happened on
11 Sep 2026 — the first version of this section hardcoded the Claude alias, and since this file is
read by every harness, Codex read it and obeyed it.

What you run through it, all read-only, all `sudo -n`:

| | |
|---|---|
| `/opt/infra/bin/verify <proj> <env>` | **which commit is in production, and is it healthy.** Run with no tag and it prints the running image id plus every local tag pointing at it — and those tags are short shas, so `git log --oneline -1 <tag>` names the commit. Also: health, restart count, and the health endpoint |
| `/opt/infra/bin/verify <proj> <env> <tag>` | same, plus: **is the thing I just deployed actually running?** Compares by image id, never by tag string — the compose points at `:latest`, so the container always reports `:latest` and a string comparison would fail on every correct deploy |
| `/opt/infra/bin/status <proj> <env>` | container states |
| `/opt/infra/bin/logs <proj> <env> [container] [n]` | logs, `--tail` bounded |
| `/opt/infra/bin/artisan <proj> <env> <sub>` | non-destructive artisan only; `tinker` is refused |

**"Which commit is deployed?"** is `verify` with no tag. A session asked the owner that on
17/09/2026 and reported it could not find out — the capability had existed for five days, and the
table above described it as "the post-deploy check", which is not what anyone searches for.

Plain reconnaissance needs no wrapper and no sudo: `ps`, `df`, `free`, `ss`, `top`, `/proc`, and
reading composes under `/opt/apps`. Production `.env` files are **not** readable, on purpose.

Deploys still run over `vps222`, because a deploy needs `docker load` and `docker compose` — and
because a deploy is the owner's action, not yours. You hand over the command; the owner runs it.

**This rule governs ad-hoc reconnaissance** — you, wanting to look at production and typing an `ssh`.
It does not revoke a path that a directory's own `settings.json` grants **explicitly** to an
instrumented tool: a script with its own gate, read-only by construction, whose payload is auditable.
`growth/`'s `pull-prod-metrics.py` is that, and it keeps working where its settings say so.

The distinction is not who is allowed more. A gated tool refuses in code what prose can only ask for;
a script whose payload you cannot inspect is reconnaissance wearing a script's clothes. And where the
gate lives inside a file the session itself can edit, treat the arrangement as temporary — the gate
belongs on the far side, in a wrapper the session cannot rewrite.

| Delegate to | For |
|---|---|
| `failing-test-author` | the proof that it was broken — the test that fails before the fix |
| `change-reviewer` | ruling on a change before merge. **Always** for a migration, a delete, or a payment path |
| `money-path-auditor` | answering whether paid → delivered is actually covered |

**The author never verifies their own work.** A writer and a reviewer at the same level fail on the
same blind spot — which is why `change-reviewer` is a separate context and not a second read.

### Language

Write in **English**: code comments, documentation, and **commit messages**. Conversation with the
owner **mirrors his language**: Portuguese in, Portuguese out; English in, English out. Conversation
is the interface, not the artifact. Material already written
in Portuguese is converted when it is edited for another reason, never as a task of its own.

### Model routing

Choose by capability class, never by model name: `scan` (sweeps, extraction — cheapest),
`implement` (writing code to an established pattern — mid), `judge` (architecture, security,
**any irreversible action** — most capable). An irreversible action moves *up* a class, and the
verifier never sits in the same class as the author.

Every agent declares `model:` explicitly. Inheriting the session is not deciding.
<!-- END foundation:standard -->

<!-- BEGIN foundation:code -->
### The part that only applies where there is code

> Delivered only to a starting point with source below it. A directory that
> analyses, curates or documents pays nothing for these rules — every line here is
> read on every turn of every session, and this park measured the price: context
> outweighs generation 165 to 1.

### Before implementing anything a user can drive

Invoke the **`branch-table`** skill. It is installed in this repository by the factory and carries
the procedure; what follows is the rule it enforces.

Write the **branch table** first, as an artifact: input → condition → response. Every row becomes a
test. A lookup needs at minimum: valid and found · valid and **not found** · malformed · upstream
down · quota exhausted · found but empty.

Typing code by hand forced you to arrive at the `else`. Commanding an agent does not. Nobody
enumerates the sad paths unless the table exists — and that is how a plate that does not exist
ended up on a 404 error page.

**Never invent data — not for a row, not for a test, not as an example.** A status, a code, a
message or a field another system sends exists only if it was returned: count it in the stored
responses and state the count before writing a rule, a test or a question about it. Zero means no
rule and no question. What a reviewer or a subagent typed as an example is a hypothesis until
counted — never relay it as a finding. Unrecognised values share one row; fixtures are cut from real
returns.

### Red-green is required — and checked only where this project said how

Write the test, **run it, watch it fail**, then write the least code that passes it. A test written
after the implementation is shaped by the implementation: it asserts what the code does rather than
what it should do, so it passes on the broken version too.

That is not a style argument here. Every test passed while paying customers could not see what they
had paid for — the suite was green about the wrong things.

**The gate installs only where `.githooks/config` declares `TEST_CMD`.** Measured across this park on
29 Aug 2026: not one project had it, so `check-red-green` had never run as a gate anywhere while this
very block said it was checked. If yours is unset, the requirement is on your honour until you set
it — `~/dev/foundation/tools/check-red-green .` says which you are.

The mechanical half:

```bash
~/dev/foundation/tools/check-red-green .
```

If the suite only runs inside a container — and in this park it usually does, because
`vendor/` is installed against the container's PHP and will not load on the host — pass the
command with `{dir}`, which expands to the directory under test:

```bash
~/dev/foundation/tools/check-red-green . --cmd \
  "docker run --rm -v {dir}:/var/www/html -v $PWD/vendor:/var/www/html/vendor \
   -w /var/www/html --network container:<db> <dev-image> vendor/bin/pest"
```

Without `{dir}` a container command tests the working tree twice and calls the result proof,
so the check refuses it.

It runs each new test against the commit you branched from and **refuses the ones that pass**,
because a test that passes without your change would not have caught your change being absent. It
runs them against `HEAD` first as a sanity probe: if they do not pass there either, it reports
`unknown` rather than reading a broken environment as proof.

The one exemption is a **characterization test** — coverage backfilled onto behaviour that already
existed. It passes on the base by definition, and it must be **declared** (`@covers-existing`, or a
`characterization` group). Undeclared, it is indistinguishable from a test written after the fact.

### A convention that lives in someone's head is not a convention

When you learn a rule this codebase must follow, ask whether it can be a **test** rather than a
paragraph. Prose binds whoever read it, in the session that loaded it; a test binds everyone.

One project in this park proved it: a 23-line `DateDisplayConventionTest` refused
`->format()` in a view from an agent that had never read a word about the convention. Twenty-three
lines did what no amount of documentation would have. `gate-authoring` carries how to write one so
it does not accuse the innocent.

### A test count is not evidence

Name the one transaction that must work — **paid → delivered** — and walk it end to end in a test,
plus a production probe. Never report a number of tests as evidence of health; report whether the
money path is covered, and say `unknown` when nobody checked. `money-path-auditor` exists to give
that question an answer other than a number.

Hundreds of green tests while paying customers saw nothing is the same false confidence as a
healthy timer with a broken alert.
<!-- END foundation:code -->
