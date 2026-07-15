# devenv-macos

Reproducible macOS development environment — bring a fresh, out-of-the-box
MacBook to a known-good, Windows-feel state with one command. The macOS
counterpart to [`talafek96/devenv`](https://github.com/talafek96/devenv).

## One-liner (fresh machine)

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/talafek96/devenv-macos/main/bootstrap.sh)
```

This installs **Homebrew** (which also installs the Xcode Command Line Tools →
git), installs + authenticates **gh**, clones this repo, and runs the full
setup. You'll be asked for your password once (Homebrew + Karabiner require it).

> Clone location is agnostic — defaults to `~/devenv-macos`. Put it elsewhere
> with `DEVENV_MACOS_DIR=/path bash <(curl ...)`. The setup works from wherever
> the repo lives.

## Quick start (already have brew + git)

```bash
git clone https://github.com/talafek96/devenv-macos.git   # anywhere you like
cd devenv-macos
./setup.sh
exec zsh                    # pick up the new shell
```

## What it sets up

### Dotfiles (symlinked from `dotfiles/`)
- **`~/.zshrc`** — eternal history, prefix history-search (↑/↓), completion, a
  self-contained git-aware prompt (macOS-native, no dependency), `fzf` Ctrl-R,
  Homebrew shellenv, safe aliases (`ll`/`la`/`gs`/…), `extract()`, macOS color.
- **`~/.inputrc`** — readline: case-insensitive completion, prefix history search.
- **`~/.config/zellij/config.kdl`** — locked-mode, mouse copy, Alt keybindings.
- **`~/.config/ghostty/config`** — Windows-Terminal keybinds, `option-as-alt=left`,
  Ctrl+V freed for Claude Code image paste, Cmd+arrows → zellij pane focus. Ends
  with an optional include of `~/.config/ghostty/local.conf` (not tracked) for
  machine-local, personal-taste settings like `theme = …`.
- **`~/.config/karabiner/karabiner.json`** — the Windows-feel keymap (globe→Ctrl
  scoped to the built-in keyboard, Windows shortcut translations, ⌥+Shift language
  switch, the function-key row scheme below, and more).

### Homebrew formulae (`packages`)
`gh`, `zellij`, `duti`, `fzf`, `ripgrep`, `fd`, `bat`, `eza`, `jq`, `tree`.

### Homebrew casks (`casks`)
`ghostty`, `karabiner-elements`, `alt-tab`, `rectangle`, `maccy`, `claude-code`,
`google-chrome`, `whatsapp`, `transmission`, `vlc`, `macdroid`.

### Dev toolchain (`tools`)
`uv` (Python package/project manager, via the Astral installer). Skip with `--skip tools`.

### macOS keyboard layer (`keybinds`)
Ghostty App-Support dedupe (macOS loads both `~/.config` and the App-Support
path and merges them, so any duplicate symlink there is removed to avoid
double-loading the config), macOS defaults (globe = Do Nothing, natural scroll,
fast key repeat / press-and-hold off), plus a printed checklist of the one-time
GUI permission grants that can't be scripted (Karabiner / AltTab / Rectangle).

### Function-key row (F1–F12)

Because globe→Ctrl consumes the real Fn key, macOS can no longer generate the
printed hardware functions on its own. So the row is handled entirely in
Karabiner:

- **Plain F1–F12** → real function keys (for apps, IDEs, debugging).
- **Ctrl + F-row** → the printed hardware functions. Since globe **is** Ctrl,
  hold **Globe *or* the ⌃ Control key** + an F-key. The rule is scoped to the
  built-in keyboard and *consumes* the Ctrl, so external keyboards keep normal
  Ctrl+F-keys and the emitted media/brightness event is unmodified.

| Ctrl+ | Action | | Ctrl+ | Action |
|-------|--------|-|-------|--------|
| F1 / F2 | Brightness − / + | | F7 / F8 / F9 | Prev / Play-Pause / Next |
| F3 | Mission Control | | F10 | Mute |
| F4 | Spotlight (⌘Space) | | F11 / F12 | Volume − / + |
| F5 | Dictation | | F6 | Do Not Disturb |

Two of these depend on macOS features that have **no reliable keystroke or CLI**:

- **F6 Do Not Disturb** — macOS only toggles Focus via the Shortcuts app.
  Create a shortcut named exactly **`Toggle Do Not Disturb`** (one action: *Set
  Focus → Do Not Disturb → Toggle*); Karabiner's Ctrl+F6 runs
  `shortcuts run "Toggle Do Not Disturb"`. **Works.**
- **F5 Dictation** — **best-effort / currently unreliable.** Ctrl+F5 emits the
  `dictation` keycode (safe — harmless if the app receives it), but macOS 26
  does not reliably start Dictation from a synthesized key even with Dictation
  enabled. Do **not** map it to a real key-combo (e.g. ⌃⌥⌘-letter): if macOS
  doesn't capture it, the combo leaks into the focused app. If you need
  dependable dictation, use a native double-tap trigger (*Settings → Keyboard →
  Dictation → Shortcut*) pressed directly, not via F5.

### Private config
`~/.zshrc_private` is created (not tracked) for API keys, machine-specific
aliases, conda init, etc. It's sourced at the end of `~/.zshrc`.

`~/.config/ghostty/local.conf` plays the same role for Ghostty: the tracked
config ends with `config-file = ?~/.config/ghostty/local.conf` (the `?` makes it
optional), so personal-taste overrides like `theme = …` live outside the repo.

## Idempotent + self-updating

Re-running is safe and **upgrades** anything outdated:

```bash
cd <repo> && git pull && ./setup.sh
```

`brew install` skips what's present; `brew upgrade` bumps outdated formulae/casks
(self-updating apps like Chrome are left to update themselves). `uv`/`rustup`
self-update, dotfile symlinks are re-pointed, and existing files are backed up to
`*.devenv-backup.*`.

## CLI

```bash
./setup.sh                       # full setup (all modules)
./setup.sh --only casks,dotfiles # just those modules
./setup.sh --skip tools          # everything except the dev toolchain
./setup.sh list                  # list modules in run order
```

## Architecture

Thin bash bootstrap → Python entry → auto-discovered modules. To add a step,
drop a file in `devenv/modules/` that subclasses `Module`.

```
devenv-macos/
├── bootstrap.sh                 # one-liner for a fresh Mac (installs brew, gh, clones, runs setup)
├── setup.sh                     # thin bootstrap (ensures brew + python3, execs setup.py)
├── setup.py                     # Python entry point
├── devenv/
│   ├── cli.py                   # CLI: setup / list, --skip / --only
│   ├── core.py                  # Context: logging, command execution, brew prefix
│   └── modules/
│       ├── __init__.py          # Module base + auto-discovery
│       ├── packages.py          # brew formulae            (order 10)
│       ├── casks.py             # brew casks / GUI apps     (order 15)
│       ├── tools.py             # uv (Python)               (order 20)
│       ├── dotfiles.py          # symlinks + gitconfig      (order 30)
│       └── keybinds.py          # macOS defaults + perms    (order 40)
├── dotfiles/
│   ├── zshrc  inputrc  gitconfig
│   └── config/{zellij,ghostty,karabiner}/…
└── Makefile                     # make setup / update / lint / test / check
```

## Testing

```bash
make check    # shellcheck + py_compile + module discovery + karabiner.json validation
```
