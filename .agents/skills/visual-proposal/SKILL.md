---
name: visual-proposal
description: Use before the first screen of a product is coded, and before any redesign — when the screens are mapped and nobody has yet decided what they look like, or when the app still wears the starter kit's theme. Produces ONE page for the owner to approve — the direction, the colours as tokens, the type, and the main screens drawn mobile-first with their empty and error states — and records the approval in design/tokens.json, which gen-tokens refuses to project without. Also when someone says the interface looks generic, amateur, or like every other project.
ours: "the owner stated on 16/11/2026 that the first delivery of any interface is a page with the screens, colours and main-screen examples for the owner's approval, after measuring that three products of this park still wore the Laravel starter kit's theme; the recorded approval and the gen-tokens refusal are ours"
---

# Visual proposal

## Why this comes before any screen

Measured on 16/11/2026 across the park: frotaspro, prefs and personal-finance shipped with the Laravel
starter kit's theme untouched — Instrument Sans, accent `neutral-800`, byte-identical across three
products sold to three different audiences. frotaspro had even **decided** a palette in
`design/tokens.json`, and its web never consumed it: 3,400 raw `gray-*`/`zinc-*`/`blue-*` classes.

That is not a talent problem. Without a direction fixed before the first screen, an agent falls back
on the average of everything it has seen — the kit's theme, the default palette, a grid of cards — and
every project comes out the same. The order was already written in the frontend agent and was skipped
anyway. So the direction is now an artifact the owner approves, and the approval is recorded where a
tool checks it.

## Where it sits

```
flow-map (which screens, which states)  →  visual-proposal (what they look like)  →  owner approves
   →  design/tokens.json carries the approval  →  gen-tokens projects it  →  screens are built
```

It needs the screen map. If `docs/FLOW.md` (or this project's equivalent) does not exist, `flow-map`
comes first — a proposal over screens nobody listed draws the happy path only.

## Before drawing: the three facts the design answers to

Write them at the top of the page, one line each, from the project's README and plan — never invented:

1. **What it is and who uses it.** "Fleet managers at city halls, checking a vehicle from the yard" is a
   fact a design can answer to. "Modern and clean" is not.
2. **The device they are on.** Measured if the product is live (analytics, access logs), otherwise
   stated as an assumption. Assume phone unless the evidence says desk.
3. **What a customer must never feel.** For a paid lookup it is *"did I pay for nothing?"*; for a
   public service it is *"is this official?"*. That line decides more than any colour.

Then **three to five real products of the same category**, named, with what each one gets right — not
screenshots to copy, the decision worth taking from it. A public-sector product looks at public-sector
references; a consumer app at consumer apps. A proposal with no references is the average again.

## The page

One self-contained HTML page. In Claude Code, publish it as an **Artifact** and hand the owner the
link; in another harness, write the file and give its path. It contains, in this order:

| # | Section | What it must show |
|---|---|---|
| 1 | **The three facts and the references** | as above, short |
| 2 | **Two directions, side by side** | each with its palette, type pairing, radius and density, applied to the same key screen. Two, not one: the owner choosing between two is one round; sending one back is a round per attempt. They must differ in kind (dense and sober vs. airy and warm), not in shade |
| 3 | **The palette as tokens** | every colour named as it will be in `design/tokens.json` (`primary`, `surface`, `textMuted`, `danger`…), with the **contrast ratio** of each text/background pair the screens use. Below 4.5:1 for body text is a defect, not a style. A **dark theme** (`themes.dark.color`), per-space **accents** (`accents.<name>.light/dark`, only `primary`, `primaryAction`, `primaryTint`) and the **font** (`font.sans.family`, `features`) are tokens too: drawn in the proposal, fingerprinted by `gen-tokens`, approved together — changing one later is a new approval |
| 4 | **Type** | real font names, loadable (Bunny/Google Fonts), the scale in px, one paragraph of real copy set in it |
| 5 | **The main screens, phone first** | three to five screens from the flow map, **the money path first** (search → result → pay → delivered, or whatever this product's is). Each drawn at **375 px wide first**, then the desktop width as the expansion of that layout — never a desktop layout squeezed down |
| 6 | **The states nobody draws** | for each main screen, at least **empty** and **error**, from the flow map. A proposal with only the happy state approves a shop window |
| 7 | **What is open** | the decisions the owner has to make that this page does not settle |

The screens read their colours from CSS variables, and a toggle swaps the variable set between the two
directions. That is cheap, and it proves the palette works on real screens and not only on swatches.

**Real content, in the customer's language.** Real-looking plates, names, amounts and dates — never
lorem ipsum, which hides every layout that breaks on a long name. The product's **commercial** name,
never the internal one.

## What the page refuses to be

- **The starter kit's theme.** Instrument Sans with a `neutral-800` accent, or the framework's default
  palette, is the absence of a decision. If a direction ends up near a default, say why in one line.
- **A grid of identical cards** as the answer to every screen. Choose the layout per screen from what
  the person does there.
- **Taste without a reason.** Every choice ties back to the three facts: "managers check this
  one-handed in a vehicle, in daylight, so the primary action sits at the bottom and text contrast is
  7:1" is a reason; "it looks modern" is not, and the owner may overrule it.
- **Markup to port.** Write inside the page that it is a mockup: what survives is the decision — which
  screens, which states, which token — never the HTML. React Native has no DOM.

## The second round: an options board

Once a direction is chosen, what is left is a handful of independent questions — a dark theme or not,
one accent or one per space, how dense the list is. Do not redraw the page for each. Publish **one
board**: every open question as a numbered row, its variants side by side as lettered cells, each cell
applied to the same real screen, so the owner answers in one line of codes — *"1a, 2b, 3b2"* (row,
variant, sub-variant when a variant has one). That was personal-finance's second round on 16/11/2026:
the dark theme (1a) and per-space accents (2b) settled in one reply.

- **Two to four variants per row**, and one of them may be *"none"* — not having a dark theme is an
  answer.
- **Each row stands alone.** If choosing 2b changes what 3 means, say so on the row, or merge them.
- **Record the codes with the answer.** The code the owner typed and what it meant go in the commit
  that changes `design/tokens.json`, next to the proposal's link; a bare *"2b"* means nothing in a month.
- The chosen variants are tokens like any other — themes, accents and font included — so they go
  through `gen-tokens --approve` again: a new decision, a new fingerprint.

## The approval, and only the owner gives it

Present the link and stop. Do not build screens while waiting, and do not treat silence as approval.

When the owner approves — a direction, possibly with changes — put the approved tokens in
`design/tokens.json` and record it:

```bash
~/dev/foundation/tools/gen-tokens <project> --approve <artifact URL or path> --direction "<A, or what the owner chose>"
```

That writes a `$approval` block carrying the date, the proposal and a fingerprint of the tokens. Then
`gen-tokens <project>` projects them into the web and the app. **It refuses tokens with no approval, and
tokens changed after one** — a colour tweaked later is a new decision and goes back to the owner. Run
`--approve` only after the owner said so in their own words; it records that decision, it does not make
it. Commit `design/tokens.json` with the proposal's link in the message.

## After the approval

- Screens consume the tokens — `bg-primary`, `text-text-muted` — never a raw `bg-gray-500`. A raw class is
  a colour decided again, per screen, by whoever typed it.
- Check each screen at 375 px before calling it done: no horizontal scroll, tap targets of at least
  44 px, inputs at 16 px or more (smaller makes iOS zoom in).
- If what you build drifts from the page, the page or the build is wrong — bring it back to the owner,
  do not let it settle silently.
