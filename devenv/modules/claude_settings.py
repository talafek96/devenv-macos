"""Managed keys in ~/.claude/settings.json (Claude Code preferences).

Claude Code owns ``~/.claude/settings.json`` and rewrites it constantly (the app
edits it in place as you toggle things), so this module does NOT symlink or own
the whole file — that would clobber machine-local keys like the statusline path,
plugins, or voice settings. Instead it merges a small set of *managed keys* into
whatever is already there, leaving every other key untouched.

Idempotent: on re-run it only writes when a managed key is missing or differs.
Malformed/unreadable JSON is left alone (a warning, never a clobber).

To change what's enforced, edit ``MANAGED_SETTINGS`` below.
"""

from __future__ import annotations

import json

from devenv.modules import Module

# Where Claude Code stores user-scoped settings.
SETTINGS_PATH = ".claude/settings.json"

# The keys devenv enforces. Everything else in the file is left as-is.
MANAGED_SETTINGS: dict[str, object] = {
    "outputStyle": "Concise",       # concise responses (see /config output style)
    "autoMemoryEnabled": False,     # don't auto-save fact files to ~/.claude/.../memory
    "cleanupPeriodDays": 36500,     # ~never delete old sessions (default is 30 days)
}


class ClaudeSettingsModule(Module):
    name = "claude-settings"
    description = "Enforce managed keys in ~/.claude/settings.json (merges, never clobbers)"
    order = 36  # after claude assets (35)

    def run(self, ctx) -> None:
        path = ctx.home_dir / SETTINGS_PATH

        current: dict = {}
        if path.exists():
            try:
                current = json.loads(path.read_text())
            except (json.JSONDecodeError, OSError) as exc:
                ctx.warn(f"Can't read {path} ({exc}) — leaving it untouched")
                return
            if not isinstance(current, dict):
                ctx.warn(f"{path} is not a JSON object — leaving it untouched")
                return

        changed = {k: v for k, v in MANAGED_SETTINGS.items() if current.get(k) != v}
        if not changed:
            ctx.ok(f"Claude settings already current ({len(MANAGED_SETTINGS)} managed keys)")
            return

        current.update(MANAGED_SETTINGS)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(current, indent=2) + "\n")
        summary = ", ".join(f"{k}={v!r}" for k, v in changed.items())
        ctx.ok(f"Claude settings updated: {summary}")
