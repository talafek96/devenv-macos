# Worked example — an unattended remote-agent handoff

A real handoff written for an agent that would run offline on a remote machine,
continuing a C/C++ refactor. Use it as a shape to adapt, not a form to fill
verbatim. Note how every convention/plan detail is a *pointer*, and the body is
current-state + recipes + guardrails.

---

```text
# Handoff — <project> <migration/task name> (UNATTENDED remote run)

You are continuing <task> on a remote machine, running UNATTENDED (the human is
OFFLINE). Work autonomously FROM the committed spec, verify yourself after every
change, commit only when green, and STOP at the boundaries in §5 rather than
guessing.

Work FROM the spec — do not wait for the human on anything it already decides.
This message is only the delta the spec can't carry. Everything else is
authoritative in the repo:
- Plan / sequence + per-item detail:  <path/to/design-doc.md>  (§X = live sequence)
- Task checklist + status banner:     <path/to/tasks.md>  — mark [X] as you finish
- Conventions to follow:              <path/to/rules.md>, <decisions.md>
- Reference to copy in style:         <path/to/reference_module.{h,c}>

Branch: <branch>  (git checkout it; == origin/main + <N> commits).

## 0. Environment + baseline (before ANY change)
- <one-time setup: hooks, submodules, deps and where they come from>.
- Prove baseline green FIRST: <build cmd> (exit 0) then <test cmd> → <N/N>.
  If not green, STOP + note; don't build on red.

## 1. Current state (delta the spec doesn't track)
<HEAD commit> = <what's landed>. Work is ADDITIVE: <why main stays green>.
Read the design doc + conventions before writing code.

## 2. Your scope this run — the next steps, in order (don't invent a plan)
1. <next step, with WRAP-vs-PORT / approach already decided by the spec>
2. <next step>
Follow the module pattern in <rules.md> + the <reference_module> reference.

## 3. Operational recipe the spec lacks
<exact commands / throwaway scaffold to add, verify against, then REVERT — never
commit it. Plus any known gotcha in how a test must be structured.>

## 4. Autonomy protocol (offline-safe, self-verifying)
- Work ONLY on <branch>; push there after each verified unit. Do NOT push to
  main (human merges); never force-push / rewrite history.
- After every change: build (exit 0) + verify + full suite green. Commit only if
  green; each commit standalone; mark the task [X] in <tasks.md>.
- If anything fails/hangs/is uncertain: STOP, leave the tree clean (or WIP on a
  scratch branch), write a clear note, halt — don't thrash. Scope find/grep to $USER.

## 5. HARD STOP — human-only, never unattended
- <the irreversible / atomic cutover step>.
- <edits to vendored/submodule code; wiring any key or secret>.
- Any genuine fork, ambiguity, or blocker.

## 6. What the human checks on return
New green commits on <branch>, each standalone-green with tests, <tasks.md>
updated; a clear note of done/next/blockers; main untouched; the §5 items NOT
attempted.
```

---

## Why it's shaped this way

- **§0 baseline-first** is Part A discipline turned into an instruction for the
  next agent: prove green before trusting the inherited state.
- **§1 "delta the spec doesn't track"** is the whole reason the message exists —
  everything else is a pointer because the repo already carries it.
- **§4 verify-each + commit-only-green** makes an offline agent self-correcting:
  it can't ask you, so the test suite is its only feedback signal.
- **§5 hard-stops** draw the authority boundary explicitly. An unattended agent
  errs safest when "where do I stop?" is answered in writing, not guessed.
