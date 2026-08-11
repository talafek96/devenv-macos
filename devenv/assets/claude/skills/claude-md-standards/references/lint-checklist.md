# Lint checklist — full rule catalog

The authoritative reference behind `scripts/lint_claude_md.py`. Each rule lists
what it checks, the threshold/heuristic, severity, confidence tier, and source.
Read this when you need to **explain** a finding, **justify** ignoring one, or
**tune** which rules run. Confidence tiers:

- **[hard]** — mechanically enforced by a shipped tool or documented behavior;
  low false-positive; always on (`error`/`warning`).
- **[strong]** — official vendor doc, or 2+ independent primary sources agree;
  on by default, thresholds configurable, disable the tier with `--no-strong`.
- **[opinionated]** — one credible source or genuinely unsolved; **off unless
  `--opinionated`**; present as a suggestion, never a hard rule.

## Table of contents
- Size / budget (rules 1–2)
- Structural (3–6)
- Content quality (7–13)
- Security (14–15)
- Cross-cutting / links (16–19)

---

## Size / budget

**1. File size ceiling** — `size/lines`, `size/bytes`.
What: total lines and bytes in one file. Thresholds observed in the wild, from
strict to loose: `cclint` default **10,000 chars**; Anthropic **"under 200
lines"**; HumanLayer **"< 300, shorter is better"** (their prod root file < 60);
AGENTS.md draft **"under 500"**; OpenAI Codex **hard 32 KiB cap** (files past it
are silently skipped). Skill default: **warn > 200 lines, error > 500 lines, warn
> 32 KiB.** All configurable (`--max-lines`, `--error-lines`, `--max-bytes`).
Severity: warning (lines), warning (bytes). Tier: **[strong]** for lines,
**[hard]** for the byte cap.
Sources: code.claude.com/docs/en/memory; claude.com/blog/steering-claude-code…;
humanlayer.dev/blog/writing-a-good-claude-md; github.com/agentsmd/agents.md
issue #135; developers.openai.com/codex/guides/agents-md;
github.com/felixgeelhaar/cclint.

**2. Instruction-count budget** — `size/instruction-count`.
What: estimated count of discrete imperative directives (bullets starting with
always/never/use/run/must/…), not just lines — a dense list can blow the budget
under 200 lines. Heuristic threshold: **> 150** (frontier thinking models track
~150–200 reliably; smaller models decay exponentially sooner; the tool's own
system prompt already consumes ~50). Severity: info. Tier: **[opinionated]** (one
quantified source). Source: humanlayer.dev/blog/writing-a-good-claude-md.

## Structural

**3. Required sections** — *not implemented as a hard rule on purpose.* `cclint`
originally required "Project Overview / Development Commands / Architecture" and
its own authors walked it back toward flexibility in v0.5.0; AGENTS.md explicitly
rejects required fields. Treat a recommended section *order* (see
`templates.md`) as guidance, not a lint error. Tier: **[hard→relaxed]**.
Sources: github.com/felixgeelhaar/cclint; agents.md.

**4. Heading hierarchy** — `structure/heading-skip`. What: ATX headings must not
skip a level (h1→h3). Severity: warning. Tier: **[hard]**. Source: cclint.

**5. Markdown hygiene** — `md/header-space`, `md/trailing-ws`, `md/blank-run`,
`md/fence-lang`, `md/final-newline`. What: space after `#`; no trailing
whitespace; ≤ 2 consecutive blank lines; fenced blocks carry a language tag; file
ends with a newline. Severity: warning (auto-fixable). Tier: **[hard]**. Source:
cclint.

**6. Cross-file duplicate content** — `content/duplicate-ancestor`. What: a long
(≥ 40-char) prose line in a nested CLAUDE.md that already appears in an ancestor
CLAUDE.md. Rely on inheritance (root-to-cwd concatenation) and delete the child
copy. Only fires in directory-scan mode. Severity: warning. Tier: **[strong]** (a
real linter rule + the AGENTS.md "implicit inheritance" principle agree). Sources:
cclint; agents.md issue #135.

## Content quality

**7. Vague / unverifiable instructions** — `content/vague`. What: pattern-match
for "follow best practices", "write clean code", "be helpful", "format properly",
"where appropriate", etc. — directives with no checkable criterion. Severity:
warning. Tier: **[strong]** (4 independent sources: cclint, agnix, Anthropic's
exclude column, AGENTS.md draft). Fix: replace with a concrete rule + one example.
Sources: cclint; github.com/agent-sh/agnix; code.claude.com/docs/en/best-practices;
agents.md issue #135.

**8. Hedging language** — `content/hedging`. What: "try to", "if possible", "when
you can", "ideally you should" — weakens directives meant to be literal. Severity:
info. Tier: **[opinionated]** (single tool). Source: cclint.

**9. Filler / politeness** — `content/filler`. What: "please", "thank you", "you
are a helpful assistant", "kindly" — tokens with no instructional signal.
Severity: info. Tier: **[opinionated]**. Source: cclint.

**10. Show, don't tell** — folded into rule 12 (large-inline-code) and the
templates guidance rather than a standalone check. Principle: one real snippet
beats three paragraphs (GitHub's 2,500-repo analysis + cclint agree). Tier:
**[strong]**. Source:
github.blog/…/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories.

**11. Content placement** — partially covered by rules 1 & 12; the semantic part
("this belongs in README / linked docs, not inline") needs your judgment. Flag
detailed API docs, standard language idioms, and file-by-file descriptions —
link, don't inline. Tier: **[strong]**. Sources:
code.claude.com/docs/en/best-practices; cclint.

**12. Large inline code / staleness proxy** — `content/large-code`. What: a fenced
code block longer than **20 lines** (`--code-block-lines`). If it mirrors real
source it will drift; prefer a `file:line` pointer. Severity: info. Tier:
**[strong]** for the "show don't tell / link don't copy" principle. True staleness
detection (does this snippet still match the source?) is **unsolved by any tool**
— it needs human judgment; the script only flags the proxy. Sources: cclint;
humanlayer.dev/blog/writing-a-good-claude-md ("prefer pointers to copies").

**13. Import de-duplication** — `import/duplicate` (see rule 16). Duplicate
`@path` imports within a file. Severity: warning. Tier: **[hard]**. Source: cclint.

## Security

**14. Secret / credential detection** — `security/secret`, `security/secret-assign`.
What: provider-key shapes (OpenAI `sk-…`/`sk-proj-…`, Anthropic `sk-ant-…`, GitHub
`ghp_/gho_/ghs_/ghu_/github_pat_…`, AWS `AKIA…`, Google `AIza…`, Slack `xox[baprs]-…`,
PEM private-key blocks) and high-entropy `KEY=/TOKEN=/SECRET=/PASSWORD=`
assignments. Scans **both prose and code blocks**. Masks matches in output (first
4 chars). Ignores placeholders (`sk-xxxx`, `your-api-key`, `<…>`, `${…}`, repeated
chars, `*_HERE`). Severity: **error**. Tier: **[hard]**. Rationale: CLAUDE.md is
versioned *and* re-transmitted to a model every session — a strictly worse
exposure surface than ordinary source. **Highest-value rule in the set.** Source:
cclint.

**15. Dangerous example commands** — `security/dangerous-cmd`. What: inside shell
code fences, `rm -rf /` (and `~`/glob/`$var` targets), `curl|bash` / `wget|sh`,
fork bombs, `chmod -R 777 /`, `mkfs`/`dd` on raw devices, redirect onto a raw
disk. A command in a code block reads as a *sanctioned example* to an agent.
Severity: **error**. Tier: **[hard]**. Source: cclint.

## Cross-cutting / links

**16. `@import` validation** — `import/unresolved`, `import/cycle`,
`import/too-deep`, `import/duplicate`. What: every `@path` must resolve to a real
file; detect circular chains (A→B→A) and enforce **max recursion depth**.
Anthropic's current docs say **4 hops**; `cclint` enforces **5** — a live
documentation drift. Default `--import-depth 4`; adjust to whatever the installed
Claude Code version actually enforces. The linter recurses into imported files so
a break three hops down is still caught. Severity: error (unresolved/cycle/too-deep),
warning (duplicate). Tier: **[hard]** (depth number uncertain). Sources:
code.claude.com/docs/en/memory; cclint; github.com/citypaul/.dotfiles
SPLIT-CLAUDE-MD-PLAN.md.

**17. Ordinary Markdown link resolution** — *not implemented* (no CLAUDE.md-specific
tool does it; it's a generic `markdownlint` concern). Add `markdownlint` separately
if you want relative-link checking. Tier: **[opinionated addition]**.

**18. Naming / location** — `naming/filename`, `naming/local-deprecated`. What:
filename should be `CLAUDE.md` / `AGENTS.md` (case-sensitive); `CLAUDE.local.md`
is deprecated (use an `@import` of a git-ignored file instead). Severity: info /
warning. Tier: **[hard]** for filename, **[strong]** for the local-file deprecation.
Source: cclint.

**19. `.claude/rules/` frontmatter scoping** — `rules/unscoped`. What: a rule file
under `.claude/rules/` with **no `paths:` frontmatter** loads in *every* session.
Topic/language/directory-specific rules should carry a `paths:` glob so they load
only when relevant. Severity: warning. Tier: **[strong]** — straight from
Anthropic's documented mechanism; **not yet automated by any surveyed linter**, so
this skill fills a genuine gap. Sources: code.claude.com/docs/en/memory;
claude.com/blog/steering-claude-code….

---

## Reference implementations (prior art this catalog is distilled from)

- **cclint** — github.com/felixgeelhaar/cclint. TypeScript CLI/LSP/MCP/GitHub
  Action for CLAUDE.md; richest single rule catalog; the primary template.
- **agnix** — github.com/agent-sh/agnix. Rust CLI+LSP, 432 rules across
  CLAUDE.md/SKILL.md/hooks/MCP/Cursor/Copilot/Kiro (53 for Claude Code alone).
- **agents-md-kit** — github.com/reaatech/agents-md-kit. npm parser + Zod schema
  validator + 18-rule linter + scaffolder + reporter for AGENTS.md.
- **GitHub blog, 2,500-repo analysis** — github.blog/…/how-to-write-a-great-agents-md.
  Empirical "what correlates with a good file"; highest-confidence content source.
- **HumanLayer, "Writing a good CLAUDE.md"** — humanlayer.dev/blog/writing-a-good-claude-md.
  Quantified instruction-budget claims; contrarian `/init` position.
- **Anthropic memory + best-practices docs** — code.claude.com/docs/en/memory,
  /best-practices; claude.com/blog/using-claude-md-files.
