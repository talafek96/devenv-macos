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

# Maccy must be RUNNING for its Option+V global hotkey to fire — but installing
# the cask doesn't make it launch at login, so a relogin silently kills it and
# the hotkey goes dead. Own a small LaunchAgent that re-opens Maccy every login
# (RunAtLoad → `open -a Maccy`; a no-op if it's already up). Prompt-free, unlike
# the System Events "add login item" route (which needs an Automation grant).
_MACCY_APP = Path("/Applications/Maccy.app")
_MACCY_AGENT_LABEL = "com.devenv.maccy"
_MACCY_AGENT_PLIST = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.devenv.maccy</string>
  <key>ProgramArguments</key>
  <array><string>/usr/bin/open</string><string>-a</string><string>Maccy</string></array>
  <key>RunAtLoad</key><true/>
</dict>
</plist>
"""

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

# CleanShot X's "Capture Area" shortcut → Option+Shift+S. Reverse-engineered by
# diffing its prefs (CleanShot 4.8.10): the shortcut lives under `LAVAtakeArea`
# as a Data blob whose bytes are the JSON string
#     {"carbonKey":1,"carbonModifiers":2560}
# carbonKey 1 = kVK_ANSI_S; carbonModifiers 2560 = optionKey 2048 + shiftKey 512.
# `defaults write -data <hex>` reproduces that blob; CleanShot reads it at launch
# (works even pre-seeded before its first run). Opaque per-version key, so this is
# best-effort — the checklist covers setting it by hand if the format ever moves.
_CLEANSHOT_DOMAIN = "pl.maketheweb.cleanshotx"
_CLEANSHOT_AREA_KEY = "LAVAtakeArea"
_CLEANSHOT_AREA_OPTION_SHIFT_S_HEX = (
    "7b22636172626f6e4b6579223a312c22636172626f6e4d6f64696669657273223a323536307d"
)
# `freezeScreen` (bool) = the "freeze the screen while I frame the shot" toggle —
# the whole reason for choosing CleanShot over the native capture. Default it on.
_CLEANSHOT_FREEZE_KEY = "freezeScreen"

# macOS "Screenshots" symbolic hotkeys (System Settings → Keyboard → Keyboard
# Shortcuts → Screenshots). CleanShot X pops a dialog on first launch asking you
# to turn these OFF so they don't collide with its capture shortcuts; we automate
# that when CleanShot is in play.
#
# IMPORTANT: disable by writing the FULL entry with enabled=0 AND keeping the
# default `value` (parameters). A bare `{enabled=0;}` (no value dict) is treated
# as malformed — System Settings silently deletes it and the shortcut reverts to
# its enabled default. Modifier mask bits: Shift=131072, Control=262144,
# Command=1048576 → Cmd+Shift=1179648, Ctrl+Cmd+Shift=1441792. Key params are
# (asciiOfDigit, kVK_ANSI_digit, mask): 3=(51,20) 4=(52,21) 5=(53,23).
#   28 save screen→file    29 copy screen→clipboard
#   30 save area→file      31 copy area→clipboard      184 screenshot toolbar
_SCREENSHOT_HOTKEYS_DISABLED = {
    28: "{enabled=0;value={parameters=(51,20,1179648);type=standard;};}",
    29: "{enabled=0;value={parameters=(51,20,1441792);type=standard;};}",
    30: "{enabled=0;value={parameters=(52,21,1179648);type=standard;};}",
    31: "{enabled=0;value={parameters=(52,21,1441792);type=standard;};}",
    184: "{enabled=0;value={parameters=(53,23,1179648);type=standard;};}",
}

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
    3. Option+Shift+S → "Capture Area" and screen-freeze are both set for you —
       restart CleanShot X once so it picks them up. If the shortcut didn't take,
       set it by hand: Settings → Shortcuts → "Capture Area" → record ⌥⇧S.
       Captures land on the clipboard; the Quick Access Overlay saves to a file.
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
        self._ensure_maccy_login_item(ctx)

    # Keep Maccy alive across logins so its Option+V hotkey stays live.
    def _ensure_maccy_login_item(self, ctx) -> None:
        if not _MACCY_APP.exists():
            return
        agents = ctx.home_dir / "Library/LaunchAgents"
        agents.mkdir(parents=True, exist_ok=True)
        plist = agents / f"{_MACCY_AGENT_LABEL}.plist"
        if not plist.exists() or plist.read_text() != _MACCY_AGENT_PLIST:
            plist.write_text(_MACCY_AGENT_PLIST)
        # Reload so it's active now and registered for every login (idempotent).
        ctx.run("launchctl", "unload", str(plist), check=False)
        ctx.run("launchctl", "load", "-w", str(plist), check=False)
        ctx.ok("Maccy set to launch at login (its Option+V hotkey needs it running)")

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
            for hk, entry in _SCREENSHOT_HOTKEYS_DISABLED.items():
                ctx.run("defaults", "write", "com.apple.symbolichotkeys",
                        "AppleSymbolicHotKeys", "-dict-add", str(hk),
                        entry, check=False)
            self._activate_settings(ctx)
            ctx.ok("Disabled native macOS screenshot shortcuts for CleanShot X "
                   "(applies after next logout/restart)")
            self._configure_cleanshot(ctx)
            return
        # Native fallback: "copy selected area to clipboard" → Option+Shift+S.
        ctx.run("defaults", "write", "com.apple.symbolichotkeys",
                "AppleSymbolicHotKeys", "-dict-add", str(_SCREENSHOT_HOTKEY_ID),
                _SCREENSHOT_HOTKEY_VALUE, check=False)
        self._activate_settings(ctx)
        ctx.ok("Bound macOS area-screenshot → clipboard to Option+Shift+S "
               "(may need a logout to take effect)")

    # Configure CleanShot's Windows-feel defaults — each written only if the user
    # hasn't already set it, so we never stomp their own choice. Both are read at
    # launch, so restart CleanShot X (or set on a fresh install) to pick them up.
    def _configure_cleanshot(self, ctx) -> None:
        # Capture-Area shortcut → Option+Shift+S.
        if ctx.command_output("defaults", "read", _CLEANSHOT_DOMAIN, _CLEANSHOT_AREA_KEY):
            ctx.info("CleanShot 'Capture Area' shortcut already set — leaving it.")
        else:
            ctx.run("defaults", "write", _CLEANSHOT_DOMAIN, _CLEANSHOT_AREA_KEY,
                    "-data", _CLEANSHOT_AREA_OPTION_SHIFT_S_HEX, check=False)
            ctx.ok("Set CleanShot 'Capture Area' shortcut to Option+Shift+S")

        # Freeze-screen-while-framing → on by default.
        if ctx.command_output("defaults", "read", _CLEANSHOT_DOMAIN, _CLEANSHOT_FREEZE_KEY):
            ctx.info("CleanShot freeze-screen already configured — leaving it.")
        else:
            ctx.run("defaults", "write", _CLEANSHOT_DOMAIN, _CLEANSHOT_FREEZE_KEY,
                    "-bool", "true", check=False)
            ctx.ok("Enabled CleanShot freeze-screen (frame the shot while paused)")

        ctx.info("Restart CleanShot X to pick up its shortcut / freeze settings.")

    def _activate_settings(self, ctx) -> None:
        ctx.run(_ACTIVATE_SETTINGS, "-u", check=False)

    def _print_checklist(self, ctx) -> None:
        ctx.header("Manual, one-time GUI permissions (cannot be scripted)")
        if ctx.karabiner_enabled:
            print(_KARABINER_CHECKLIST)
        if ctx.cleanshot_enabled or _CLEANSHOT_APP.exists():
            print(_CLEANSHOT_CHECKLIST)
        print(_PERMISSION_CHECKLIST)
