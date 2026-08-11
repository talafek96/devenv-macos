---
name: resume-remote-handoff
description: >
  Reconstruct and continue software work that was stopped on a different,
  unreachable Claude instance — another machine, a separate standalone session,
  or an agent whose local state you can't access — and author self-contained
  handoffs for an unattended/offline agent to pick up. Use this skill whenever a
  task involves "continue what the other agent/session did", "pick up where the
  remote machine left off", "the other instance is gone, keep going", resuming a
  teammate's or coworker's in-progress branch you didn't author, or preparing a
  handoff/kickoff message for an offline, unattended, or remote run — even if the
  user doesn't say the word "handoff". The core discipline: reconstruct state
  from committed artifacts (git history, spec status, task checklists), never
  assume local memory files (HANDOFF.md, notes, scratchpads) survived the trip.
---

# Resuming work across unreachable Claude instances

Two situations, one root principle. You are either **picking up** work an
unreachable instance left behind, or **authoring** a handoff so a future
unreachable instance can pick up yours. Both hinge on the same fact:

> **Local memory does not travel. Only committed artifacts do.**

Files a previous instance relied on for continuity — `HANDOFF.md`,
`PITFALLS.md`, `progress.md`, scratchpad notes, uncommitted diffs — are
frequently gitignored or machine-local. On a fresh clone or a different box they
are simply absent. So the durable record of "what happened and what's next" has
to be reconstructed from, and written into, things that are committed to the
repo: commit messages, a spec/design status banner, a task checklist, ADRs.
Treat any local memory file as a *bonus you cross-check*, never as the source of
truth.

Read the section for your situation. When you're both finishing someone's work
*and* leaving it for the next unattended agent, do both, in order.

---

## Part A — Picking up work from an instance you can't reach

You've been told to continue work someone (or some past session) started, and
you can't ask them anything. Rebuild the picture before you touch code.

### 1. Reconstruct state from committed evidence, in this order

The point of the ordering is trust: git and in-repo docs are what actually
crossed the gap; prose memory may not have.

- **`git log --oneline -30`** and *read the commit messages*. They are the real
  changelog — each subject line is a claim about what was done. `git diff` the
  commits that matter to confirm the claim matches the code.
- **In-repo status the origin deliberately left behind:** a spec or design doc's
  "implementation status" banner, a `tasks.md` / checklist with `[X]`/`[ ]`
  boxes, a decisions/ADR file. This is the *authoritative plan*; the commits are
  the *evidence of progress against it*. Where they disagree, the code wins.
- **Local memory files (`HANDOFF.md`, `PITFALLS.md`, notes) only if present.**
  Useful color, but possibly stale or from another machine entirely. Cross-check
  every claim against git before believing it.

### 2. Verify real git state before believing any prose

Prose says "pushed to the branch"; reality might differ. Confirm:

- current branch, `HEAD` vs `origin/<branch>`, and whether the tree is clean;
- that the branch you were told about actually exists and points where claimed.

A one-line mismatch here ("the summary said X was merged; origin/main doesn't
have it") is worth surfacing immediately — it changes everything downstream.

### 3. Establish a green baseline BEFORE changing anything

Run the project's documented build + full test suite and record the pass count.
This does two jobs: it proves the inherited state actually works, and it gives
you a reference so that if something breaks later you know *you* did it.

If the baseline is **not** green, stop and report it. Do not build new work on a
red baseline, and do not silently "fix" a pre-existing break — it may be
load-bearing, or a known in-flight state the origin left deliberately.

### 4. Reconcile the recorded plan with what you actually find

A status banner claiming "module X done" while its tests are commented out, or a
recorded finding like "substrate Y turned out unusable, recommend Z instead" —
these are *inputs to a decision*, not settled facts. Confirm against the code,
and treat a recommendation the origin wrote as a proposal to verify, not an
order to execute blindly.

### 5. Continue *from* the plan, don't reinvent it

Execute the next steps the committed plan already defines, in its stated order.
If the plan is sound, following it is how you stay coherent with an author you
can't talk to. Only deviate when the code forces it — and when you do, record
why (see Part B: your deviation is the next instance's "recorded finding").

---

## Part B — Authoring a handoff for an unattended / remote agent

You're leaving work for an instance that will run **without you online** — a
remote box, an overnight unattended loop, a teammate's fresh session. The
failure mode to design against is the one from Part A: the agent arrives, your
local notes aren't there, and it either flails or silently does the wrong thing.

Two rules shape a good handoff:

1. **Direct to authority; don't duplicate it.** The spec, the task list, the
   conventions, and the code are already in the repo and already travel. Copying
   their contents into the handoff just creates a second source that drifts out
   of date. Point at them and tell the agent to *work from them*.
2. **Carry only the delta they can't derive.** Current position, hard-won
   gotchas, exact commands, and the rules of autonomy — that's what isn't
   already written down anywhere the agent can read.

If a fact belongs in the repo (a status, a decision, a pitfall), **commit it
into the repo** — a status banner in the spec, a checked box in `tasks.md` — so
it travels on its own and the handoff can just point at it. The handoff message
itself may not survive; the commit will.

### Handoff structure

Keep each pointer to a line; spend your words on the delta and the guardrails.
See `references/handoff-template.md` for a filled-in, real-world example you can
adapt.

- **Pointers to authority (one line each):** the plan/design doc (with the
  section that is the live sequence), the task checklist to keep current, the
  conventions/rules file, and *one reference module or file to copy in style*.
  "Work FROM these; don't wait for me on anything they already decide."
- **Current state — the delta:** branch name, `HEAD` commit, what's done vs.
  pending, and the key hazards already discovered (with where each is recorded
  in-repo, so it survives even if this message doesn't).
- **Operational recipes the docs lack:** exact commands or scaffolds the agent
  needs that aren't obvious from the repo — e.g. a throwaway build scaffold to
  add, verify against, and revert before committing; a known gotcha in how a
  test must be structured.
- **Autonomy protocol (offline-safe, self-verifying):**
  - work only on the designated branch; **never push to the shared mainline**
    (a human merges) and never force-push or rewrite shared history;
  - after *every* change: build clean + run the full suite; commit only when
    green; each commit builds standalone;
  - update the in-repo checklist as tasks complete, so progress travels;
  - on a shared machine, scope any recursive `find`/`grep` to the user's own
    directories;
  - if anything fails, hangs, or is genuinely ambiguous: **stop, leave the tree
    clean (or WIP on a scratch branch), write a clear note, and halt — don't
    thrash.** An unattended agent that stops cleanly is recoverable; one that
    guesses and pushes is not.
- **Hard-stop boundaries — human-only, never unattended:** the irreversible or
  atomic steps (a cutover that deletes the old path, a mass rewrite), edits to
  submodules/vendored code, wiring any secret or API key, and *any genuine fork
  in the plan*. Name them explicitly so the agent knows exactly where its
  authority ends.
- **Definition of return-done:** what the human should find on return — green
  commits on the branch, checklist updated, mainline untouched, hard-stops not
  attempted, and a note of done/next/blockers.

---

## Cross-cutting discipline

- **Committed over local, always.** Anything the next instance must know goes
  into a traveling artifact (commit message, spec status, checklist), not a
  local memory file — because you cannot know which machine reads it next.
- **Verify before trust.** Real git state over prose claims; a green run you
  performed over a green run you were told about.
- **Report faithfully.** If tests fail, say so with the output; if you skipped a
  step, say that; state what's actually done, not what was planned.
