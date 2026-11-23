---
name: systematic-debugging
description: Use when something in this project is broken and the cause is unknown — a failing test, a 500, a page that renders wrong, a deploy that succeeded and changed nothing, a job that never runs. Also use when the second fix attempt has failed, which means the hypothesis is wrong rather than the fix. Covers reading the actual signal and confirming by effect.
sources: [product-discovery/falsifiability]
ours: "verify the effect and not the exit code is this park's own scar tissue, from failures that all exited zero"
---

# Systematic debugging

## The rule that costs the most when ignored

**Verify the effect, not the command.**

The expensive failures in this codebase's history all exited zero:

- `config:cache` **succeeds** while writing default values over an unreadable `.env` — and the app
  then serves 404 for every route, with no error line anywhere
- a deploy ships a new image running old code, because a named volume only takes the image's content
  when it is **empty**
- an `unhealthy` container silently leaves the reverse proxy's pool: the domain serves 404 while the
  application inside is perfectly fine
- a plate that does not exist dropped the user on a **404 error page**, and every test passed while
  paying customers could not see what they had paid for

That last one is the shape to remember: **a green suite is not evidence.** It is evidence about the
cases someone wrote down.

So the first question is not *what went wrong* but **what would I see if it were working** — then go
look at that, not at the return code.

## The loop

**1. Read the actual signal.** Not the summary, not what you expect. The log line, the status code,
the row in the database, the rendered HTML. Quote it.

If there is no signal, that is the first finding and it usually has its own fix.

**2. State the hypothesis, and what would disprove it.** One sentence, falsifiable. "The container is
unhealthy" is a hypothesis. "Something is wrong with Docker" is not.

**3. Probe, do not fix.** Test the smallest thing that separates two hypotheses. A probe is cheaper
than a fix and tells you whether the fix is even aimed at the right thing.

**4. Fix, then re-run the original failing observation.** Not the command that just succeeded.

**5. If the second fix fails, stop fixing.** Two failed attempts means the hypothesis is wrong, and a
third attempt at the same hypothesis is the most expensive form of hope. Go back to step 1 and read a
signal you have not read yet.

## Where to look when the log says nothing

Ordered by how often it pays off:

1. **The layer below the one reporting.** A monitor showed a failure and sent no alert; three passes
   through its logs found nothing; the answer was in its **database** — the notification was attached
   to no monitor. The log was honest, it just was not where the state lived.
2. **The container, not the file.** Editing a compose does not change a running container. The
   restart policy in particular lives on the container: `docker update --restart=...`, or recreate.
3. **Permissions on anything the entrypoint touches.** An `.env` at mode 600 that the app user cannot
   read — and `config:cache` succeeds anyway.
4. **The healthcheck's own path.** A healthcheck on `/` for an app that redirects `/` reports sick
   while the app is well.
5. **Cache.** `config:cache`, `route:cache`, `view:cache` and the response cache all serve a past
   version of reality with total confidence.

## Absent is not zero

A query that returns nothing has two meanings — *there are none* and *I could not look* — and they
lead to opposite conclusions.

Before building on a zero, **prove the probe can see a positive.** Point it at something you know
exists. If it cannot find that either, the finding is about your probe.

## Two commands that mislead

- `docker compose config` **prints the interpolated `.env`** — secrets on your terminal. Use
  `config --quiet`.
- `curl -f` exits non-zero *after* `-w` already printed, so `... || echo '000'` concatenates into
  `000000`. Drop the `-f` when capturing the code.

## Before calling it fixed

- [ ] The original failing observation now shows the working result — you re-ran it
- [ ] You can say **why** it broke, not only what you changed
- [ ] If a test, guard or alert should have caught this and did not, that is a **second finding** and
      it does not get dropped — take it to `gate-authoring`
- [ ] If a user could drive this path, the branch that broke is now a row in a test
