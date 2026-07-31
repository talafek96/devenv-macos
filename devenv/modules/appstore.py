"""Mac App Store apps (installed via `mas`).

Some apps aren't on Homebrew — e.g. Pixea, the image viewer we set as the
default for photos. Those come from the Mac App Store via `mas`.

Requires being signed in to the App Store. NOTE: `mas install` can only
*re-download* apps already associated with your Apple ID — it cannot do a
first-time acquisition of an app you've never "gotten". A brand-new app fails
with "Redownload is unavailable with this account"; you must open its App Store
page once and click Get/Install (that both installs it and ties it to your
account). After that `mas` manages it fine.

This module never fails the setup over a missing App Store app: when it can't
auto-install one, it PROMPTS you (open the App Store / retry / skip) on an
interactive run, and just prints the link and moves on when non-interactive.
"""

import os

from devenv.modules import Module

# Display name -> App Store numeric id (the `id=...` in its App Store URL).
APP_STORE_APPS = {
    "Pixea": "1507782672",   # modern image / media viewer (jpg, png, heic, webp, raw)
}


def _app_store_url(app_id: str) -> str:
    """Direct link that opens the app's page in the App Store app."""
    return f"macappstore://apps.apple.com/app/id{app_id}"


class AppStoreModule(Module):
    name = "appstore"
    description = "Install Mac App Store apps (via mas)"
    order = 16  # right after casks, before dotfiles/fileassoc

    def run(self, ctx) -> None:
        if not APP_STORE_APPS:
            return
        if not ctx.has_command("mas"):
            ctx.warn("mas not found — skipping App Store apps "
                     "(install it with `brew install mas`, then re-run).")
            return

        installed_ids = self._installed_ids(ctx)
        for name, app_id in APP_STORE_APPS.items():
            if app_id in installed_ids:
                ctx.ok(f"{name} already installed")
                continue
            ctx.info(f"Installing {name} from the App Store (id {app_id})...")
            if ctx.run("mas", "install", app_id, check=False).returncode == 0:
                ctx.ok(f"Installed {name}")
            else:
                # First-time acquisition isn't possible via mas — hand it off to
                # the user (or note it and move on when non-interactive).
                self._handle_manual_get(ctx, name, app_id)

    # `mas list` prints "<id>  <Name>  (<version>)" per installed app.
    def _installed_ids(self, ctx) -> set[str]:
        return {
            line.split()[0]
            for line in ctx.command_output("mas", "list").splitlines()
            if line.strip()
        }

    def _handle_manual_get(self, ctx, name: str, app_id: str) -> None:
        url = _app_store_url(app_id)
        ctx.warn(f"{name} needs a one-time manual install: Apple blocks first-time "
                 "`mas` installs, so you must \"Get\" it once from the App Store "
                 "(if you saw \"Redownload is unavailable with this account\", "
                 "that's this).")

        # Non-interactive (e.g. the curl one-liner / CI): don't block on input.
        if not os.isatty(0):
            ctx.info(f'    Get it here, then re-run setup:  open "{url}"')
            return

        # Interactive: let the user open the page, retry, or skip.
        while True:
            try:
                choice = input(
                    f"    {name}: [o]pen in App Store · [r]etry install · "
                    "[s]kip (default: skip) > "
                ).strip().lower()
            except EOFError:
                choice = "s"

            if choice in ("", "s", "skip"):
                ctx.warn(f"Skipped {name}. Re-run setup after installing it to "
                         "finish (its file associations will be set then).")
                return
            if choice in ("o", "open", "get"):
                ctx.run("open", url, check=False)
                ctx.info("    Click \"Get\" in the App Store, then come back and "
                         "choose [r] to continue.")
                continue
            if choice in ("r", "retry"):
                # A GUI "Get" already installs the app, so re-check presence too.
                if (app_id in self._installed_ids(ctx)
                        or ctx.run("mas", "install", app_id, check=False).returncode == 0):
                    ctx.ok(f"{name} is installed.")
                    return
                ctx.warn(f"{name} still isn't available — \"Get\" it in the App "
                         "Store first, then choose [r] again.")
                continue
            ctx.info("    Please enter o, r, or s.")
