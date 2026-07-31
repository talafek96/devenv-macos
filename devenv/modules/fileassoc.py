"""Default apps for file types (via `duti`).

Maps file extensions to the app that should open them (double-click + "Open").
Idempotent: duti just re-asserts each LaunchServices binding on every run.

Two wrinkles this module handles:
  * Right after an app is installed, LaunchServices is still registering the
    types it claims, so `duti -s` can return success WITHOUT the binding
    sticking. We therefore VERIFY each set with `duti -x` and retry once.
  * Only extensions the target app actually claims are listed — setting an app
    as the handler for a type it can't open would just yield "open" errors.
"""

from devenv.modules import Module

# App bundle id -> extensions it should become the default handler for.
# (Pixea's claimed types, per its Info.plist / LaunchServices registration.)
DEFAULT_APPS: dict[str, list[str]] = {
    "imagetasks.Pixea": [
        "jpg", "jpeg", "png", "heic", "heif", "webp",
        # RAW — Nikon (.nef) first, then the other vendors Pixea supports.
        "nef",                          # Nikon
        "cr2", "cr3", "crw",            # Canon
        "arw", "sr2",                   # Sony
        "dng",                          # Adobe / generic
        "raf",                          # Fujifilm
        "orf",                          # Olympus
        "erf",                          # Epson
        "mrw",                          # Minolta
        "rwl",                          # Leica
        "3fr",                          # Hasselblad
    ],
}


class FileAssocModule(Module):
    name = "fileassoc"
    description = "Set default apps for file types (Pixea for images, via duti)"
    order = 47  # after installs (casks=15, appstore=16) and keybinds

    def run(self, ctx) -> None:
        if not ctx.has_command("duti"):
            ctx.warn("duti not found — skipping file associations "
                     "(install it with `brew install duti`).")
            return

        for bundle_id, exts in DEFAULT_APPS.items():
            if not self._app_registered(ctx, bundle_id):
                ctx.warn(f"{bundle_id} not installed/registered — skipping its "
                         "file associations (re-run after it's installed).")
                continue

            failed = [ext for ext in exts if not self._set_default(ctx, bundle_id, ext)]
            ok = len(exts) - len(failed)
            ctx.ok(f"{bundle_id}: default for {ok}/{len(exts)} extensions")
            if failed:
                ctx.warn(f"  could not set: {', '.join(failed)} "
                         "(unclaimed type or LaunchServices lag — a re-run may fix it)")

    # Set the handler and confirm it actually took; retry once for LS lag.
    def _set_default(self, ctx, bundle_id: str, ext: str) -> bool:
        for attempt in (1, 2):
            ctx.run("duti", "-s", bundle_id, ext, "all", check=False)
            if self._current_handler(ctx, ext) == bundle_id:
                return True
        return False

    # `duti -x <ext>` prints: app name / app path / bundle id — id is line 3.
    def _current_handler(self, ctx, ext: str) -> str:
        out = ctx.command_output("duti", "-x", ext).splitlines()
        return out[2].strip() if len(out) >= 3 else ""

    def _app_registered(self, ctx, bundle_id: str) -> bool:
        """True if LaunchServices/Spotlight can resolve the app by bundle id."""
        return bool(ctx.command_output(
            "mdfind", f"kMDItemCFBundleIdentifier == '{bundle_id}'"
        ))
