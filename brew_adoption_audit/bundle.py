from __future__ import annotations

import plistlib
from pathlib import Path

from .appstore import is_app_store_app
from .models import AppBundle
from .shell import ReadOnlyCommandRunner


def read_info_plist(app_path: Path) -> dict[str, str]:
    plist_path = app_path / "Contents" / "Info.plist"
    try:
        with plist_path.open("rb") as handle:
            data = plistlib.load(handle)
    except Exception:
        return {"name": app_path.stem, "bundle_id": "", "version": ""}

    return {
        "name": str(data.get("CFBundleName") or data.get("CFBundleDisplayName") or app_path.stem),
        "bundle_id": str(data.get("CFBundleIdentifier") or ""),
        "version": str(data.get("CFBundleShortVersionString") or data.get("CFBundleVersion") or ""),
    }


def discover_apps(
    application_dirs: list[Path],
    runner: ReadOnlyCommandRunner,
) -> list[AppBundle]:
    apps: list[AppBundle] = []
    seen_paths: set[str] = set()

    for app_dir in application_dirs:
        if not app_dir.exists() or not app_dir.is_dir():
            continue

        for app_path in sorted(app_dir.glob("*.app")):
            resolved = str(app_path)
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)

            info = read_info_plist(app_path)
            apps.append(
                AppBundle(
                    name=info["name"],
                    app_bundle=app_path.name,
                    path=str(app_path),
                    bundle_id=info["bundle_id"] or "-",
                    version=info["version"] or "-",
                    app_store=is_app_store_app(runner, app_path),
                )
            )

    return apps
