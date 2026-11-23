---
name: flow-map
description: Use when the product is defined and no application exists yet — before Laravel, before Expo, before a single screen is coded. Produces the screen map as an artifact: which screens exist, what leads where, and which states each one has, including the ones nobody draws. Invoke after PRODUCT.md §1-2 and before the first migration. Also when someone says the app is done and nobody knows what happens when the list is empty.
ours: "putting the screen map before the stack came from this park's owner, and the forgotten states came from the 404 a nonexistent plate served in production"
---

# Screen map

## Why before the application

A drawn screen costs minutes. A built screen costs a day, and built wrong it costs the day plus the
day to undo it. The map is the cheapest thing you can be wrong about.

And it is **stack-agnostic**: the same screens hold for Laravel and for Expo, and the choice between
them can come afterwards. That is why it fits before the first migration — not as ceremony, but
because deciding screens while looking at code is already deciding late.

**This is not market research, and it does a job research does not.** Research tells you whether
anyone wants it; the map tells you what you will have to build. Drawing every screen forces you to
face what the product actually does — and drawing the sad states forces you to face what happens
when it does not.

## The artifact

A file, in the repository. Not a paragraph in a prompt, not a list in a chat — both disappear, and
this one has to survive to become screens and become tests.

**`docs/FLOW.md`, or wherever this project already keeps internal documentation.** Follow the
convention that is there instead of creating a second docs folder — `frotaspro` uses `.docs/`, and
the first real flow map in this park landed at `app/.docs/FLOW.md` for that reason. A measurement
from outside that only looked at `docs/` reported the file as missing and concluded, wrongly, that
this skill had never been used.

```
| Screen | Arrives from | States | Goes to | Branch table |
|---|---|---|---|---|
| Reading | Library, Today's queue | content · loading · source failed | Glossary, Review | docs/branch/reading.md |
```

That last column is what ties the map to what is already mandatory: **every non-happy state of a
screen is a row in the branch table of the feature it serves.** Do not invent the list of states —
derive it. If the table does not exist yet, the `branch-table` skill comes first.

## The states nobody draws

Every screen that shows data has at least these, and most maps carry only the first:

| State | The question it answers |
|---|---|
| **with content** | what shows when it worked |
| **empty** | first time, nothing there yet — and what the person does from there |
| **loading** | what they see while waiting, and after how long |
| **error** | when the source failed. **Never a generic error page** |
| **not permitted** | it exists, but not for them |

**Empty and first-time are not the same state.** "You have not added any text yet" invites; "No
results" in a freshly created library reads as a defect. Whoever arrives for the first time decides
right there whether they come back.

The **error** state is the one this park has already paid for: a plate that did not exist dropped
the user on a 404 page. The data layer knew — there was even a `PlateNotFound` model. The screen
layer never decided.

## The order

1. **List the screens** the product needs for PRODUCT.md §1 to happen. If a screen does not serve
   the stated problem, it is not in v1 — record it as out of scope and move on.
2. **Connect them**: where you arrive from, where you go. A screen with no entrance is orphaned; a
   screen with no exit is a dead end. Both are map defects, not code defects.
3. **Five states per screen.** Writing "not applicable" is an answer; leaving it blank is not.
4. **Point at each feature's branch table.** Whatever has none, you have just discovered is missing.
5. **Only then** decide stack, component and colour — and colour is decided by the owner, over a page
   the `visual-proposal` skill produces from this map. Tokens live in `design/tokens.json` and reach
   both destinations through `gen-tokens` — a colour is decided once, not once per platform.

## A mockup is for thinking, not for porting

Static HTML consuming the tokens is excellent for looking and changing. But **it does not become the
app**: React Native has no DOM and no CSS, and converting markup is wasted work. What survives from
mockup to app is the **decision** — which screens, which states, which token — never the markup.

If you build a mockup, write that inside it. Someone will try to reuse the HTML.

## Signs the map is lying

- **Every screen has only the happy state.** That is not a map, it is a shop window.
- **No screen leads to an error.** Either the product touches no network and no database, or you did
  not draw it.
- **One screen does three things.** It is probably three screens, and the decision to merge them has
  to be written down — once built, nobody remembers it was a choice.
- **The map has a screen no line of §1 asks for.** Scope arriving through the back door.

## What no tool does for you

Deciding what the person sees when it goes wrong. An agent fills the "error" column with "show an
error message" and that is not a decision — it is the absence of one, wearing the shape of a filled
table.
