---
name: shipping-to-production
description: Use before any deploy of this project, when the release script fails or is being changed, and whenever something is wrong in production. Covers what the release gates refuse and why, the migration rule that cost a week of sales, confirming a deploy landed instead of trusting that it exited zero, and the version — cutting it in CHANGELOG.md, the SemVer bump, and the tag release.sh creates.
ours: "the release gates came from this park's own deploy incidents; no source is claimed. The versioning grammar adopts Keep a Changelog 1.1.0 and SemVer 2.0.0 by name, as the owner decided on 11/11/2026; the gates over them are ours"
---

# Shipping to production

## The flow, and it does not bend

**Agents do not change production.** Diagnose read-only, hand the exact command over, the owner runs
it, then verify the effect.

Code on the VPS is immutable: nobody edits it there. A fix goes dev → deploy. Editing on the server
is the origin of every drift, because the next deploy silently overwrites it and the fix disappears
with no error.

## `release.sh` is the only way

It is the source of truth for this project's deploy. Do not reproduce its steps by hand — the steps
are not the point, the **gates** are, and running the commands yourself skips exactly the checks that
exist because something already went wrong.

Two of its gates are hard and have no escape:

**Branch.** Production deploys only from `master`. No flag turns this off.

**Pending migrations.** If `master` carries a migration that is not applied, the deploy stops. This
gate exists because a deploy went out without its migrations and **this product went a week without
selling.** Nobody noticed, because nothing failed — the application answered 200 and simply could not
complete a purchase.

That is why the check runs **before and after**: a deploy that applies migrations halfway is worse
than one that refuses to start.

A third hard gate, in production only, is the **version** — next section.

## Versioning

Decided by the owner on 11/11/2026. **SemVer 2.0.0** (`X.Y.Z`, no pre-release suffix), one version
per repository. `CHANGELOG.md` sits at the **repository root** in the **Keep a Changelog 1.1.0** form,
in English. The commit that reached production gets the annotated tag `vX.Y.Z`, and `release.sh`
creates it and pushes it to `origin`, never a person.

- **MAJOR**: a change that breaks an installed client, like a public API (`/api/v1`) or the mobile app.
- **MINOR**: a feature.
- **PATCH**: fixes only.

The grammar `release.sh` reads. It parses only the top two sections. Older history is never judged,
whatever form it is in:

```markdown
# Changelog

## [Unreleased]

## [2.0.0] - 2026-11-12
### Added
- Fuel orders take a trip justification when the organization requires it.
### Changed
- **BREAKING** `/api/v1/vehicles` no longer returns `plate_raw`.
### Fixed
- Plate search ignored lowercase input.
```

- `## [Unreleased]` comes first. It is optional, but every merge to `master` adds one line under it.
- `## [X.Y.Z] - YYYY-MM-DD` is the version being released, and it needs at least one entry.
- The headings are only `### Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`. Entries
  start with `- `.
- `**BREAKING**` right after the `- ` of an entry marks a MAJOR change (in the middle of a line it is
  just text). Over `1.x` it must come with a MAJOR
  bump (`0.x` may break on a MINOR, as SemVer allows).
- There is no "Deploy steps" and no "API" section. An API change is an entry like any other, marked
  `**BREAKING**` when it breaks a client. A step someone must do by hand at deploy belongs in the
  release (a migration, a seeder, a command in `deploy.sh`). A changelog line does not make it
  happen.

**Cutting a version is a commit, made before the release.** The bump is a judgement about installed
clients, so it belongs in a reviewed commit and not in a flag typed at deploy time. Rename
`## [Unreleased]` to `## [X.Y.Z] - <today>`, put an empty `## [Unreleased]` back on top, and commit it
on `master`. Then run the release.

What a production release refuses (exit 2, `status=version-refused`):

| Refused | Fix |
|---|---|
| no `CHANGELOG.md` at the root, in `HEAD` | create it. The first time, cut the version that is live today |
| a heading outside the grammar in the top two sections | use the grammar above |
| no version section | cut one |
| a version with no entries | write what changed |
| entries still under `[Unreleased]` | they ship in this release: move them into the version |
| `vX.Y.Z` already tagged **on another commit**, here or on `origin` | cut the next version |
| the version is not above the latest `vX.Y.Z` tag | versions only go up |
| `**BREAKING**` without a MAJOR bump over `1.x` | bump MAJOR, or remove the marker |

It passes and warns on `### Added` in a PATCH. It treats the **same code already tagged** as a
redeploy: it passes and creates no new tag. "The same code" means the same commit, or, in a repository
where the app is one directory of several (confereplaca's `web/`), a commit that changed nothing in
that directory. A redeploy whose tag never reached `origin` pushes it.

The gate reads `CHANGELOG.md` **as committed in `HEAD`**. A cut you made in the editor and did not
commit does not count, and the refusal says so. `--explain-gates` reports the version verdict and
exits 0.

The tag is created **only after production is healthy**, and only when the image is the commit the gate
checked. Health failing, maintenance mode stuck on,
or migrations still pending all exit 3 untagged, and the release prints the command to tag later. An
image built with `--allow-dirty` is not a commit, and an image built after `master` moved under the
release is not the commit that was checked, so neither is tagged. The tag message names the
image tag (`app 1.1.0 — production, image 3f2a91c`), and the last line carries `version=1.1.0`. To go
from what runs to its version: `verify` prints `commit:` from the image's own label
(`org.opencontainers.image.revision`, set by `build.sh`). It does not read the image tags, because the
server's nightly prune leaves only `:latest`. An image built before the label says `unknown`. Then
`git describe --tags --match 'v*' <commit>` names the version. It prints
`v1.1.0` when that commit is the tag, and `v1.1.0-3-g<sha>` for a redeploy whose commit differs only
outside the app directory.

Staging is neither gated nor tagged. A mobile app built with EAS does not go through `release.sh`,
and nothing here checks it yet.

## If gates fail every time, the gates are the bug

A release script whose gates always fail gets run with `--skip-gates` every time, and then it
protects nothing. If you are reaching for that flag habitually, **stop and fix the gate** — that is a
real finding and it is more urgent than the deploy.

## Verify the effect, not the exit code

The deploy exits zero and that means nothing:

- a named volume only takes the image's content when it is **empty** — without wipe-and-copy the new
  image runs the old code, no error
- `config:cache` **succeeds** over an unreadable `.env` and the app serves 404 for everything
- an `unhealthy` container leaves the proxy pool: the domain 404s while the app inside is fine
- a zero-byte tarball sails through a backup unnoticed

So after every deploy, look at something that only changes when it worked:

- [ ] the health endpoint answers, and answers the **new** version
- [ ] one page that exercises the change renders correctly
- [ ] migrations ran — check the migrations table, not the log line
- [ ] the container is `healthy`, not merely `Up`
- [ ] **the money path completes end to end** — the one transaction that must work

That last one is the only test that matters on a bad day. A count of passing tests is effort, not
coverage. Report whether the money path is covered, and say `unknown` when nobody checked.

## When production is wrong

Read-only first, always. Reproduce it in dev before changing anything — a fix applied straight to
production cannot be verified and cannot be rolled back cleanly.

If the cause is unknown, use `systematic-debugging`. If a guard should have caught it and did not,
that is a second finding: take it to `gate-authoring` so the next one is refused before it ships.

## Rolling back

Know the rollback command **before** you need it, and confirm it exists for this project. A deploy
you cannot reverse is not a deploy, it is a commitment — and by the rule this project runs on,
irreversible actions get more care, not less.
