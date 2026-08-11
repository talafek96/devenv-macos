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
`google-chrome`, `whatsapp`, `transmission`, `vlc`, `macdroid`,
`adobe-acrobat-reader`.
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
clipboard — the Windows key sits where Option is on a Mac) and installing a
LaunchAgent so **Maccy starts at login** (a global hotkey is dead if its app
isn't running — installing the cask alone doesn't auto-launch it), binding
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

When opted in (or if CleanShot X is already installed), the `keybinds` module:
- **Disables all native macOS screenshot shortcuts** in prefs so they don't
  collide with CleanShot's (this satisfies the "turn these off" dialog CleanShot
  pops on first launch — it reads the same prefs — so you can just dismiss it;
  macOS itself only drops the old chords after a logout/restart).
- **Sets CleanShot's "Capture Area" shortcut to `Option+Shift+S`** and turns on
  its **screen-freeze** (`freezeScreen`) so you can frame the shot while paused —
  each written only if you haven't already set it, so a custom choice is never
  stomped. (Reverse-engineered from CleanShot 4.8.10: `LAVAtakeArea` +
  `freezeScreen` prefs, read at launch.) Restart CleanShot X once to pick them up.
- **Prints a checklist** to activate your license (and set the shortcut by hand
  if the pref format ever moves between CleanShot versions).

All of the above — the shortcut, the freeze default, *and* disabling the native
screenshot shortcuts — apply **only** when CleanShot X is opted in or already
installed. Without it, `keybinds` uses the native fallback and never touches
CleanShot's prefs.

Enable both opt-in flags together if you want them:

```bash
DEVENV_KARABINER=1 DEVENV_CLEANSHOT=1 ./setup.sh
```

### Claude Code assets are opt-in

The repo ships a default set of [Claude Code](https://claude.com/claude-code)
agents, skills, and slash commands under `devenv/assets/claude/`. The `claude`
module links them into `~/.claude/` so a fresh machine gets the same agent setup,
and `git pull` keeps them current. It is **opt-in**:

```bash
DEVENV_CLAUDE_ASSETS=1 ./setup.sh                # full setup, with the Claude assets
DEVENV_CLAUDE_ASSETS=1 ./setup.sh --only claude  # just link the assets
```

What gets linked:

- **Agents** — `prior-art-researcher` (iterative prior-art research for design
  and architecture questions) and `query-librarian` (compacts the researcher's
  accumulated query lessons into a ranked playbook).
- **Skills** — `prior-art`, `duckduckgo-search`, `web-scraper` (the
  researcher agent routes all its fetching through these three, so they belong
  wherever the agent lives), plus `claude-md-standards`, `explain-with-trees`,
  `reconcile-docs`, and `resume-remote-handoff`.
- **Commands** — `/end-session` (wind-down ritual) and `/shift-handoff`
  (compaction prompt for the next session).

It's opt-in because `~/.claude/` is a directory Claude Code owns and that people
customize by hand — an unrelated setup run shouldn't change your agent setup.
Each asset is linked **individually** rather than linking the parent
directories, so your own agents and skills sitting alongside these are left
alone. Anything already at a target path is backed up to
`<name>.devenv-backup.<timestamp>` before the symlink replaces it, same as the
dotfiles module. Re-running is a no-op once linked.

**Opting back out.** Set the flag to `uninstall` (`remove` and `unlink` also
work) to remove the links:

```bash
DEVENV_CLAUDE_ASSETS=uninstall ./setup.sh --only claude
```

Note the asymmetry, which is deliberate: **unsetting** the flag stops managing
the assets and leaves them in place (same convention as the Karabiner keymap);
only an explicit `uninstall` removes them. That way a missing env var — in a
fresh shell, a cron job, a CI run — can never silently tear down your agent
setup.

Uninstall is as conservative as install. It removes **only** symlinks that point
into this repo's `devenv/assets/claude/`; a real file or directory you put at one
of those paths, or a symlink pointing somewhere else, is reported and left
untouched. Backups from the original install are not restored automatically —
they stay as `*.devenv-backup.*` for you to restore or delete. Re-running the
uninstall is a no-op.

The `duckduckgo-search` and `web-scraper` skills run as `uv` scripts with
[PEP 723](https://peps.python.org/pep-0723/) inline dependencies — the `tools`
module already installs `uv`, so they need no separate setup.

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
DEVENV_CLAUDE_ASSETS=1 ./setup.sh  # full setup + Claude Code agents/skills/commands
DEVENV_CLAUDE_ASSETS=uninstall ./setup.sh --only claude   # remove those links again
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
