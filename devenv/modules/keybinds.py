"""macOS keyboard layer: Ghostty App-Support dedupe, macOS defaults, and the
one-time GUI permission checklist that can't be scripted.

The Karabiner keymap, Ghostty config, and zellij config are deployed by the
dotfiles module (symlinks). This module handles the macOS-side pieces around
them and prints what still needs a manual click.
"""

from __future__ import annotations

import os
import plistlib
from pathlib import Path

from devenv import vorssaint_settings
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

# ── Dictation shortcut → "Press Right Command twice" ────────
# macOS's default dictation trigger is "Press 🌐 (Globe) twice", which fires by
# accident here because the Globe key is busy as our input-source switch / fn-row
# key. Move dictation onto a double-tap of the Right Command key instead.
# Symbolic hotkey 164, encoded exactly as System Settings writes it: a `modifier`
# entry whose two params are the right-Command mask (1048592 = Command 0x100000
# + right-side bit 0x10) and its negated release value (-1048593). A `modifier`
# type carries no key params, unlike the `standard` screenshot entries above.
_DICTATION_HOTKEY_ID = 164
_DICTATION_HOTKEY_VALUE = "{enabled=1;value={parameters=(1048592,-1048593);type=modifier;};}"

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

# Vorssaint is an all-in-one menu-bar toolkit that replaces several single-purpose
# apps at once: its modules cover the app switcher (was AltTab), window snapping
# (was Rectangle), and scroll-direction invert for external mice (was Mos), plus
# extras (per-app volume mixer, system monitors, keep-awake, …).
# Since 3.4.4 it also drives external-monitor speakers over DDC (was
# MonitorControl; see _retire_monitorcontrol). It can't replace Karabiner's
# per-keyboard remapping.
_VORSSAINT_APP = Path("/Applications/Vorssaint.app")
_VORSSAINT_DOMAIN = "com.vorssaint.utils"
_VORSSAINT_AGENT_LABEL = "com.devenv.vorssaint"
# At login: rebuild the settings file if a source changed while the watcher
# below wasn't running (e.g. before login), THEN open Vorssaint, in one job so
# Vorssaint can't start on a stale file (see vorssaint_settings.py --launch).
_VORSSAINT_AGENT_PLIST = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.devenv.vorssaint</string>
  <key>ProgramArguments</key>
  <array><string>/usr/bin/python3</string><string>{script}</string><string>--launch</string></array>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>{log}</string>
  <key>StandardErrorPath</key><string>{log}</string>
</dict>
</plist>
"""

# Vorssaint's settings live in a plist the repo owns:
# dotfiles/config/vorssaint/settings.plist (modules, scroll, snapping shortcuts,
# auto-quit exceptions, …; documented inline). Vorssaint 3.4.4+ reads
# ~/.config/vorssaint/settings.plist at every launch and overlays the keys it
# lists, leaving unlisted keys local. Vorssaint reads only that one file, so
# setup writes it as the shared file merged with the untracked private overlay
# ~/.config/vorssaint/settings.private.plist (private keys win), rather than
# symlinking it like the other dotfiles.
# The merge (and restart) lives in devenv/vorssaint_settings.py, shared with a
# LaunchAgent that watches both source files and re-applies on every save.
_VORSSAINT_WATCH_LABEL = "com.devenv.vorssaint-settings"
_VORSSAINT_WATCH_PLIST = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.devenv.vorssaint-settings</string>
  <key>ProgramArguments</key>
  <array><string>/usr/bin/python3</string><string>{script}</string></array>
  <key>WatchPaths</key>
  <array><string>{shared}</string><string>{private}</string></array>
  <key>StandardOutPath</key><string>{log}</string>
  <key>StandardErrorPath</key><string>{log}</string>
</dict>
</plist>
"""
# Onboarding flags stay `defaults` writes made before Vorssaint launches: on a
# fresh machine its first-run onboarding re-derives module state, so these must
# already be set or the modules from the settings file get reset.
_VORSSAINT_ONBOARDING = {
    "hasOnboarded": ("-bool", "true"),
    "featuresOnboardingVersion": ("-int", "4"),
    "onboardingStep": ("-int", "0"),
}

# MonitorControl used to drive external-monitor speakers over DDC (e.g. the Dell
# U3425WE over USB-C, whose macOS volume slider is greyed out). Vorssaint 3.4.4+
# does this itself (displayVolume* keys in its settings file), and two apps
# grabbing the volume keys fight, so setup retires MonitorControl on machines
# that had it: removes our login agent, quits it and uninstalls the cask.
_MONITORCONTROL_APP = Path("/Applications/MonitorControl.app")
_MONITORCONTROL_CASK = "monitorcontrol"
_MONITORCONTROL_AGENT_LABEL = "com.devenv.monitorcontrol"
# First Vorssaint with monitor speaker control (and the settings file).
_VORSSAINT_MIN_VERSION = (3, 4, 4)

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

# "After capture" behavior. `afterScreenshotActions` / `afterVideoActions` are
# INTEGER arrays of the enabled post-capture actions; [0,1] = show the Quick
# Access Overlay AND copy to the clipboard (so the result is on the clipboard
# immediately while the overlay still lets you decide to save/annotate).
# `defaults` can only write STRING arrays, so these must go through `plutil
# -json` on the plist file (verified: CleanShot keeps them as ints). Value codes
# reverse-engineered from CleanShot 5.x by diffing prefs; a future version could
# renumber them. `popupAskForDestinationWhenSaving` = ask where to save each time.
_CLEANSHOT_PLIST = "Library/Preferences/pl.maketheweb.cleanshotx.plist"
_CLEANSHOT_AFTER_CAPTURE_KEYS = ("afterScreenshotActions", "afterVideoActions")
_CLEANSHOT_AFTER_CAPTURE_JSON = "[0,1]"  # 0 = Quick Access Overlay, 1 = Copy
_CLEANSHOT_ASK_DESTINATION_KEY = "popupAskForDestinationWhenSaving"

# CleanShot's Option+Shift+S is an IN-APP global hotkey, so CleanShot must be
# RUNNING for it to fire — but the cask doesn't make it launch at login, so a
# restart silently kills it and the screenshot shortcut goes dead (same failure
# mode as Maccy). Own a LaunchAgent that re-opens CleanShot every login
# (RunAtLoad → `open -a "CleanShot X"`; a no-op if it's already up).
_CLEANSHOT_AGENT_LABEL = "com.devenv.cleanshotx"
_CLEANSHOT_AGENT_PLIST = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.devenv.cleanshotx</string>
  <key>ProgramArguments</key>
  <array><string>/usr/bin/open</string><string>-a</string><string>CleanShot X</string></array>
  <key>RunAtLoad</key><true/>
</dict>
</plist>
"""

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
  Vorssaint (menu-bar toolkit — replaces AltTab, Rectangle, Mos and MonitorControl):
    - Grant Accessibility on first launch — REQUIRED, and the one thing setup
      can't do for you. Without it the switcher, window snapping, and
      scroll-invert stay dead. (System Settings → Privacy & Security →
      Accessibility → enable Vorssaint.)
    - Modules and settings come from ~/.config/vorssaint/settings.plist, which
      setup builds from the repo's dotfiles/config/vorssaint/settings.plist plus
      your untracked ~/.config/vorssaint/settings.private.plist. Vorssaint
      applies it at every launch, so a listed setting you change in the app
      reverts on relaunch: change it in one of those files instead. Saving
      either file applies it within seconds (a LaunchAgent rebuilds the file
      and restarts Vorssaint; log in ~/Library/Logs/devenv-vorssaint-settings.log).
      If a module didn't come up (e.g. it needs a one-time download on a fresh
      machine), toggle it on in Vorssaint's Settings once.
    - App switcher: if ⌘Tab-hold doesn't feel right, set its Hold key to Command
      in Settings (your external Alt = ⌘).
    - Window snapping uses Rectangle-style shortcuts, pre-set by setup:
      halves ⌃⌥←/→/↑/↓, corners ⌃⌥U/I/J/K, thirds ⌃⌥D/F/G, maximize ⌃⌥↩,
      center ⌃⌥C (⌃⌥ = Win+Ctrl on the external keyboard, so ⌥+arrow word-jump
      still works).
    - Kept alive at login by the com.devenv.vorssaint LaunchAgent; you can also
      flip Vorssaint's own "start at login" as a backup.
  Maccy (clipboard history):
    - Grant Accessibility if you want it to paste directly.
    - Monitor speakers (replaces MonitorControl): with sound going to a
      monitor (e.g. the Dell U3425WE over USB-C), the volume keys/wheel move
      the monitor's own volume in 2% steps, and the volume island follows the
      pointer to that screen. Settings → Displays → Monitor speakers.
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
        self._set_dictation_shortcut(ctx)
        self._set_app_hotkeys(ctx)
        self._retire_monitorcontrol(ctx)
        self._ensure_vorssaint_login_item(ctx)
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

    # Move the Dictation trigger off "Globe twice" (the Globe key is busy as the
    # input-source / fn-row key here) onto a double-tap of the Right Command key.
    def _set_dictation_shortcut(self, ctx) -> None:
        ctx.run("defaults", "write", "com.apple.symbolichotkeys",
                "AppleSymbolicHotKeys", "-dict-add", str(_DICTATION_HOTKEY_ID),
                _DICTATION_HOTKEY_VALUE, check=False)
        self._activate_settings(ctx)
        ctx.ok("Dictation shortcut set to Right Command twice "
               "(was Globe-twice; may need a logout to fully take effect)")

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
        self._ensure_login_item(ctx, _MACCY_AGENT_LABEL, _MACCY_AGENT_PLIST)
        ctx.ok("Maccy set to launch at login (its Option+V hotkey needs it running)")

    # Configure Vorssaint (onboarding flags + the merged settings file) and keep
    # it alive across logins. Accessibility still has to be granted by hand (see checklist).
    def _ensure_vorssaint_login_item(self, ctx) -> None:
        if not _VORSSAINT_APP.exists():
            ctx.info("Vorssaint not installed — skipping (app switcher / window "
                     "snapping / scroll-invert / volume mixer won't be available)")
            return

        # Quit first: Vorssaint only reads the settings file at launch, skips it
        # while another instance runs, and would overwrite onboarding writes on
        # exit. Seed onboarding BEFORE it relaunches (see _VORSSAINT_ONBOARDING).
        vorssaint_settings.quit_and_wait()
        for key, (vtype, value) in _VORSSAINT_ONBOARDING.items():
            ctx.run("defaults", "write", _VORSSAINT_DOMAIN, key, vtype, value, check=False)
        count = self._write_vorssaint_settings(ctx)
        if count:
            ctx.ok(f"Vorssaint settings file written ({count} keys: switcher, window "
                   "snapping, scroll invert/linear/zoom, volume mixer, auto-quit, +extras); "
                   "applied when it relaunches")

        # start: Vorssaint was quit above; the job reopens it.
        self._ensure_login_item(ctx, _VORSSAINT_AGENT_LABEL, _VORSSAINT_AGENT_PLIST.format(
            script=Path(vorssaint_settings.__file__).resolve(),
            log=ctx.home_dir / "Library/Logs/devenv-vorssaint-settings.log"), start=True)
        ctx.ok("Vorssaint set to launch at login — grant it Accessibility once "
               "(see the checklist) or the switcher/snapping/scroll won't work")

    # Write the merged settings file (see devenv/vorssaint_settings.py) and
    # install the LaunchAgent that rebuilds it and restarts Vorssaint whenever
    # either source file is saved. Returns the number of settings (0 on error).
    def _write_vorssaint_settings(self, ctx) -> int:
        if vorssaint_settings.ensure_private():
            ctx.ok(f"Created {vorssaint_settings.PRIVATE} (your machine-specific "
                   "Vorssaint settings)")
        try:
            text, count = vorssaint_settings.render()
        except vorssaint_settings.SettingsError as exc:
            ctx.err(f"Vorssaint settings not written: can't read {exc}")
            return 0
        backup = vorssaint_settings.write(text)
        if backup:
            ctx.warn(f"Backed up a hand-made {vorssaint_settings.TARGET} -> {backup}")

        log = ctx.home_dir / "Library/Logs/devenv-vorssaint-settings.log"
        self._ensure_login_item(ctx, _VORSSAINT_WATCH_LABEL, _VORSSAINT_WATCH_PLIST.format(
            script=Path(vorssaint_settings.__file__).resolve(),
            shared=vorssaint_settings.SHARED, private=vorssaint_settings.PRIVATE, log=log))
        ctx.ok("Vorssaint settings auto-apply: saving either settings file rebuilds "
               f"it and restarts Vorssaint (log: {log})")
        return count

    # Hand monitor-speaker volume over to Vorssaint: on a machine that ran an
    # older setup, remove our MonitorControl login agent, quit it and uninstall
    # the cask. Skipped while Vorssaint is missing or older than 3.4.4, so the
    # monitor never loses volume keys. Idempotent: a no-op once it's gone.
    def _retire_monitorcontrol(self, ctx) -> None:
        agent = ctx.home_dir / f"Library/LaunchAgents/{_MONITORCONTROL_AGENT_LABEL}.plist"
        cask = _MONITORCONTROL_CASK in ctx.command_output("brew", "list", "--cask").split()
        if not (agent.exists() or cask):
            if _MONITORCONTROL_APP.exists():
                # Installed by hand, not by setup: not ours to remove.
                ctx.warn("MonitorControl is installed (not by setup): quit it, or it "
                         "fights Vorssaint over the monitor's volume keys")
            return
        version = self._vorssaint_version()
        if version < _VORSSAINT_MIN_VERSION:
            ctx.warn("Keeping MonitorControl: Vorssaint "
                     f"{'.'.join(map(str, version)) if version else 'is not installed'}"
                     f"{' is older than 3.4.4' if version else ''}, so it can't drive "
                     "monitor speakers yet. Update Vorssaint and re-run setup.")
            return
        if agent.exists():
            ctx.run("launchctl", "unload", str(agent), check=False)
            agent.unlink()
        if ctx.run("pgrep", "-x", "MonitorControl", capture=True, check=False).returncode == 0:
            ctx.run("osascript", "-e", 'quit app "MonitorControl"', check=False)
        if cask:
            ctx.run("brew", "uninstall", "--cask", _MONITORCONTROL_CASK, check=False)
        if _MONITORCONTROL_APP.exists():
            ctx.warn(f"{_MONITORCONTROL_APP} is still there after uninstalling: "
                     "delete it by hand so it can't grab the volume keys")
        else:
            ctx.ok("Removed MonitorControl: Vorssaint now drives monitor speakers")

    def _vorssaint_version(self) -> tuple[int, ...]:
        try:
            info = plistlib.loads((_VORSSAINT_APP / "Contents/Info.plist").read_bytes())
            return tuple(int(x) for x in info["CFBundleShortVersionString"].split(".")[:3])
        except (OSError, KeyError, ValueError, plistlib.InvalidFileException):
            return ()

    # Write + (re)load a per-user LaunchAgent that re-opens an app every login.
    # Shared by Maccy, Vorssaint and CleanShot: both expose global hotkeys that only fire
    # while the app is running, and neither cask launches itself at login.
    # start=True: the caller quit the app, so run the job now even when the
    # agent needs no reload.
    def _ensure_login_item(self, ctx, label: str, plist_text: str,
                           start: bool = False) -> None:
        agents = ctx.home_dir / "Library/LaunchAgents"
        agents.mkdir(parents=True, exist_ok=True)
        plist = agents / f"{label}.plist"
        changed = not plist.exists() or plist.read_text() != plist_text
        if changed:
            plist.write_text(plist_text)
        # Reload only when needed: a reload re-runs RunAtLoad, and `open -a` on
        # an app that's already running pops its window (Maccy's history).
        loaded = ctx.run("launchctl", "list", label, capture=True, check=False).returncode == 0
        if loaded and not changed:
            if start:
                ctx.run("launchctl", "kickstart", f"gui/{os.getuid()}/{label}", check=False)
            return
        ctx.run("launchctl", "unload", str(plist), check=False)
        ctx.run("launchctl", "load", "-w", str(plist), check=False)

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

        # After-capture: copy to clipboard AND show the Quick Access Overlay, plus
        # ask where to save each time. The action arrays must be INTEGER arrays,
        # which `defaults` can't write, so quit CleanShot (so it can't overwrite),
        # edit the plist with `plutil -json`, and flush cfprefsd's cache.
        ctx.run("osascript", "-e", 'quit app "CleanShot X"', check=False)
        ctx.run("defaults", "write", _CLEANSHOT_DOMAIN, _CLEANSHOT_ASK_DESTINATION_KEY,
                "-bool", "true", check=False)
        plist = ctx.home_dir / _CLEANSHOT_PLIST
        if plist.exists():
            for key in _CLEANSHOT_AFTER_CAPTURE_KEYS:
                ctx.run("plutil", "-replace", key, "-json",
                        _CLEANSHOT_AFTER_CAPTURE_JSON, str(plist), check=False)
            ctx.run("killall", "cfprefsd", check=False)
            ctx.ok("CleanShot after-capture: copy to clipboard + Quick Access "
                   "Overlay, and prompt for destination on save")
        else:
            ctx.info("CleanShot prefs not created yet — after-capture actions will "
                     "apply on a later setup run (or set them in Settings → After Capture)")

        # CleanShot's Option+Shift+S only fires while CleanShot is running; keep
        # it alive across logins so the screenshot hotkey survives a restart.
        if _CLEANSHOT_APP.exists():
            self._ensure_login_item(ctx, _CLEANSHOT_AGENT_LABEL, _CLEANSHOT_AGENT_PLIST,
                                    start=True)  # quit above for the prefs edit
            ctx.ok("CleanShot X set to launch at login (its Option+Shift+S hotkey needs it running)")

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
