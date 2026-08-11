---
name: reconcile-docs
description: >-
  End-of-session documentation reconciliation. Bring the project's living docs
  (HANDOFF.md, PITFALLS.md, and any relevant docs/) into full agreement
  with the current system state after work just accomplished, immediately before
  taking a break or handing off. The bar is not "the docs mention the new state" —
  it is that an operator who READS each document in full, top to bottom, and
  EXECUTES as they go, lands in the correct final state, having encountered zero
  contradictions. Use when wrapping up a work session, "updating the docs",
  "making the docs current", "writing things up before a break", or before
  stepping away from a project that has HANDOFF/PITFALLS files. NOT for
  generating a compaction prompt for the next agent. NOT for a quick throwaway
  task that moved no durable project state.
---

# reconcile-docs

Reconcile the project's living documents with reality before a break, so a fresh
operator can reproduce the current system state from the docs alone.

The core verb is **reconcile**, not **update**. "Update" tolerates additive edits.
"Reconcile" demands that every surviving claim in a document agrees with every
other claim in that document, with the other documents, and with the actual system.
The docs usually **already exist** and may **already assert things that are now
false or that contradict each other**. Your job is to make the contradictions gone
— at the source — not to bury them under a fresh section.

## The two documents

Each has a distinct job; keeping them distinct is what stops them from drifting
into one contradictory blob:

- **`HANDOFF.md`** — a **local (gitignored)** ramp-up doc whose whole purpose is to
  let any engineer pick up the work and get productive fast, so a handoff costs
  minutes, not days: what's done (with evidence), what's in-flight or half-done, the
  immediate next steps, open decisions, and how to reach a working setup. It is the
  single place progress lives — do **not** also keep a separate `progress.md` that
  can drift from it. Rewritten to stay current, not appended to indefinitely.
- **`PITFALLS.md`** — a **local (gitignored)** record of hazards and gotchas: things
  that look right but bite, non-obvious constraints, and "don't do X because Y"
  hard-won lessons.

If a doc in scope does not exist yet, **create** it from the ground truth (step 1
below): reconciling is the steady state, and the first run bootstraps the file.

## The acceptance contract (the oracle)

> A stranger who never saw this session opens each document, reads it **in full,
> from the first line to the last**, executes every instruction in order, and
> arrives at the **correct current system state** — without ever hitting a
> statement that contradicts another, points at a path that no longer holds, or
> requires knowledge that lives only in this chat.

This is a **linear read-through test**, and it is pass/fail. "The operator *could*
follow the docs" is not the bar — an operator reading top-to-bottom must not be
led astray by a stale passage they encounter *before* the corrected one.

## Two failure modes this skill exists to prevent

1. **Append-and-leave-the-contradiction.** Tacking a new "current state" section
   onto the end while an earlier passage still claims the old, now-false thing.
   This passes a lazy "can you follow it?" glance and **fails the read-through**:
   the operator meets the stale instruction first and diverges. Appending is
   allowed **only when the document remains internally consistent end-to-end after
   the append.** If the new content contradicts old content, you must change,
   supersede, or delete the old content — not just add next to it.

2. **Scatter-and-narrate.** Sprinkling disconnected paragraphs through the files
   and conveying the real procedure to the user in chat. The chat will not exist
   next session. The **documents are the deliverable** and must stand alone. If a
   step can only be understood from something you said in conversation, the doc is
   incomplete — fix the doc, don't explain it in chat.

## Procedure

### 1. Establish ground truth — what the system actually IS now
Before touching a doc, determine the real current state, from evidence not memory:
- `git log` since the session start / last doc update; what files changed.
- What was actually accomplished, what runs, what passes, what is half-done.
- What commands/paths/names are real *right now* (verify the ones the docs cite).

You are reconciling docs *against this*, so it has to be solid first.

### 2. Inventory the docs in scope
`HANDOFF.md`, `PITFALLS.md` at repo root, plus any `docs/` page the
session's work touched or invalidated. Read each one **completely** — you cannot
detect a contradiction in a passage you didn't read. If one is missing, creating
it (per "The two documents") is part of this pass.

### 3. Claim-audit each document
Walk each doc and tag every load-bearing claim:
- **still-true** — leave it.
- **now-false** — the world moved; this is a hazard (a once-right command can turn
  destructive). Must be corrected or removed.
- **now-incomplete** — true but missing what changed this session.
- **internally-contradicted** — disagrees with another passage in the same doc or
  a sibling doc. One of them must yield.

### 4. Reconcile at the source
Rewrite so each document, read **linearly**, is internally consistent and matches
ground truth:
- Resolve every contradiction where it lives — edit the stale passage, don't
  out-vote it with a later one.
- Delete or explicitly supersede stale instructions. Removing a hazard is worth
  more than preserving history; if history matters, move it to `.archive/`.
- Keep one source of truth per concern (per the project's doc model); let indexes
  link, don't duplicate facts that can drift apart.
- Append only when end-to-end coherence survives it.
- Document the **undo** beside the **apply** where a step is consequential.

### 5. Run the read-through (the gate)
Now BE the stranger. For each document, read top to bottom and trace execution:
- Does following it in order reach the correct final state?
- Did you pass any statement that contradicts a later one, or reality?
- Did any step require knowledge not on the page?

Any "no" / "yes-contradiction" / "off-page knowledge" → the **document** is wrong,
not the operator. Go back to step 4. Do not patch the gap by telling the user.

### 6. Then close out
Only once every in-scope doc passes its read-through, report what was reconciled
(which docs, which contradictions resolved, what was archived) and that the
acceptance contract holds. Now it is safe to take the break.
