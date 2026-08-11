---
name: claude-md-standards
description: >-
  Create, lint, edit, or review CLAUDE.md files (and AGENTS.md — near-identical
  format, lessons transfer) against industry-wide best practices. Use whenever
  the user wants to write, audit, clean up, shrink, split, refactor, or
  "improve" a CLAUDE.md / AGENTS.md / agent-instruction / agent-memory file, set
  up `.claude/rules/`, bootstrap agent context for a repo that has none, or asks
  whether their CLAUDE.md is any good — even if they just say "my CLAUDE.md is
  too long", "check my agent instructions", or "how should I structure this".
  Ships a real linter script, so also use it to mechanically check a file for
  secrets, dangerous example commands, broken @imports, size/budget, and vague
  instructions.
---

# Authoring and linting CLAUDE.md files

A `CLAUDE.md` (and its cross-tool cousin `AGENTS.md`) is persistent context fed
to a coding agent at the *start of every session*. That framing drives every
rule here: a line in this file is not documentation a human reads once — it is
re-transmitted to a model on every run and spends part of a finite attention and
token budget each time. So the goal is never "write down everything true about
the repo"; it is **the smallest set of high-signal, checkable instructions the
agent genuinely cannot infer on its own.** Less is more, but *specific* less.

The same file is read as context by other tools too, so the advice below is
Claude-Code-first but calls out where behavior is tool-specific.

## Which job is this?

Route to the matching section; each points at the deeper reference file.

| The user wants to…                                   | Go to        |
|------------------------------------------------------|--------------|
| Check / audit / "is this good?" an existing file     | **Lint**     |
| Shrink, split, dedupe, de-stale a bloated file       | **Edit/refactor** |
| Write one for a repo that has none                   | **Create**   |

More than one can apply (create → then lint the draft; lint → then refactor what
it found). Do them in that order.

## Core principles (the "why" behind every rule)

Internalize these five; the specific rules are downstream of them.

1. **Context, not configuration.** Claude *reads* CLAUDE.md as guidance — it does
   not *enforce* it. Anything that must be guaranteed (tests run before commit,
   formatting) belongs in a **hook** or CI check, not in prose here. Telling the
   file to do a linter's job is the single most common wasted instruction.
2. **Specific and checkable beats general and true.** "Use React 18 with the App
   Router" and one real code snippet beat "follow front-end best practices."
   Anything the model already knows, or can't verify, is noise.
3. **Every line costs budget every session.** Frontier models track on the order
   of a couple hundred discrete instructions reliably and degrade past that; the
   tool's own system prompt already spends some of that before your file loads.
   Short is not aesthetic — it is functional.
4. **Put detail where it loads only when needed.** Root CLAUDE.md loads every
   session; a **nested** `CLAUDE.md` loads only when a file in its directory is
   touched; a `.claude/rules/*.md` with a `paths:` glob loads only for matching
   files. Scope detail down the tree instead of piling it into the root.
5. **It rots.** An unowned file that only grows is the default failure mode. Give
   it an owner, review changes to it like code, and re-lint periodically.

## Lint

Run the bundled linter — it does the mechanical checks deterministically so you
can spend judgment on the rest:

```sh
python .claude/skills/claude-md-standards/scripts/lint_claude_md.py <file-or-dir> --opinionated
```

- Pass a **directory** to scan the whole repo (root + nested CLAUDE.md +
  `.claude/rules/*.md`) and get cross-file duplicate-content detection. It prunes
  `.git`, `node_modules`, `obj`, `build`, etc., so it is safe to point at a repo
  root — but do **not** point it above the repo (see the devpod filesystem rules).
- `--opinionated` adds the lower-confidence checks (hedging, filler,
  instruction-count). Drop it for only the high-confidence findings.
- `--json` for machine-readable output; `--strict` to make warnings fail the exit
  code; `--no-strong` for hard rules only. Thresholds (`--max-lines`,
  `--error-lines`, `--import-depth`, …) are all configurable per project.

**Interpreting results — respect the confidence tiers** (this is deliberate; do
not "fix" everything with equal force):

- **`error` / `[hard]`** — mechanical and near-certain (secrets, dangerous
  example commands, broken/circular `@import`s). Fix these first and always.
- **`warning` / `[strong]`** — multi-source consensus (size budget, vague
  instructions, unscoped rule files, content placement). Act on them by default,
  but the *thresholds* are project preferences — a team may legitimately set
  `--max-lines 300`.
- **`info` / `[opinionated]`** — one credible source, or genuinely unsolved
  (hedging, filler, staleness). Raise them as suggestions; never present them as
  hard rules.

Two important things the script **cannot** judge and you must, by reading the
file: **staleness** (does an inline snippet still match the real source? prefer a
`file:line` pointer over a copy) and **whether "necessary" content is truly
necessary** (could the model infer it from the code?). The full rule catalog,
with the source and confidence behind each rule, is in
[`references/lint-checklist.md`](references/lint-checklist.md) — read it when you
need to explain or justify a finding, or tune what runs.

## Edit / refactor

For a bloated or stale file, follow the measure → decide → dedupe → re-measure
loop. The key decision is **why** it's oversized, which picks the fix — and the
traps (especially that `@import` is *not* lazy loading) are easy to get wrong.
The full decision tree lives in
[`references/workflows.md`](references/workflows.md#editrefactor); the short form:

1. **Lint first** to get numbers and clear all `error`s before touching structure.
2. **Route each oversized chunk by cause:**
   - Generic / inferable content → **delete** it (highest leverage, zero loss).
   - Necessary but *directory-specific* detail → move to a **nested `CLAUDE.md`**
     (loads on demand).
   - Necessary, *cross-cutting*, topic-coherent detail → move to
     **`.claude/rules/<topic>.md` with a `paths:` glob** (loads only for matching
     files).
   - Deep reference rarely needed in full → move to a docs file and leave a
     **one-line pointer** (progressive disclosure).
   - **Trap:** `@import` still loads the imported file into context at launch — it
     organizes *source text*, it does **not** reduce what loads. Only nested files
     and path-scoped rules are truly lazy.
3. **Dedupe across the hierarchy** — delete anything a child restates from an
   ancestor; inheritance is automatic (root-to-cwd concatenation).
4. **Re-lint** to confirm you actually reduced size, not just moved bulk around.

## Create

**There is a real, unresolved disagreement here — surface it, don't silently pick
a side.** Anthropic's docs say run `/init` and refine the output; a credible
practitioner camp argues *against* auto-generation because a bad line in this
file compounds across every future session, unlike a bad line of ordinary code.

Reconcile the two by treating any generated draft as **raw material that must pass
the same review + lint gate a hand-authored file would**:

1. **Inspect, don't assume** — build/test commands, stack + versions, and
   directory layout are discoverable from manifests, CI config, and `README.md`
   (this is what `/init` already reads; make it explicit). Also fold in any
   existing `.cursorrules`, `AGENTS.md`, or `.github/copilot-instructions.md`.
2. **Ask the user, don't infer** — repository etiquette (branch/commit/PR
   conventions), deliberate boundaries ("never touch X", "ask before Y"), and
   whether smaller/non-frontier models will run against this file (it changes the
   instruction budget).
3. **Draft from the template** in
   [`references/templates.md`](references/templates.md), using the copyable
   starters in [`assets/`](assets/). Keep only what survives the "can the agent
   infer this?" filter.
4. **Lint the draft before calling it done** — this is the mechanism that
   resolves the tension: a generated draft that passes the same gate has already
   had its generic and vague content flagged out.

Full workflow, including exactly what to inspect/ask/infer, is in
[`references/workflows.md`](references/workflows.md#create-from-scratch).

## Structure & templates

Section order and the include/exclude line for a root file, how a nested file
differs, and the ready-to-paste "✅ Always / ⚠️ Ask first / 🚫 Never" boundaries
block are all in [`references/templates.md`](references/templates.md). Copyable
skeletons: [`assets/root-CLAUDE.md`](assets/root-CLAUDE.md) and
[`assets/nested-CLAUDE.md`](assets/nested-CLAUDE.md).

## Anti-patterns

Ten common failure modes with their fixes (treating the file as enforced config;
unowned append-only growth; stuffing everything in "just in case"; using it as a
linter; `@import`-as-lazy-loading; secrets; cross-file duplication; auto-generate-
and-forget; assuming precedence is identical across tools) are tabulated in
[`references/workflows.md`](references/workflows.md#anti-patterns). Recognize these
proactively when reviewing a file, not only when asked.
