#!/usr/bin/env python3
"""
brew-adoption-audit.py

Enterprise-ready read-only audit of macOS applications against Homebrew casks.

Safety contract:
- Does NOT install, adopt, uninstall, upgrade, update, cleanup, move, copy, or delete anything.
- Does NOT mutate /Applications, ~/Library, Homebrew state, or app bundles.
- Uses Homebrew only for metadata reads: brew list/search/info.
- Sets HOMEBREW_NO_AUTO_UPDATE=1 for every brew invocation.

The only write operation this program can perform is writing an explicit report file
when --output is provided by the caller.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import plistlib
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

TOOL_VERSION = "0.2.0"

RECOMMEND_LEAVE_APP_STORE = "LEAVE_APP_STORE"
RECOMMEND_ALREADY_BREW = "ALREADY_BREW"
RECOMMEND_SAFE_TO_ADOPT = "SAFE_TO_ADOPT"
RECOMMEND_MANUAL_REVIEW = "MANUAL_REVIEW"
RECOMMEND_NO_CASK_FOUND = "NO_CASK_FOUND"

# Curated high-confidence mappings. This is intentionally conservative.
# The artifact check still has to pass before SAFE_TO_ADOPT is emitted.
BUNDLE_ID_TO_CASK: dict[str, str] = {
    "com.microsoft.VSCode": "visual-studio-code",
    "com.docker.docker": "docker-desktop",
    "com.googlecode.iterm2": "iterm2",
    "com.raycast.macos": "raycast",
    "com.mikrotik.winbox": "winbox",
    "com.figma.Desktop": "figma",
    "com.obsproject.obs-studio": "obs",
    "com.raspberrypi.rpi-imager": "raspberry-pi-imager",
    "com.raspberrypi.imagingutility": "raspberry-pi-imager",
    "com.microsoft.edgemac": "microsoft-edge",
    "com.microsoft.OneDrive": "onedrive",
    "com.microsoft.teams2": "microsoft-teams",
    "com.parallels.desktop.console": "parallels",
    "com.parallels.toolbox": "parallels-toolbox",
    "com.spotify.client": "spotify",
    "com.openai.chat": "chatgpt",
    "com.openai.atlas": "chatgpt-atlas",
    "com.exafunction.windsurf": "devin-desktop",
    "ai.devin.desktop": "devin-desktop",
    "com.devin.desktop": "devin-desktop",
    "com.windsurf.editor": "windsurf",
    "com.electron.realtimeboard": "miro",
    "com.techsmith.camtasia2024": "camtasia",
}

# Apps that are commonly better left under their vendor's updater even if casks exist.
VENDOR_MANAGED_BUNDLE_PREFIXES = (
    "com.microsoft.Word",
    "com.microsoft.Excel",
    "com.microsoft.Powerpoint",
    "com.microsoft.PowerPoint",
    "com.microsoft.Outlook",
    "com.microsoft.onenote.mac",
    "com.microsoft.wdav",
)


@dataclass(frozen=True)
class AuditRow:
    app_name: str
    app_bundle: str
    path: str
    bundle_id: str
    version: str
    app_store: bool
    brew_managed: str
    verified_cask: str
    possible_casks: str
    artifact_match: bool
    confidence: int
    recommendation: str
    suggested_command: str
    notes: str


class CommandRunner:
    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose

    def run(self, cmd: list[str]) -> str:
        env = os.environ.copy()
        env["HOMEBREW_NO_AUTO_UPDATE"] = "1"
        env["HOMEBREW_NO_INSTALL_FROM_API"] = "0"

        if self.verbose:
            print(f"[read-only] {' '.join(cmd)}", file=sys.stderr)

        try:
            return subprocess.check_output(
                cmd,
                text=True,
                stderr=subprocess.DEVNULL,
                env=env,
            ).strip()
        except Exception:
            return ""


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def read_info_plist(app_path: Path) -> dict[str, str]:
    plist_path = app_path / "Contents" / "Info.plist"
    try:
        with plist_path.open("rb") as handle:
            data = plistlib.load(handle)
        return {
            "name": str(data.get("CFBundleName") or data.get("CFBundleDisplayName") or app_path.stem),
            "bundle_id": str(data.get("CFBundleIdentifier") or ""),
            "version": str(data.get("CFBundleShortVersionString") or data.get("CFBundleVersion") or ""),
        }
    except Exception:
        return {"name": app_path.stem, "bundle_id": "", "version": ""}


def is_app_store_app(runner: CommandRunner, app_path: Path) -> bool:
    receipt_type = runner.run(["mdls", "-raw", "-name", "kMDItemAppStoreReceiptType", str(app_path)])
    if receipt_type and receipt_type != "(null)":
        return True

    # Fallback for cases where Spotlight metadata is missing or stale.
    receipt = app_path / "Contents" / "_MASReceipt" / "receipt"
    return receipt.exists()


def get_installed_casks(runner: CommandRunner) -> set[str]:
    out = runner.run(["brew", "list", "--cask"])
    return {line.strip() for line in out.splitlines() if line.strip()}


def get_all_casks(runner: CommandRunner) -> set[str]:
    out = runner.run(["brew", "search", "--casks"])
    return {line.strip() for line in out.splitlines() if line.strip()}


def get_cask_json(runner: CommandRunner, cask: str) -> dict[str, Any] | None:
    raw = runner.run(["brew", "info", "--json=v2", "--cask", cask])
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def extract_app_artifacts(cask_json: dict[str, Any] | None) -> list[str]:
    if not cask_json:
        return []

    artifacts: list[str] = []
    for cask in cask_json.get("casks", []):
        for artifact in cask.get("artifacts", []):
            if not isinstance(artifact, dict):
                continue
            if "app" not in artifact:
                continue
            app_artifact = artifact["app"]
            if isinstance(app_artifact, list) and app_artifact:
                artifacts.append(str(app_artifact[0]))
            elif isinstance(app_artifact, str):
                artifacts.append(app_artifact)
    return artifacts


def is_vendor_managed(bundle_id: str) -> bool:
    return any(bundle_id.startswith(prefix) for prefix in VENDOR_MANAGED_BUNDLE_PREFIXES)


def candidate_casks(app_name: str, app_bundle: str, bundle_id: str, all_casks: set[str]) -> list[str]:
    candidates: list[str] = []

    mapped = BUNDLE_ID_TO_CASK.get(bundle_id)
    if mapped and mapped in all_casks:
        candidates.append(mapped)

    app_slug = slug(app_name)
    bundle_slug = slug(app_bundle.removesuffix(".app"))

    aliases = {
        app_slug,
        bundle_slug,
        app_slug.replace("code", "visual-studio-code"),
        bundle_slug.replace("visual-studio-code", "visual-studio-code"),
        bundle_slug.replace("docker", "docker-desktop"),
        bundle_slug.replace("iterm", "iterm2"),
        bundle_slug.replace("devin", "devin-desktop"),
    }

    for alias in sorted(a for a in aliases if a):
        if alias in all_casks and alias not in candidates:
            candidates.append(alias)

    for cask in sorted(all_casks):
        if len(candidates) >= 8:
            break
        if app_slug and (cask == app_slug or cask.startswith(app_slug + "-")):
            if cask not in candidates:
                candidates.append(cask)
        elif bundle_slug and (cask == bundle_slug or cask.startswith(bundle_slug + "-")):
            if cask not in candidates:
                candidates.append(cask)

    return candidates


def find_verified_cask(
    runner: CommandRunner,
    app_bundle: str,
    candidates: Iterable[str],
    cask_json_cache: dict[str, dict[str, Any] | None],
) -> str:
    for cask in candidates:
        cask_json = cask_json_cache.setdefault(cask, get_cask_json(runner, cask))
        artifacts = extract_app_artifacts(cask_json)
        if app_bundle in artifacts:
            return cask
    return ""


def detect_brew_managed(
    runner: CommandRunner,
    app_bundle: str,
    installed_casks: set[str],
    cask_json_cache: dict[str, dict[str, Any] | None],
) -> str:
    for cask in sorted(installed_casks):
        cask_json = cask_json_cache.setdefault(cask, get_cask_json(runner, cask))
        artifacts = extract_app_artifacts(cask_json)
        if app_bundle in artifacts:
            return cask
    return ""


def build_row(
    runner: CommandRunner,
    app_path: Path,
    installed_casks: set[str],
    all_casks: set[str],
    cask_json_cache: dict[str, dict[str, Any] | None],
) -> AuditRow:
    plist = read_info_plist(app_path)
    app_name = plist["name"]
    app_bundle = app_path.name
    bundle_id = plist["bundle_id"]
    version = plist["version"]
    app_store = is_app_store_app(runner, app_path)

    possible = candidate_casks(app_name, app_bundle, bundle_id, all_casks)
    brew_managed = detect_brew_managed(runner, app_bundle, installed_casks, cask_json_cache)
    verified = find_verified_cask(runner, app_bundle, possible, cask_json_cache)
    artifact_match = bool(verified)

    notes: list[str] = []
    suggested = ""
    confidence = 0

    if app_store:
        recommendation = RECOMMEND_LEAVE_APP_STORE
        confidence = 100
        notes.append("Installed from Mac App Store; keep App Store as source of updates.")
    elif brew_managed:
        recommendation = RECOMMEND_ALREADY_BREW
        confidence = 100
        notes.append(f"Already managed by Homebrew cask '{brew_managed}'.")
    elif is_vendor_managed(bundle_id):
        recommendation = RECOMMEND_MANUAL_REVIEW
        confidence = 60
        notes.append("Likely vendor-managed application; verify updater/licensing before Brew adoption.")
    elif verified:
        recommendation = RECOMMEND_SAFE_TO_ADOPT
        confidence = 95 if BUNDLE_ID_TO_CASK.get(bundle_id) == verified else 85
        suggested = f"brew install --cask --adopt {verified}"
        notes.append("Homebrew cask artifact matches the installed .app bundle name.")
    elif possible:
        recommendation = RECOMMEND_MANUAL_REVIEW
        confidence = 50
        notes.append("Possible cask found, but artifact match was not verified.")
    else:
        recommendation = RECOMMEND_NO_CASK_FOUND
        confidence = 0
        notes.append("No reliable Homebrew cask candidate found.")

    return AuditRow(
        app_name=app_name or app_path.stem,
        app_bundle=app_bundle,
        path=str(app_path),
        bundle_id=bundle_id or "-",
        version=version or "-",
        app_store=app_store,
        brew_managed=brew_managed or "-",
        verified_cask=verified or "-",
        possible_casks=",".join(possible) if possible else "-",
        artifact_match=artifact_match,
        confidence=confidence,
        recommendation=recommendation,
        suggested_command=suggested,
        notes=" ".join(notes),
    )


def audit(applications_dir: Path, runner: CommandRunner) -> list[AuditRow]:
    installed_casks = get_installed_casks(runner)
    all_casks = get_all_casks(runner)
    cask_json_cache: dict[str, dict[str, Any] | None] = {}

    rows: list[AuditRow] = []
    for app_path in sorted(applications_dir.glob("*.app")):
        rows.append(build_row(runner, app_path, installed_casks, all_casks, cask_json_cache))
    return rows


def truncate(value: Any, width: int) -> str:
    text = str(value)
    if len(text) <= width:
        return text
    return text[: max(width - 1, 0)] + "…"


def print_table(rows: list[AuditRow]) -> None:
    data = [asdict(row) for row in rows]
    headers = [
        "app_name",
        "app_bundle",
        "bundle_id",
        "version",
        "app_store",
        "brew_managed",
        "verified_cask",
        "confidence",
        "recommendation",
    ]
    widths = {h: min(max(len(h), *(len(str(row[h])) for row in data)), 36) for h in headers}

    print("  ".join(h.ljust(widths[h]) for h in headers))
    print("  ".join(("-" * widths[h]) for h in headers))
    for row in data:
        print("  ".join(truncate(row[h], widths[h]).ljust(widths[h]) for h in headers))

    safe = [row for row in rows if row.recommendation == RECOMMEND_SAFE_TO_ADOPT]
    manual = [row for row in rows if row.recommendation == RECOMMEND_MANUAL_REVIEW]

    if safe:
        print("\nSafe-to-adopt candidates — commands are printed only, not executed:")
        for row in safe:
            print(f"  {row.suggested_command}    # {row.app_name}")

    if manual:
        print("\nManual review:")
        for row in manual:
            print(f"  {row.app_name}: {row.notes}")


def emit_json(rows: list[AuditRow]) -> str:
    return json.dumps([asdict(row) for row in rows], indent=2, ensure_ascii=False)


def emit_csv(rows: list[AuditRow]) -> str:
    import io

    buffer = io.StringIO()
    fieldnames = list(asdict(rows[0]).keys()) if rows else []
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(asdict(row) for row in rows)
    return buffer.getvalue()


def emit_markdown(rows: list[AuditRow]) -> str:
    data = [asdict(row) for row in rows]
    if not data:
        return ""
    headers = list(data[0].keys())
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in data:
        lines.append("| " + " | ".join(str(row[h]).replace("|", "\\|") for h in headers) + " |")
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only audit of macOS apps against Homebrew casks.")
    parser.add_argument("--applications-dir", default="/Applications", help="Directory containing .app bundles. Default: /Applications")
    parser.add_argument("--format", choices=("table", "json", "csv", "markdown"), default="table", help="Output format. Default: table")
    parser.add_argument("--output", help="Optional report output path. This is the only supported write operation.")
    parser.add_argument("--verbose", action="store_true", help="Print read-only commands to stderr.")
    parser.add_argument("--version", action="version", version=f"brew-adoption-audit {TOOL_VERSION}")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    applications_dir = Path(args.applications_dir)

    if not applications_dir.exists() or not applications_dir.is_dir():
        print(f"ERROR: applications directory not found: {applications_dir}", file=sys.stderr)
        return 2

    runner = CommandRunner(verbose=args.verbose)
    if not runner.run(["which", "brew"]):
        print("ERROR: Homebrew not found in PATH.", file=sys.stderr)
        return 2

    rows = audit(applications_dir, runner)

    if args.format == "table":
        output = ""
        print_table(rows)
    elif args.format == "json":
        output = emit_json(rows)
    elif args.format == "csv":
        output = emit_csv(rows)
    elif args.format == "markdown":
        output = emit_markdown(rows)
    else:
        raise AssertionError(args.format)

    if args.format != "table":
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"Audit report written to: {args.output}")
        else:
            print(output, end="")

    print("\nNo system changes were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
