#!/usr/bin/env python3
"""Lint a CLAUDE.md / AGENTS.md file (or a whole repo) against the community
best-practice checklist bundled with the `claude-md` skill.

Why a script and not just a prompt: the mechanical rules here (secret shapes,
dangerous-command patterns, import resolution, Markdown hygiene, size budgets)
are deterministic and easy to get subtly wrong by eye. Running them once, the
same way every time, frees the model to spend its judgment on the parts that
genuinely need it (is this instruction actually vague? is this content stale?).

Rule tiers mirror the skill's confidence flags:
  [hard]        mechanical, low false-positive, always on.
  [strong]      multi-source consensus; on by default, thresholds configurable,
                the whole tier can be turned off with --no-strong.
  [opinionated] one credible source / unsolved; OFF unless --opinionated.

Exit codes: 0 = clean (no failing findings), 1 = at least one failing finding,
2 = usage error. By default only `error` findings fail the run; --strict makes
`warning` fail too. `info` never fails.

Python 3.8+ (no third-party deps).
"""

import argparse
import json
import os
import re
import sys
from collections import namedtuple

Finding = namedtuple("Finding", ["path", "line", "severity", "rule", "tier", "message"])

ERROR, WARNING, INFO = "error", "warning", "info"
HARD, STRONG, OPINIONATED = "hard", "strong", "opinionated"

# --------------------------------------------------------------------------- #
# Small parsing helpers
# --------------------------------------------------------------------------- #

FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")


def split_frontmatter(text):
    """Return (frontmatter_dict_lines, body_text, body_start_lineno).

    Only recognizes YAML-style frontmatter delimited by leading '---'. We do
    not parse YAML fully (no dep); we just capture the raw lines so callers can
    look for specific keys such as `paths:`.
    """
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() in ("---", "..."):
                return lines[1:i], "\n".join(lines[i + 1:]), i + 2
    return [], text, 1


def iter_code_blocks(text):
    """Yield (lang, start_lineno, end_lineno, [content_lines]) for fenced blocks.

    Line numbers are 1-based and refer to the fence lines themselves.
    """
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = FENCE_RE.match(lines[i])
        if m:
            fence = m.group(2)[0]
            lang = m.group(3).strip().split()[0].lower() if m.group(3).strip() else ""
            start = i
            body = []
            i += 1
            while i < len(lines):
                m2 = FENCE_RE.match(lines[i])
                if m2 and m2.group(2)[0] == fence:
                    yield (lang, start + 1, i + 1, body)
                    break
                body.append(lines[i])
                i += 1
            else:
                # Unterminated fence; treat rest of file as its body.
                yield (lang, start + 1, len(lines), body)
        i += 1


def code_line_ranges(text):
    """Set of 1-based line numbers that fall inside a fenced code block
    (including the fence lines). Used to skip prose-only checks."""
    inside = set()
    for _lang, start, end, _body in iter_code_blocks(text):
        for ln in range(start, end + 1):
            inside.add(ln)
    return inside


# --------------------------------------------------------------------------- #
# Rules
# --------------------------------------------------------------------------- #

def rule_size(path, text, cfg, out):
    """[strong] File-size budget in lines, plus [hard] the Codex 32 KiB hard cap
    on bytes (files past it are silently dropped by some tools)."""
    n_lines = len(text.splitlines())
    if n_lines > cfg.error_lines:
        out.append(Finding(path, 1, ERROR, "size/lines", STRONG,
                           "%d lines exceeds the hard ceiling of %d; split into "
                           ".claude/rules/ or nested CLAUDE.md files."
                           % (n_lines, cfg.error_lines)))
    elif n_lines > cfg.max_lines:
        out.append(Finding(path, 1, WARNING, "size/lines", STRONG,
                           "%d lines is over the ~%d-line target; trim generic "
                           "content or move detail to scoped files."
                           % (n_lines, cfg.max_lines)))
    n_bytes = len(text.encode("utf-8"))
    if n_bytes > cfg.max_bytes:
        out.append(Finding(path, 1, WARNING, "size/bytes", HARD,
                           "%d bytes exceeds %d (OpenAI Codex silently skips "
                           "instruction files past this cap)." % (n_bytes, cfg.max_bytes)))


IMPERATIVE_BULLET_RE = re.compile(
    r"^\s*[-*+]\s+(?:always |never |do not |don't |must |use |run |prefer |avoid "
    r"|ensure |make sure|check |validate |set |call |return |panic |keep )",
    re.IGNORECASE,
)


def rule_instruction_count(path, text, cfg, out):
    """[opinionated] Estimate discrete directives. Frontier models track ~150-200
    reliably; the tool's own system prompt already spends ~50 before this file
    loads. A dense list can blow the budget well under the line ceiling."""
    codelines = code_line_ranges(text)
    count = 0
    for i, line in enumerate(text.splitlines(), start=1):
        if i in codelines:
            continue
        if IMPERATIVE_BULLET_RE.match(line):
            count += 1
    if count > cfg.instruction_budget:
        out.append(Finding(path, 1, INFO, "size/instruction-count", OPINIONATED,
                           "~%d imperative directives detected (> %d). Instruction "
                           "adherence decays as this grows; consider consolidating."
                           % (count, cfg.instruction_budget)))


def rule_heading_hierarchy(path, text, cfg, out):
    """[hard] ATX headings should not skip a level (h1 -> h3)."""
    codelines = code_line_ranges(text)
    prev = 0
    for i, line in enumerate(text.splitlines(), start=1):
        if i in codelines:
            continue
        m = re.match(r"^(#{1,6})\s", line)
        if not m:
            continue
        level = len(m.group(1))
        if prev and level > prev + 1:
            out.append(Finding(path, i, WARNING, "structure/heading-skip", HARD,
                               "heading jumps from h%d to h%d (skips a level)."
                               % (prev, level)))
        prev = level


def rule_markdown_hygiene(path, text, cfg, out):
    """[hard] Header spacing, trailing whitespace, blank-line runs, fenced blocks
    missing a language tag, and a missing final newline."""
    lines = text.splitlines()
    codelines = code_line_ranges(text)
    blank_run = 0
    for i, line in enumerate(lines, start=1):
        if i not in codelines:
            if re.match(r"^#{1,6}[^#\s]", line):
                out.append(Finding(path, i, WARNING, "md/header-space", HARD,
                                   "missing space after '#' in header."))
        if line != line.rstrip():
            out.append(Finding(path, i, WARNING, "md/trailing-ws", HARD,
                               "trailing whitespace."))
        if line.strip() == "":
            blank_run += 1
            if blank_run == 3:
                out.append(Finding(path, i, WARNING, "md/blank-run", HARD,
                                   "more than 2 consecutive blank lines."))
        else:
            blank_run = 0
    for lang, start, _end, _body in iter_code_blocks(text):
        if not lang:
            out.append(Finding(path, start, WARNING, "md/fence-lang", HARD,
                               "fenced code block has no language tag."))
    if text and not text.endswith("\n"):
        out.append(Finding(path, len(lines), WARNING, "md/final-newline", HARD,
                           "file does not end with a newline."))


def rule_large_inline_code(path, text, cfg, out):
    """[strong] A long inline code block often duplicates real source, which
    drifts. Prefer a file:line pointer over pasting the code."""
    for _lang, start, _end, body in iter_code_blocks(text):
        if len(body) > cfg.code_block_lines:
            out.append(Finding(path, start, INFO, "content/large-code", STRONG,
                               "code block of %d lines; if it mirrors real source, "
                               "link to it (file:line) instead of inlining a copy "
                               "that can drift." % len(body)))


VAGUE_PATTERNS = [
    r"\bfollow (?:all )?best practices\b",
    r"\bwrite clean code\b",
    r"\bwrite good code\b",
    r"\bbe helpful\b",
    r"\bbe helpful and accurate\b",
    r"\bbe a helpful assistant\b",
    r"\bformat (?:it |the code )?properly\b",
    r"\buse proper (?:formatting|style)\b",
    r"\bhandle errors appropriately\b",
    r"\bas (?:you see |deemed )?appropriate\b",
    r"\bwhere appropriate\b",
    r"\bhigh[- ]quality code\b",
    r"\bmake it (?:nice|good|clean)\b",
]
VAGUE_RE = re.compile("|".join(VAGUE_PATTERNS), re.IGNORECASE)


def rule_vague(path, text, cfg, out):
    """[strong] Unverifiable directives waste budget: the model already knows
    them, or cannot check them. Replace with a concrete, checkable instruction
    plus one example."""
    codelines = code_line_ranges(text)
    for i, line in enumerate(text.splitlines(), start=1):
        if i in codelines:
            continue
        for m in VAGUE_RE.finditer(line):
            out.append(Finding(path, i, WARNING, "content/vague", STRONG,
                               "vague/unverifiable instruction: %r. Replace with a "
                               "checkable rule + a concrete example." % m.group(0)))


HEDGE_RE = re.compile(r"\b(?:try to|if possible|when you can|ideally you should)\b",
                      re.IGNORECASE)
FILLER_RE = re.compile(r"\b(?:please|thank you|thanks|you are a helpful assistant|"
                       r"kindly)\b", re.IGNORECASE)


def rule_hedging(path, text, cfg, out):
    """[opinionated] Hedges weaken directives the model is meant to treat as literal."""
    codelines = code_line_ranges(text)
    for i, line in enumerate(text.splitlines(), start=1):
        if i in codelines:
            continue
        m = HEDGE_RE.search(line)
        if m:
            out.append(Finding(path, i, INFO, "content/hedging", OPINIONATED,
                               "hedging language %r reduces reliability; state the "
                               "rule directly." % m.group(0)))


def rule_filler(path, text, cfg, out):
    """[opinionated] Politeness/persona filler spends tokens with no instructional
    signal."""
    codelines = code_line_ranges(text)
    for i, line in enumerate(text.splitlines(), start=1):
        if i in codelines:
            continue
        m = FILLER_RE.search(line)
        if m:
            out.append(Finding(path, i, INFO, "content/filler", OPINIONATED,
                               "filler %r carries no instruction; remove it." % m.group(0)))


# --- security -------------------------------------------------------------- #

def _mask(s):
    s = s.strip().strip("'\"")
    return s[:4] + "…" if len(s) > 4 else s


SECRET_PATTERNS = [
    ("openai-key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{20,}\b")),
    ("anthropic-key", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}\b")),
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("google-key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b")),
    ("pem-private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
]
# Match an identifier that *contains* a secret-ish word, even when it is glued
# into a larger name by underscores/dashes (AWS_SECRET_ACCESS_KEY, MY_API_KEY,
# DB_PASSWORD). A plain \bSECRET\b misses these because '_' is a word char.
ASSIGN_SECRET_RE = re.compile(
    r"(?<![A-Za-z0-9])[A-Za-z0-9_\-]*"
    r"(?:API[_-]?KEY|APIKEY|SECRET|TOKEN|PASSWORD|PASSWD|PWD|ACCESS[_-]?KEY)"
    r"[A-Za-z0-9_\-]*"
    r"\s*[:=]\s*['\"]?(?P<val>[A-Za-z0-9/+_\-\.]{16,})['\"]?",
    re.IGNORECASE,
)
PLACEHOLDER_RE = re.compile(
    r"^(?:x{3,}|your[_-]|example|changeme|placeholder|<[^>]+>|\$\{|\.\.\.|"
    r"[A-Z][A-Z0-9_]*_HERE|abc123|foobar|test|dummy|redacted)", re.IGNORECASE)


def _is_placeholder(val):
    v = val.strip().strip("'\"")
    if PLACEHOLDER_RE.match(v):
        return True
    if len(set(v.replace("-", "").replace("_", ""))) <= 2:  # e.g. "xxxxxxxx"
        return True
    return False


def rule_secrets(path, text, cfg, out):
    """[hard] Credentials in a versioned, per-session-transmitted file are worse
    than in ordinary source. Scans prose AND code blocks."""
    for i, line in enumerate(text.splitlines(), start=1):
        for name, rx in SECRET_PATTERNS:
            for m in rx.finditer(line):
                if _is_placeholder(m.group(0)):
                    continue
                out.append(Finding(path, i, ERROR, "security/secret", HARD,
                                   "possible %s (%s). Never commit secrets to an "
                                   "instruction file; reference by name only."
                                   % (name, _mask(m.group(0)))))
        for m in ASSIGN_SECRET_RE.finditer(line):
            val = m.group("val")
            if _is_placeholder(val):
                continue
            out.append(Finding(path, i, ERROR, "security/secret-assign", HARD,
                               "hard-coded credential assignment (%s). Use an env "
                               "var / secret manager, referenced by name."
                               % _mask(val)))


DANGEROUS_PATTERNS = [
    (re.compile(r"\brm\s+-rf?\s+(?:-[a-z]+\s+)*(?:/|~|\$\w+|/\*|\*)(?:\s|$)"),
     "destructive 'rm -rf' against a root/home/glob target"),
    (re.compile(r"\b(?:curl|wget)\b[^\n|]*\|\s*(?:sudo\s+)?(?:ba)?sh\b"),
     "piping a network download straight into a shell (curl|bash)"),
    (re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:"), "fork bomb"),
    (re.compile(r"\bchmod\s+-R\s+777\s+/"), "recursive chmod 777 on an absolute path"),
    (re.compile(r"\bmkfs\.\w+\s+/dev/"), "filesystem creation on a raw device"),
    (re.compile(r"\bdd\b[^\n]*\bof=/dev/(?:sd|nvme|hd)"), "dd writing to a raw disk device"),
    (re.compile(r">\s*/dev/(?:sd|nvme|hd)\w+"), "redirect onto a raw disk device"),
]


def rule_dangerous_commands(path, text, cfg, out):
    """[hard] A command in a code block reads as a sanctioned example to an agent.
    A destructive one there is a live footgun, not documentation. Scans shell
    code blocks (and any code block, to be safe)."""
    for lang, _start, _end, body in iter_code_blocks(text):
        if lang and lang not in ("sh", "bash", "shell", "console", "zsh", "sh-session", ""):
            continue
        # Compute absolute line numbers for the body.
        for offset, cl in enumerate(body):
            for rx, desc in DANGEROUS_PATTERNS:
                if rx.search(cl):
                    # +1 to skip the opening fence line; _start is the fence.
                    out.append(Finding(path, _start + 1 + offset, ERROR,
                                       "security/dangerous-cmd", HARD,
                                       "%s in an example command." % desc))


# --- imports --------------------------------------------------------------- #

IMPORT_RE = re.compile(r"(?:^|\s)@([~./][^\s`]+|[A-Za-z0-9_./\-]+\.md)\b")


def _resolve_import(base_dir, spec):
    if spec.startswith("~/"):
        return os.path.expanduser(spec)
    if spec.startswith("/"):
        return spec
    return os.path.normpath(os.path.join(base_dir, spec))


def rule_imports(path, text, cfg, out, _depth=1, _seen=None):
    """[hard] Every @path must resolve; enforce max recursion depth, detect
    cycles and duplicate imports within a file."""
    if _seen is None:
        _seen = set()
    base_dir = os.path.dirname(os.path.abspath(path))
    codelines = code_line_ranges(text)
    seen_here = set()
    for i, line in enumerate(text.splitlines(), start=1):
        if i in codelines:
            continue
        for m in IMPORT_RE.finditer(line):
            spec = m.group(1)
            if not spec.endswith(".md"):
                continue
            target = _resolve_import(base_dir, spec)
            if spec in seen_here:
                out.append(Finding(path, i, WARNING, "import/duplicate", HARD,
                                   "duplicate import of %s." % spec))
            seen_here.add(spec)
            if _depth > cfg.import_depth:
                out.append(Finding(path, i, ERROR, "import/too-deep", HARD,
                                   "import nesting exceeds max depth %d."
                                   % cfg.import_depth))
                continue
            if target in _seen:
                out.append(Finding(path, i, ERROR, "import/cycle", HARD,
                                   "circular import chain via %s." % spec))
                continue
            if not os.path.isfile(target):
                out.append(Finding(path, i, ERROR, "import/unresolved", HARD,
                                   "import target does not exist: %s." % spec))
                continue
            # Recurse so a broken import three hops down is still reported.
            _seen.add(target)
            try:
                with open(target, "r", encoding="utf-8", errors="replace") as fh:
                    sub = fh.read()
                rule_imports(target, sub, cfg, out, _depth + 1, _seen)
            except OSError:
                pass


def rule_filename(path, text, cfg, out):
    """[hard]/[opinionated] Filename/location sanity."""
    base = os.path.basename(path)
    if base not in ("CLAUDE.md", "AGENTS.md") and not (
            os.sep + ".claude" + os.sep + "rules" + os.sep in os.path.abspath(path)):
        out.append(Finding(path, 1, INFO, "naming/filename", HARD,
                           "'%s' is not a recognized agent-instruction filename "
                           "(CLAUDE.md / AGENTS.md)." % base))
    if base == "CLAUDE.local.md":
        out.append(Finding(path, 1, WARNING, "naming/local-deprecated", STRONG,
                           "CLAUDE.local.md is deprecated; use an @import of an "
                           "un-tracked file instead."))


def rule_rules_frontmatter(path, text, cfg, out):
    """[strong] A .claude/rules/*.md file with no `paths:` frontmatter is loaded
    into *every* session. Topic-specific rule files should be path-scoped so they
    only load when relevant."""
    ap = os.path.abspath(path)
    if (os.sep + ".claude" + os.sep + "rules" + os.sep) not in ap:
        return
    fm, _body, _start = split_frontmatter(text)
    has_paths = any(re.match(r"\s*paths\s*:", ln) for ln in fm)
    if not has_paths:
        out.append(Finding(path, 1, WARNING, "rules/unscoped", STRONG,
                           "rule file has no `paths:` frontmatter, so it loads in "
                           "every session (even unrelated ones). Add a `paths:` "
                           "glob if this rule is topic/language/directory-specific."))


# --------------------------------------------------------------------------- #
# Cross-file: duplicate content between ancestor and descendant files
# --------------------------------------------------------------------------- #

def _significant_lines(text):
    codelines = code_line_ranges(text)
    sig = {}
    for i, line in enumerate(text.splitlines(), start=1):
        if i in codelines:
            continue
        s = line.strip()
        if len(s) >= 40 and not s.startswith("#"):
            sig[s] = i
    return sig


def cross_file_dedup(files, out):
    """[strong] Guidance stated in an ancestor need not be restated in a child
    (implicit inheritance). Flag long lines duplicated between a parent CLAUDE.md
    and a nested one."""
    parsed = []
    for p in files:
        if os.path.basename(p) not in ("CLAUDE.md", "AGENTS.md"):
            continue
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as fh:
                parsed.append((p, _significant_lines(fh.read())))
        except OSError:
            continue
    for i in range(len(parsed)):
        for j in range(len(parsed)):
            if i == j:
                continue
            pi, li = parsed[i]
            pj, lj = parsed[j]
            # Only compare ancestor (shorter path / higher in tree) vs descendant.
            if not os.path.abspath(pj).startswith(os.path.dirname(os.path.abspath(pi))):
                continue
            if os.path.dirname(os.path.abspath(pi)) == os.path.dirname(os.path.abspath(pj)):
                continue
            for line, lineno in lj.items():
                if line in li:
                    out.append(Finding(pj, lineno, WARNING, "content/duplicate-ancestor",
                                       STRONG,
                                       "line duplicates guidance already in ancestor "
                                       "%s; rely on inheritance and delete the copy."
                                       % os.path.relpath(pi)))


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #

HARD_RULES = [rule_size, rule_heading_hierarchy, rule_markdown_hygiene,
              rule_secrets, rule_dangerous_commands, rule_imports, rule_filename]
STRONG_RULES = [rule_large_inline_code, rule_vague, rule_rules_frontmatter]
OPINIONATED_RULES = [rule_instruction_count, rule_hedging, rule_filler]


def lint_file(path, cfg):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    out = []
    rules = list(HARD_RULES)
    if not cfg.no_strong:
        rules += STRONG_RULES
    if cfg.opinionated:
        rules += OPINIONATED_RULES
    for rule in rules:
        try:
            rule(path, text, cfg, out)
        except Exception as e:  # a buggy rule must not sink the whole run
            out.append(Finding(path, 1, INFO, "linter/internal", HARD,
                               "rule %s crashed: %s" % (rule.__name__, e)))
    return out


def discover(root):
    """Find agent-instruction files under a directory, without walking huge
    shared mounts: prune common heavy/vendor dirs."""
    prune = {".git", "node_modules", "obj", "build", ".venv", "venv",
             "__pycache__", ".research", "dist", "target"}
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in prune]
        for f in filenames:
            if f in ("CLAUDE.md", "AGENTS.md", "CLAUDE.local.md"):
                found.append(os.path.join(dirpath, f))
            elif (os.sep + ".claude" + os.sep + "rules" + os.sep) in \
                    (os.path.join(dirpath, f) + os.sep) and f.endswith(".md"):
                found.append(os.path.join(dirpath, f))
    return sorted(found)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="A CLAUDE.md/AGENTS.md file, or a directory to scan.")
    ap.add_argument("--max-lines", type=int, default=200,
                    help="warn above this line count (default 200; Anthropic target).")
    ap.add_argument("--error-lines", type=int, default=500,
                    help="error above this line count (default 500; AGENTS.md bound).")
    ap.add_argument("--max-bytes", type=int, default=32 * 1024,
                    help="warn above this byte size (default 32 KiB; Codex cap).")
    ap.add_argument("--import-depth", type=int, default=4,
                    help="max @import recursion depth (default 4).")
    ap.add_argument("--code-block-lines", type=int, default=20,
                    help="flag inline code blocks longer than this (default 20).")
    ap.add_argument("--instruction-budget", type=int, default=150,
                    help="flag when estimated directives exceed this (default 150).")
    ap.add_argument("--opinionated", action="store_true",
                    help="also run opinionated rules (hedging, filler, "
                         "instruction-count).")
    ap.add_argument("--no-strong", action="store_true",
                    help="run only the hard, always-safe rules.")
    ap.add_argument("--strict", action="store_true",
                    help="treat warnings as failures for the exit code.")
    ap.add_argument("--json", action="store_true", help="emit findings as JSON.")
    cfg = ap.parse_args(argv)

    if os.path.isdir(cfg.path):
        files = discover(cfg.path)
        if not files:
            print("No CLAUDE.md/AGENTS.md files found under %s" % cfg.path,
                  file=sys.stderr)
            return 0
    elif os.path.isfile(cfg.path):
        files = [cfg.path]
    else:
        print("No such file or directory: %s" % cfg.path, file=sys.stderr)
        return 2

    all_findings = []
    for f in files:
        all_findings.extend(lint_file(f, cfg))
    if len(files) > 1:
        cross_file_dedup(files, all_findings)

    all_findings.sort(key=lambda x: (x.path, x.line,
                                     {ERROR: 0, WARNING: 1, INFO: 2}[x.severity]))

    if cfg.json:
        print(json.dumps([f._asdict() for f in all_findings], indent=2))
    else:
        _print_human(files, all_findings)

    n_error = sum(1 for f in all_findings if f.severity == ERROR)
    n_warn = sum(1 for f in all_findings if f.severity == WARNING)
    if n_error or (cfg.strict and n_warn):
        return 1
    return 0


SEV_TAG = {ERROR: "ERROR ", WARNING: "WARN  ", INFO: "INFO  "}


def _print_human(files, findings):
    if not findings:
        print("✓ %d file(s) checked, no findings." % len(files))
        return
    cur = None
    for f in findings:
        if f.path != cur:
            cur = f.path
            print("\n%s" % os.path.relpath(f.path))
        print("  %s:%-4d %s [%s/%s] %s"
              % (SEV_TAG[f.severity], f.line, "", f.rule, f.tier, f.message))
    n_e = sum(1 for x in findings if x.severity == ERROR)
    n_w = sum(1 for x in findings if x.severity == WARNING)
    n_i = sum(1 for x in findings if x.severity == INFO)
    print("\n%d error(s), %d warning(s), %d info across %d file(s)."
          % (n_e, n_w, n_i, len(files)))


if __name__ == "__main__":
    sys.exit(main())
