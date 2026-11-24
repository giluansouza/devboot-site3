---
name: branch-table
description: Use BEFORE implementing anything a user can drive — a lookup, a search, a form, a webhook, a payment step, a chat command. Produces the branch table (input → condition → response) as an artifact, so the sad paths get decided instead of discovered in production. Invoke when starting a feature, when a bug report says "it just showed an error page", or when someone says the tests are green but users are complaining.
ours: "enumerating sad paths came from this park's own 404 on a plate that did not exist, not from a body of practice"
---

# Branch table

## Why this exists

Typing code by hand was a forcing function. The language makes you arrive at the `else` — you cannot
type the happy path and leave a branch undecided, because something has to be there.

Commanding an agent removes it. The owner describes the happy path, a plausible implementation
appears that also covers the happy path, and **nobody enumerates the sad paths**. The decision tree
that used to live in the coder's head while typing is now written down nowhere.

Two failures paid for this skill, both on the same product:

- Typing a plate that does not exist dropped the user on a **404 error page**. Not a model failure —
  a branch nobody declared. The application even had a `PlateNotFound` model: the data layer knew,
  the presentation layer never decided.
- Every test passed while paying customers could not see what they had paid for.

## The rule

**No implementation of user-driven behaviour begins before the table exists.**

The table is an artifact — a file, in the repository, next to the feature. Not a paragraph in a
prompt, not a list in a chat message. Both disappear; the table has to survive to become tests.

## The shape

| Input | Condition | Response |
|---|---|---|
| what arrives | what is true about it | what the user gets |

The response column is the one that matters. `"error"` is not a response. `"404"` is not a response.
Write what the human sees and what they can do next.

## A row needs proof that its condition happens

A table is not a licence to imagine. There are two kinds of condition, and only one of them is free:

| Kind | Examples | What it needs |
|---|---|---|
| **structural** — true by how the system is built | input missing or malformed, record not found, dependency unreachable, request repeated, sender unknown | nothing; every row in the list below is of this kind |
| **a value somebody else sends** — a status, a code, a message, a field from a supplier, a gateway, a regulator, an import | `status: "BAIXADO"`, `codigo: "3"`, a refusal text | **a real occurrence**: its count in the stored responses, a captured real body, or the sender's own documentation — written in the row |

**Count before you write the row.** Zero occurrences means no row, no test, no code, and no question
to the owner. State the count and where you counted it.

Every value never seen shares **one** row — *a value we do not recognise → what the user gets*. That
row is what makes the invented ones unnecessary: it covers all of them, including the ones nobody
thought of.

A string a reviewer, an auditor, a subagent or you typed as an example is a **hypothesis**. It
becomes a row when the count comes back above zero, not before. Relaying it as a finding is how one
product here took a list of lien statuses to its owner as a decision to make — they existed only in
an auditor's test strings, with zero occurrences in everything the supplier had ever returned.

Test data follows the same rule. What stands in for another system's answer is **taken from a real
return**, trimmed and with personal data replaced — never typed from imagination. A fixture with no
real counterpart is a claim about a system you do not own.

## The rows that get forgotten

Start from these. They are not exhaustive; they are the ones absent from every first draft:

| Row | Why it is missed |
|---|---|
| valid, found | never missed — it is the demo |
| **valid, not found** | the branch that produced the 404 |
| malformed input | "the form validates it" — until an API client does not |
| upstream dependency down | only ever tested by an outage |
| quota / credit exhausted | fine until the account has volume |
| found but empty | the shape exists, the content does not |
| duplicate delivery | webhooks retry; charging twice is a refund |
| unauthenticated / unknown sender | on a chat channel the sender is a phone number, not a session |

For anything that takes money, one row outranks the rest: **paid → delivered**, end to end. If it is
not in the table, stop and add it before continuing.

## Then what

1. Write the table. Show it before writing code — it is cheaper to argue about a row than about an
   implementation.
2. Hand it to the `failing-test-author` subagent. One test per row, each proven to fail for the right
   reason.
3. Implement until they pass. The table stays in the repository as the record of what was decided.

## Red flags

| Thought | Reality |
|---|---|
| "The framework handles that case" | Then write the row and let the test prove it. |
| "That can't happen" | If the structure of the system allows it, write the row. If it is a value nobody has ever received, it belongs to the *do not recognise* row — do not write one for it. |
| "The supplier might send…" | Count it. *Might* is not a row. |
| "I'll add the edge cases after" | The happy path shipped alone is exactly how the 404 reached users. |
| "The table is obvious, I'll keep it in my head" | That is precisely what stopped working when you stopped typing the code. |

## What no tool can do for you

Nothing enumerates the branches. That thinking stays the owner's — it is domain knowledge, not
mechanics. What tooling *can* do is refuse to move on while the table is empty, and check that every
declared row has a test. Same move as a compose linter: it does not understand your architecture, it
just will not let you ship a database you forgot to close.
