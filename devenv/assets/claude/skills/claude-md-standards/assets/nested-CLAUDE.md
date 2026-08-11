<!--
  Nested (per-directory) CLAUDE.md starter. Place inside the subdirectory it
  governs, e.g. src/infra/lock/CLAUDE.md. It loads ONLY when the agent touches a
  file in this subtree, so it can be denser than the root file.
  RULE: include only what is specific to THIS directory. Do NOT restate project-
  wide conventions — they are inherited from the root file automatically.
-->

# [submodule name]

This file governs `[path/to/this/dir/]` only.

[One or two sentences: what this component is and the one non-obvious thing an
agent must know before editing it.]

## Local conventions & invariants

[Directory-specific rules, gotchas, and invariants that are NOT true elsewhere in
the repo. Example: "Everything reachable from the signal handler must be
async-signal-safe — no malloc/printf/locks." Include a concrete example where it
helps.]

## Adding to this component

[If there's a specific procedure for extending this module — a list to append to,
a test to register — state it step by step.]
