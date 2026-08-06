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
setup. You'll be asked for your password once (Homebrew requires it; the
opt-in Karabiner keymap also prompts — see [Karabiner is opt-in](#karabiner-is-opt-in)).

> **Want the Windows-feel Karabiner keymap?** It's **opt-in** — prefix any
> setup command with `DEVENV_KARABINER=1`. Details below.

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
- **`~/.zsh_aliases_shared`** — shared, repo-managed aliases (symlinked from
  `dotfiles/zsh_aliases`), sourced by `~/.zshrc`. Ships e.g. `claude` →
  `claude --dangerously-skip-permissions` (bypass-permissions mode). A personal,
  untracked **`~/.zsh_aliases`** is created alongside it and sourced *last*, so
  your machine-local aliases override the shared ones.
- **`~/.inputrc`** — readline: case-insensitive completion, prefix history search.
- **`~/.config/zellij/config.kdl`** — locked-mode, mouse copy, Alt keybindings.
- **`~/.config/ghostty/config`** — Windows-Terminal keybinds, `option-as-alt=left`,
  text paste on Ctrl+V *and* Ctrl+Shift+V, Claude Code **image paste on Cmd+V**
  (Cmd+V emits the Ctrl+V byte Claude catches to paste a clipboard image),
  Cmd+arrows → zellij pane focus. Ends
  with an optional include of `~/.config/ghostty/local.conf` (not tracked) for
  machine-local, personal-taste settings like `theme = …`.
- **`~/.config/karabiner/karabiner.json`** *(opt-in — `DEVENV_KARABINER=1`)* —
  the Windows-feel keymap (Windows shortcut translations on the Control key,
  ⌥+Shift language switch, the function-key row scheme below, and more). The
  globe/fn key is left **native** (see below). Only symlinked when opted in.
- **`~/Library/Application Support/Code/User/settings.json`** — VS Code user
  settings (format-on-save, 100-col ruler, zsh terminal, telemetry off, …).

### Homebrew formulae (`packages`)
`gh`, `zellij`, `duti`, `mas`, `fzf`, `ripgrep`, `fd`, `bat`, `eza`, `jq`, `tree`.

### Homebrew casks (`casks`)
`ghostty`, `alt-tab`, `rectangle`, `maccy`, `claude-code`, `visual-studio-code`,
`google-chrome`, `whatsapp`, `transmission`, `vlc`, `macdroid`.
`karabiner-elements` is added **only** when `DEVENV_KARABINER=1`, and
`cleanshot` (CleanShot X) **only** when `DEVENV_CLEANSHOT=1` (both opt-in — see below).

### Mac App Store apps (`appstore`)
Installed via `mas` (needs you signed in to the App Store):
- **Pixea** — modern image / media viewer, set as the default for photos.

> Apple blocks *first-time* `mas` installs, so a brand-new app must be "gotten"
> once from the App Store GUI. This module never fails the setup over that: on
> an interactive run it **prompts** you to open the App Store / retry / skip; on
> a non-interactive run it prints the link and moves on. Skipped apps finish on
> the next `./setup.sh` once they're installed.

### Default apps for file types (`fileassoc`)
Uses `duti` to make **Pixea** the default opener (replacing Preview) for
`.jpg`/`.jpeg`, `.png`, `.heic`/`.heif`, `.webp`, and the RAW formats Pixea
supports (`.nef`, `.cr2`/`.cr3`/`.crw`, `.arw`/`.sr2`, `.dng`, `.raf`, `.orf`,
`.erf`, `.mrw`, `.rwl`, `.3fr`). Each binding is **verified** with `duti -x`
and retried once (LaunchServices lags right after an app is installed).

### Dev toolchain (`tools`)
`uv` (Python package/project manager, via the Astral installer). Skip with `--skip tools`.

### macOS keyboard layer (`keybinds`)
Ghostty App-Support dedupe (macOS loads both `~/.config` and the App-Support
path and merges them, so any duplicate symlink there is removed to avoid
double-loading the config), macOS defaults (globe tap = Change Input Source, natural scroll,
fast key repeat / press-and-hold off), **disabling macOS's `Ctrl+←/→`
"move a space" Mission Control shortcuts** (they're grabbed system-wide and
otherwise swallow `Ctrl+arrow` before the terminal can use it for word-jump),
setting **Maccy's clipboard-history popup to `Option+V`** (the Windows `Win+V`
clipboard — the Windows key sits where Option is on a Mac), binding
**screenshot to `Option+Shift+S`** (the Windows `Win+Shift+S` — CleanShot X if
opted in / installed, otherwise the built-in macOS "copy selected area to
clipboard"; see [CleanShot X is opt-in](#cleanshot-x-is-opt-in)),
plus a printed checklist of the one-time
GUI permission grants that can't be scripted (AltTab / Rectangle, and — when
opted in — Karabiner).

### Karabiner is opt-in

The Windows-feel **Karabiner keymap** (the cask, `karabiner.json`, and its
permission checklist) is **not installed by default** — nobody who just wants
the terminal + tooling is forced into a system-wide keyboard remapper. Enable
it by setting the `DEVENV_KARABINER` environment variable before setup:

```bash
DEVENV_KARABINER=1 ./setup.sh            # full setup, with the Karabiner keymap
DEVENV_KARABINER=1 ./setup.sh --only casks,dotfiles,keybinds   # just the keymap bits
```

Or via the one-liner on a fresh machine:

```bash
DEVENV_KARABINER=1 bash <(curl -fsSL https://raw.githubusercontent.com/talafek96/devenv-macos/main/bootstrap.sh)
```

Accepted truthy values: `1`, `true`, `yes`, `on`. When unset, `casks` skips
`karabiner-elements`, `dotfiles` skips the `karabiner.json` symlink, and
`keybinds` omits the Karabiner permission steps. Re-running **without** the flag
never removes an already-linked keymap — it just stops managing it.

### CleanShot X is opt-in

Unlike Windows, the macOS built-in screenshot doesn't **freeze the screen** when
you start a capture, which makes it hard to time/frame a shot around menus or
hover states. [CleanShot X](https://cleanshot.com) solves that (its "Freeze"
capture pauses the display), and can copy to the clipboard *and* save to a file
afterwards — but it's a **paid app** ($29 one-time), so it's **opt-in**:

```bash
DEVENV_CLEANSHOT=1 ./setup.sh    # install CleanShot X + surface its setup checklist
```

When opted in (or if CleanShot X is already installed), the `keybinds` module
**disables all native macOS screenshot shortcuts** (so they don't collide with
CleanShot's — the "turn these off" dialog CleanShot pops on first launch is
handled for you) and prints a checklist to **activate your license** and **bind
`Option+Shift+S`** to its Freeze/Capture-Area action (a one-time in-app step —
CleanShot stores shortcuts internally, so it can't be scripted). Enable both flags together if you want them:

```bash
DEVENV_KARABINER=1 DEVENV_CLEANSHOT=1 ./setup.sh
```

**When unset** (and CleanShot X isn't installed), `keybinds` instead binds the
built-in macOS **"copy selected area to clipboard"** to `Option+Shift+S` — the
Windows `Win+Shift+S` behaviour (no freeze, but zero-install). Some macOS builds
only apply this after a logout.

### Function-key row (F1–F12) & the globe/fn key

The globe/fn key keeps its **full native dual role** — Karabiner does **not**
touch the F-row (`fn_function_keys` is `[]`), so macOS owns it entirely, exactly
like a stock Mac:

- **Tap globe** → cycle keyboard input sources (`AppleFnUsageType = 1`).
- **Hold globe (= fn) + F1–F12** → the printed hardware functions (brightness,
  Mission Control, Spotlight, media, volume, etc.).
- **Plain F1–F12** → real function keys (for apps, IDEs, debugging), because
  `com.apple.keyboard.fnState = true` ("use F1–F12 as standard function keys").
- **fn** also gives the native chords: `fn+←/→` = Home/End, `fn+↑/↓` =
  PageUp/PageDown, `fn+Delete` = forward-delete.

> The critical bit: **don't let Karabiner remap the F-row.** Any `fn_function_keys`
> override stops macOS's native `fn`→hardware inversion from applying, which
> silently breaks `globe+F1..F12`. Leave it `[]` and let `fnState` do the work.

> Ctrl is the **physical Control key** (native), which drives all the
> Windows-style `Ctrl+…` translations. The bottom-left **corner** key is fn, as
> on a stock MacBook — it is *not* remapped to Control.

### Private config
`~/.zshrc_private` is created (not tracked) for API keys, machine-specific
aliases, conda init, etc. It's sourced at the end of `~/.zshrc`.

`~/.zsh_aliases` is created (not tracked) for your personal aliases. It's
sourced *after* the shared `~/.zsh_aliases_shared`, so your entries win.

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
DEVENV_KARABINER=1 ./setup.sh    # full setup + the opt-in Karabiner keymap
DEVENV_CLEANSHOT=1 ./setup.sh    # full setup + CleanShot X (paid screenshot app)
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
│       ├── appstore.py          # Mac App Store apps (mas)  (order 16)
│       ├── tools.py             # uv (Python)               (order 20)
│       ├── dotfiles.py          # symlinks + gitconfig      (order 30)
│       ├── keybinds.py          # macOS defaults + perms    (order 40)
│       └── fileassoc.py         # default apps (duti)       (order 47)
├── dotfiles/
│   ├── zshrc  zsh_aliases  inputrc  gitconfig
│   └── config/{zellij,ghostty,karabiner}/…
└── Makefile                     # make setup / update / lint / test / check
```

## Testing

```bash
make check    # shellcheck + py_compile + module discovery + karabiner.json validation
```
