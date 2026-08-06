"""macOS keyboard layer: Ghostty App-Support dedupe, macOS defaults, and the
one-time GUI permission checklist that can't be scripted.

The Karabiner keymap, Ghostty config, and zellij config are deployed by the
dotfiles module (symlinks). This module handles the macOS-side pieces around
them and prints what still needs a manual click.
"""

from __future__ import annotations

from pathlib import Path

from devenv.modules import Module

_ACTIVATE_SETTINGS = ("/System/Library/PrivateFrameworks/SystemAdministration"
                      ".framework/Resources/activateSettings")

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

# ── macOS symbolic hotkeys to DISABLE ───────────────────────
# macOS reserves Ctrl+←/→ for Mission Control "Move left/right a space" and
# swallows those chords system-wide BEFORE any app (terminal included) sees
# them — so Ctrl+Left/Right word-jump in Ghostty/zsh produced *nothing*. We turn
# those four off for the Windows-feel setup (Windows doesn't switch desktops on
# Ctrl+arrow anyway; use a trackpad swipe / Mission Control for spaces).
#   79 = Move left a space (Ctrl+←)        81 = Move right a space (Ctrl+→)
#   80 = + shift (move window left)         82 = + shift (move window right)
_DISABLE_SYMBOLIC_HOTKEYS = [79, 80, 81, 82]

# ── Third-party app hotkeys (Windows-feel) ──────────────────
# Maccy's clipboard-history popup → Option+V (the Windows `Win+V` clipboard,
# with the Windows key sitting where Option is on a Mac). Maccy stores its
# shortcut (KeyboardShortcuts lib) as a JSON string of Carbon key + modifier
# codes: keyCode 9 = "V", modifier 2048 = optionKey (⌥ alone). Read at launch,
# so it takes effect next time Maccy starts.
_MACCY_DOMAIN = "org.p0deje.Maccy"
_MACCY_POPUP_KEY = "KeyboardShortcuts_popup"
_MACCY_POPUP_OPTION_V = '{"carbonKeyCode":9,"carbonModifiers":2048}'

# ── Screenshot hotkey → Option+Shift+S ──────────────────────
# CleanShot X (opt-in, DEVENV_CLEANSHOT) is the preferred capture app — it can
# FREEZE the screen so you can frame the shot. Its capture shortcut is set in
# the app itself (Settings → Shortcuts) — surfaced in the checklist. When it's
# not present, we bind the built-in macOS "copy selected area to clipboard"
# (symbolic hotkey 31 — the Windows `Win+Shift+S` behaviour) to Option+Shift+S.
#   parameters = (ascii, virtualKeyCode, modifierMask)
#   's' = 115, kVK_ANSI_S = 1, Option+Shift = 524288 (⌥) + 131072 (⇧) = 655360
_CLEANSHOT_APP = Path("/Applications/CleanShot X.app")
_SCREENSHOT_HOTKEY_ID = 31
_SCREENSHOT_HOTKEY_VALUE = "{enabled=1;value={parameters=(115,1,655360);type=standard;};}"

# All macOS "Screenshots" symbolic-hotkey ids (System Settings → Keyboard →
# Keyboard Shortcuts → Screenshots). CleanShot X pops a dialog on first launch
# asking you to turn these OFF so they don't collide with its capture shortcuts;
# we automate that when CleanShot is in play.
#   28 save screen→file    29 copy screen→clipboard
#   30 save area→file      31 copy area→clipboard      184 screenshot toolbar
_SCREENSHOT_HOTKEY_IDS = [28, 29, 30, 31, 184]

_GHOSTTY_APP_SUPPORT = "Library/Application Support/com.mitchellh.ghostty/config"

_KARABINER_CHECKLIST = """\
  Karabiner-Elements (the keymap won't work until all three are done):
    1. Open Karabiner-Elements → approve the driver / system-extension prompt.
    2. System Settings → Privacy & Security → Input Monitoring   → enable Karabiner.
    3. System Settings → Privacy & Security → Accessibility        → enable Karabiner.
"""

_CLEANSHOT_CHECKLIST = """\
  CleanShot X (opt-in screenshot app with screen-freeze):
    1. Launch CleanShot X → grant Screen Recording + Accessibility when prompted.
       Its "turn off native screenshot shortcuts" dialog is already satisfied —
       this module set them disabled in prefs (CleanShot reads that), so just
       click Done. (macOS only fully drops the old chords after a logout/restart;
       or untick them now in System Settings → Keyboard Shortcuts → Screenshots.)
    2. Activate your license: menu-bar icon → Settings → General → "Activate
       License" (or paste the key at first launch).
    3. Bind Option+Shift+S to capture: Settings → Shortcuts. To get the Windows
       "freeze then frame" behaviour, record ⌥⇧S on the "Capture Area (Freeze)"
       / "Freeze" action (there's also a plain "Capture Area" if you prefer no
       freeze). Captures land on the clipboard + the Quick Access Overlay lets
       you save to a file afterwards.
"""

_PERMISSION_CHECKLIST = """\
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
        self._disable_space_switch_hotkeys(ctx)
        self._set_app_hotkeys(ctx)
        self._bind_screenshot_hotkey(ctx)
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

    # Free Ctrl+←/→ from Mission Control so they reach the terminal (word-jump).
    def _disable_space_switch_hotkeys(self, ctx) -> None:
        for hk in _DISABLE_SYMBOLIC_HOTKEYS:
            # -dict-add replaces the whole entry for this id; the stock entries
            # carry no key-binding params, so {enabled=0;} is enough to disable.
            ctx.run("defaults", "write", "com.apple.symbolichotkeys",
                    "AppleSymbolicHotKeys", "-dict-add", str(hk), "{enabled=0;}",
                    check=False)
        # Apply without a full logout (Ctrl+arrow may still need a re-login on
        # some macOS builds to fully release from the WindowManager).
        self._activate_settings(ctx)
        ctx.ok("Disabled macOS Ctrl+←/→ space-switching (frees Ctrl+arrow for word-jump)")

    # Windows-feel global hotkeys for third-party apps (currently just Maccy).
    def _set_app_hotkeys(self, ctx) -> None:
        ctx.run("defaults", "write", _MACCY_DOMAIN, _MACCY_POPUP_KEY,
                "-string", _MACCY_POPUP_OPTION_V, check=False)
        ctx.ok("Set Maccy clipboard-history popup to Option+V "
               "(takes effect next time Maccy launches)")

    # Screenshot on Option+Shift+S — Windows `Win+Shift+S`.
    def _bind_screenshot_hotkey(self, ctx) -> None:
        # CleanShot X owns the screenshot when opted in or already installed. It
        # asks you to disable ALL native "Screenshots" shortcuts so they don't
        # fight its capture hotkeys — we write that here. NOTE: macOS only reads
        # these symbolic hotkeys at LOGIN, so `activateSettings -u` doesn't make
        # it live; it takes effect on the next logout/restart (or untick them in
        # System Settings → Keyboard Shortcuts → Screenshots for it to apply now).
        # CleanShot's own capture hotkey is still set inside the app: the
        # checklist walks through license activation + the Option+Shift+S binding.
        if ctx.cleanshot_enabled or _CLEANSHOT_APP.exists():
            for hk in _SCREENSHOT_HOTKEY_IDS:
                ctx.run("defaults", "write", "com.apple.symbolichotkeys",
                        "AppleSymbolicHotKeys", "-dict-add", str(hk),
                        "{enabled=0;}", check=False)
            self._activate_settings(ctx)
            ctx.ok("Disabled native macOS screenshot shortcuts for CleanShot X "
                   "(applies after next logout/restart; bind Option+Shift+S "
                   "inside CleanShot — see the checklist)")
            return
        # Native fallback: "copy selected area to clipboard" → Option+Shift+S.
        ctx.run("defaults", "write", "com.apple.symbolichotkeys",
                "AppleSymbolicHotKeys", "-dict-add", str(_SCREENSHOT_HOTKEY_ID),
                _SCREENSHOT_HOTKEY_VALUE, check=False)
        self._activate_settings(ctx)
        ctx.ok("Bound macOS area-screenshot → clipboard to Option+Shift+S "
               "(may need a logout to take effect)")

    def _activate_settings(self, ctx) -> None:
        ctx.run(_ACTIVATE_SETTINGS, "-u", check=False)

    def _print_checklist(self, ctx) -> None:
        ctx.header("Manual, one-time GUI permissions (cannot be scripted)")
        if ctx.karabiner_enabled:
            print(_KARABINER_CHECKLIST)
        if ctx.cleanshot_enabled or _CLEANSHOT_APP.exists():
            print(_CLEANSHOT_CHECKLIST)
        print(_PERMISSION_CHECKLIST)
