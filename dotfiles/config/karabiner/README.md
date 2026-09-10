# Karabiner keymap — Windows-feel keyboard layer

This is the reference for the Karabiner-Elements keymap in
[`karabiner.json`](./karabiner.json) (that file is the source of truth; this doc
summarizes it). The goal is a **Windows-style muscle memory** on macOS: `Ctrl`
does what `Cmd` does, the Windows key drives window/launcher actions, and an
external PC keyboard's modifiers sit where a Mac user expects.

Deployed as a symlink by the `dotfiles` module and only active when Karabiner is
installed (opt-in: `DEVENV_KARABINER=1`). Reload after edits:

```bash
launchctl kickstart -k "gui/$(id -u)/org.pqrs.service.agent.Karabiner-Console-User-Server"
```

## Conventions used below

- **`Ctrl+X`** means the physical Ctrl key — Karabiner rewrites these to the Mac
  `Cmd` equivalent, so Windows habits (`Ctrl+C`, `Ctrl+S`, …) just work.
- **`Win`** = the Windows/⊞ key. On an external PC keyboard it is remapped to
  **Option (⌥)** (see modifier swap below), and several `Win`+key combos are
  captured here for window management and launching.
- Many rules are **context-scoped**: excluded in the terminal (Ghostty), in
  Jump Desktop (remote sessions), or limited to browsers — noted per row.
- The modifier swap is **external keyboards only** (`device_unless
  is_built_in_keyboard`); the built-in MacBook keyboard is never remapped.

## Modifiers & base

| Keys | Action | Notes |
|---|---|---|
| Win → Option, Alt → Command | Swap ⌘/⌥ | External keyboards only; puts ⌘ next to the spacebar |
| Caps Lock | Disabled (does nothing) | |
| Cmd+Q | Blocked (no accidental quit) | Not in Jump |
| Physical Cmd+W | Blocked | Globe+W still closes; not in Jump |

## Input source (language)

| Keys | Action | Notes |
|---|---|---|
| Cmd+Shift (hold ⌘, tap Shift) | Switch input source (⌃⌥Space) | All keyboards; ⌘+Shift+key stays a normal shortcut |

## Windows-style editing

| Keys | Action |
|---|---|
| Ctrl+C / Ctrl+V / Ctrl+X | Copy / Paste / Cut |
| Ctrl+Z / Ctrl+Y | Undo / Redo |
| Ctrl+S / Ctrl+N | Save / New |
| Ctrl+A | Select All |
| Ctrl+F / Ctrl+G | Find / Find Next |
| Ctrl+W | Close (not in terminal) |

## Caret & word navigation

| Keys | Action | Notes |
|---|---|---|
| Ctrl+(Shift+)← / → | Move / select by word | |
| Ctrl+(Shift+)Home / End | Document start / end | |
| RightCtrl+← / → | Line / document start / end | Not terminal or Jump |
| RightCtrl+↑ / ↓ | Document top / bottom | Not terminal or Jump |
| Ctrl+Backspace | Delete word backward | Not Ghostty/Jump |
| Ctrl+Delete | Delete word forward | Not Ghostty/Jump |

## Window management & launching

| Keys | Action | Notes |
|---|---|---|
| Win+← / → | Snap left / right half | |
| Win+↑ / ↓ | Toggle maximize / restore | |
| Win+L | Lock screen (⌃⌘Q) | |
| Win+. | Emoji & Symbols (⌃⌘Space) | Not in Jump |
| Win+E | Open Finder at home | Not Ghostty/Jump |
| Win (tapped alone) | Apps launcher (Start-key feel) | Not in Jump |
| Alt+F4 | Quit app (⌘Q) | Not in Jump |

> Fuller window snapping (thirds, corners, displays) is handled by **Vorssaint**
> with Rectangle-style `⌃⌥`+key shortcuts — see the main README.

## Terminal (Ghostty)

| Keys | Action |
|---|---|
| RightOpt+← / → | Line start / end (Ctrl+A / Ctrl+E) |
| RightOpt+↑ / ↓ | Page up / down |
| RightOpt+Shift+↑ / ↓ | Line up / down |

## Finder

| Keys | Action |
|---|---|
| Delete | Move to Trash (⌘⌫) |

## Browser

| Keys | Action | Notes |
|---|---|---|
| Ctrl+L | Focus address bar (⌘L) | |
| Ctrl+D | Bookmark page (⌘D) | |
| Ctrl+Shift+T | Reopen closed tab | |
| Ctrl+Click | Open link in new tab (⌘Click) | |
| fn+F5 | Reload (⌘R) | Plain F5 stays Brightness |
| Cmd+N / Cmd+Shift+N | Option+N / Option+Shift+N | Edge only (extension quirk) |

## Jump Desktop (remote sessions)

Inside Jump Desktop the modifiers use a different scheme so shortcuts pass
through to the remote Windows machine correctly:

| Physical key | Sends |
|---|---|
| Left Command | Alt (left_option) |
| Left Option | Win (left_command) |
| Right Command | Alt (right_option) |
| Right Option | Ctrl (right_control) |
