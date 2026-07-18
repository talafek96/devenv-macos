"""macOS keyboard layer: Ghostty App-Support dedupe, macOS defaults, and the
one-time GUI permission checklist that can't be scripted.

The Karabiner keymap, Ghostty config, and zellij config are deployed by the
dotfiles module (symlinks). This module handles the macOS-side pieces around
them and prints what still needs a manual click.
"""

from __future__ import annotations

from devenv.modules import Module

# ── macOS defaults (domain, key, type, value) ───────────────
# Each is a per-user `defaults write`. Several only take full effect after a
# logout/login (noted to the user at the end).
_DEFAULTS = [
    # Globe/fn = its native macOS dual role: a lone TAP cycles input sources
    # (1 = Change Input Source), and HOLDING it is the fn modifier. Both are
    # stock behavior; Karabiner does NOT remap the F-row (fn_function_keys is []
    # in karabiner.json) so macOS owns it. Read at login → effective next login.
    ("com.apple.HIToolbox", "AppleFnUsageType", "-int", "1"),
    # F1-F12 are standard function keys; fn+F-row = hardware (brightness/volume/
    # media/etc.). Required now that Karabiner no longer forces the F-row — macOS
    # must be the one making plain F-keys function keys and fn+F the hardware layer.
    ("NSGlobalDomain", "com.apple.keyboard.fnState", "-bool", "true"),
    # Natural scrolling ON (the known-good baseline for the keymap).
    ("NSGlobalDomain", "com.apple.swipescrolldirection", "-bool", "true"),
    # Key repeat instead of the accent-picker popover (essential for vim/coding).
    ("NSGlobalDomain", "ApplePressAndHoldEnabled", "-bool", "false"),
    # Fast key repeat.
    ("NSGlobalDomain", "KeyRepeat", "-int", "2"),
    ("NSGlobalDomain", "InitialKeyRepeat", "-int", "15"),
]

_GHOSTTY_APP_SUPPORT = "Library/Application Support/com.mitchellh.ghostty/config"

_PERMISSION_CHECKLIST = """\
  Karabiner-Elements (the keymap won't work until all three are done):
    1. Open Karabiner-Elements → approve the driver / system-extension prompt.
    2. System Settings → Privacy & Security → Input Monitoring   → enable Karabiner.
    3. System Settings → Privacy & Security → Accessibility        → enable Karabiner.
  AltTab:
    - Grant Accessibility on first launch.
    - Controls → set the Hold shortcut to Command (so your Alt = Command opens it).
  Rectangle:
    - Grant Accessibility on first launch.
  Maccy (clipboard history):
    - Grant Accessibility if you want it to paste directly.
  Function row: globe/fn is native, so the printed hardware functions work via
  fn+F1..F12 out of the box (brightness, Mission Control, media, volume, Do Not
  Disturb on F6, etc.). For fn+F5 Dictation, enable it once under System
  Settings → Keyboard → Dictation.
"""


class KeybindsModule(Module):
    name = "keybinds"
    description = "macOS defaults, Ghostty App-Support dedupe, and the GUI-permission checklist"
    order = 40

    def run(self, ctx) -> None:
        self._dedupe_ghostty_app_support(ctx)
        self._apply_macos_defaults(ctx)
        self._print_checklist(ctx)

    # Ghostty on macOS loads BOTH ~/.config/ghostty/config AND the App-Support
    # path, then merges them. Symlinking App-Support to the canonical file (as
    # an earlier version of this module did) therefore loads the SAME config
    # twice — harmless for last-wins scalars, but it makes every `config-file`
    # include fire twice and trips Ghostty's cycle detector. So we ensure the
    # App-Support path is absent and let ~/.config be the single source.
    def _dedupe_ghostty_app_support(self, ctx) -> None:
        canonical = ctx.home_dir / ".config/ghostty/config"
        app_support = ctx.home_dir / _GHOSTTY_APP_SUPPORT
        try:
            # Only remove OUR duplicate: a symlink pointing at the canonical
            # file. A real file there is the user's own config — leave it.
            if app_support.is_symlink() and app_support.resolve() == canonical.resolve():
                app_support.unlink()
                ctx.ok("Removed duplicate Ghostty App-Support symlink (was double-loading config)")
            elif app_support.is_symlink() or app_support.exists():
                ctx.info(f"Left existing {app_support} in place (not our symlink)")
            else:
                ctx.ok("Ghostty App-Support config already deduped")
        except OSError as exc:
            ctx.warn(f"Could not dedupe Ghostty App-Support config: {exc}")

    def _apply_macos_defaults(self, ctx) -> None:
        for domain, key, vtype, value in _DEFAULTS:
            ctx.run("defaults", "write", domain, key, vtype, value, check=False)
        ctx.ok("Applied macOS defaults (globe tap=Change Input Source, fn+F-row=hardware, natural scroll, key repeat)")
        ctx.info("Some of these take effect after the next logout/login.")

    def _print_checklist(self, ctx) -> None:
        ctx.header("Manual, one-time GUI permissions (cannot be scripted)")
        print(_PERMISSION_CHECKLIST)
