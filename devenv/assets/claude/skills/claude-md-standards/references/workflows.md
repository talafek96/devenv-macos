# Workflows: edit/refactor, create-from-scratch, anti-patterns

## Edit/refactor

Take a bloated or stale file to compliance. Each step is gated on a concrete
trigger, not done reflexively.

### 1. Measure first
Run the linter (`scripts/lint_claude_md.py`, `--opinionated`) to get numbers:
total lines, estimated instruction count, and every `error` finding. **Fix all
`error`s before any structural work** — secrets, broken imports, and dangerous
example commands are not architecture decisions, they're bugs.

### 2. Decide split vs. trim — by *why* it's oversized, not just its size

| Why it's oversized | Fix | Trigger |
|--------------------|-----|---------|
| Generic / inferable content (exclude-column violations) | **Delete.** Highest leverage — cuts lines *and* instruction count with zero information loss. | The line tells the model something it already knows or can read from code. |
| Necessary but **directory-specific** detail | **Move to a nested `CLAUDE.md`** in that directory (loads on demand). | Relevant to < 100% of sessions and maps cleanly to one directory. |
| Necessary, **cross-cutting**, topic-coherent detail | **Move to `.claude/rules/<topic>.md` with a `paths:` glob.** | Applies across several directories by file type, not one subtree (e.g. a C-only style policy across `src/**`). |
| Deep **reference** material rarely needed in full | **Move to a docs file; leave a one-line pointer** (progressive disclosure). | Occasionally valuable, but most sessions don't need it in context. |

### 3. The `@import` trap
`@import` (`@path/to/file.md`) **still loads the imported file into context at
launch** — Anthropic's docs are explicit. It organizes *source text* for human
maintainability; it does **not** reduce what the model loads. Only **nested
CLAUDE.md** and **path-scoped `.claude/rules/`** are genuinely lazy. So:

- Want the root file *shorter to read/maintain* but same context cost? → `@import`.
- Want to *reduce what loads* into a given session? → nested file or `paths:` rule.

Conflating these is a documented practitioner mistake. Don't reach for `@import`
to solve a context-budget problem.

### 4. Dedupe across the hierarchy
Before finalizing, remove anything a child file restates from an ancestor
(the `content/duplicate-ancestor` lint rule catches the long ones). Inheritance
is automatic — root→cwd concatenation — so a child never needs to repeat the root.

### 5. Re-measure
Re-lint. Confirm you reduced line/instruction/error counts. A "split" that just
redistributes the same bulk into more files hasn't fixed anything — the whole
point is *less loaded*, not *more files*.

### 6. Freshness pass (human judgment — no tool does this)
For each inline snippet or exact command, check it against the current repo.
Convert inline code that could drift into a `file:line` pointer. There is no
numeric staleness threshold in any source; this is where human review is required.

### 7. Assign an owner
Process, not content, but the most-cited fix for the "unowned file that only
grows" failure: give CLAUDE.md an owner and review changes to it like code.

---

## Create-from-scratch

**There is a genuine, unresolved disagreement in the field. Present both paths;
do not silently pick one.**

- **Path A — Anthropic's documented default:** run `/init`, then edit. `/init`
  inspects manifests, docs, config, and code structure, and folds in existing
  `.cursorrules` / `.windsurfrules` / `AGENTS.md`. Anthropic's framing: "a
  starting point, not a finished product." Post-`/init`: review for accuracy, add
  what it couldn't infer (workflow, boundaries), delete generic guidance, commit.
- **Path B — the hand-author camp (HumanLayer):** *don't* auto-generate. Rationale:
  CLAUDE.md is "the highest leverage point of the harness" — a bad line compounds
  across every future session, unlike a bad line of ordinary code. Auto-generated
  files also tend never to get the careful review they need ("the AI already
  wrote it").

**Reconciliation this skill uses:** offer generation as a fast first draft, but
gate it behind the same review + lint pass a hand-authored file must pass. A
generated draft that survives the lint gate has already had its generic/vague
content flagged out — which is exactly Path B's concern, enforced mechanically.

Concretely:

1. **Inspect, don't assume:** build/test manifests (`package.json`, `pyproject.toml`,
   `CMakeLists.txt`, `Makefile`, CI config), `README.md`, and other tools' configs
   (`.cursorrules`, `AGENTS.md`, `.github/copilot-instructions.md`).
2. **Infer, don't ask:** build/test commands (from CI/build scripts), stack +
   versions (from manifests), directory structure (by listing).
3. **Ask the user, don't infer:**
   - Repository etiquette (branch naming, commit format, review/PR process) —
     `/init` characteristically misses this.
   - Deliberate boundaries ("never touch X", "always ask before Y") — a judgment
     call about risk, not inferable from code.
   - Whether smaller/non-frontier models will run against this file — it changes
     the instruction-count budget materially.
4. **Draft from the template** (`references/templates.md` + `assets/`), keeping
   only content that survives the "can the agent infer this?" filter.
5. **Lint the draft before presenting it as final.** This is the gate that
   resolves the A-vs-B tension.

---

## Anti-patterns

Recognize these proactively when reviewing any file.

| # | Anti-pattern | Fix |
|---|--------------|-----|
| 1 | **Treating CLAUDE.md as enforced config** — assuming "always run tests before commit" is obeyed mechanically. | It's context, not enforcement. For guarantees use a `PreToolUse`/`Stop` hook or CI check, not prose. |
| 2 | **Unowned, append-only growth** — everyone adds, nobody removes. | Assign an owner; review edits like code; re-lint against real usage periodically. |
| 3 | **Stuffing everything in "just in case."** | "Universally applicable only" filter: relevant to < 100% of sessions → path-scoped rule or nested file, not the root. |
| 4 | **Vague, unverifiable instructions** ("follow best practices", "write clean code"). | Replace with a checkable instruction + one concrete example. |
| 5 | **Using CLAUDE.md as a linter** — pasting full style rulebooks. | Use a real formatter/linter via a Stop hook; keep only the few *non-default* conventions a tool can't express. |
| 6 | **Confusing `@import` with lazy loading.** | `@import` loads at launch (organizes source text only). Use nested files / `paths:`-scoped rules to actually reduce what loads. |
| 7 | **Duplicating a rule across parent and child files.** | Delete the child copy; rely on root→leaf inheritance (concatenation, not override). |
| 8 | **Pasting secrets "temporarily."** | Never — the file is versioned *and* re-sent to a model every session. Env vars / secret managers, referenced by name. |
| 9 | **Auto-generate and never revisit** — `/init` once, treat as done. | Treat any generated draft as a lint-checked, human-reviewed first draft, never final. |
| 10 | **Assuming precedence is identical across tools** — "closest file always wins." | Claude Code concatenates root→cwd; AGENTS.md draft has a named precedence chain; Copilot's formats are additive. Check the specific tool's docs; make multi-tool precedence explicit. |

### Sources
Anthropic memory + best-practices docs and the "using CLAUDE.md files" / "steering
Claude Code" blog posts; HumanLayer "Writing a good CLAUDE.md"; GitHub's
2,500-repo analysis; cclint / agnix / agents-md-kit rule catalogs;
citypaul/.dotfiles SPLIT-CLAUDE-MD-PLAN.md. Full URLs in `lint-checklist.md`.
