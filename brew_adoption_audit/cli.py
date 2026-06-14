from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .audit import run_audit
from .reporting import print_table, to_csv, to_html, to_json, to_markdown
from .shell import ReadOnlyCommandRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only audit of macOS applications against Homebrew casks."
    )
    parser.add_argument(
        "--applications-dir",
        action="append",
        default=None,
        help="Directory containing .app bundles. Can be repeated. Default: /Applications",
    )
    parser.add_argument(
        "--include-user-applications",
        action="store_true",
        help="Also audit ~/Applications.",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json", "csv", "markdown", "html"),
        default="table",
        help="Output format. Default: table",
    )
    parser.add_argument(
        "--output",
        help="Optional report output path. This is the only supported write operation.",
    )
    parser.add_argument("--verbose", action="store_true", help="Print read-only commands to stderr.")
    parser.add_argument("--version", action="version", version=f"brew-adoption-audit {__version__}")
    return parser


def application_dirs_from_args(args: argparse.Namespace) -> list[Path]:
    dirs = [Path(p) for p in args.applications_dir] if args.applications_dir else [Path("/Applications")]
    if args.include_user_applications:
        dirs.append(Path.home() / "Applications")
    return dirs


def render(rows, fmt: str) -> str:
    if fmt == "json":
        return to_json(rows)
    if fmt == "csv":
        return to_csv(rows)
    if fmt == "markdown":
        return to_markdown(rows)
    if fmt == "html":
        return to_html(rows)
    raise ValueError(fmt)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    runner = ReadOnlyCommandRunner(verbose=args.verbose)
    if not runner.stdout(["which", "brew"]):
        print("ERROR: Homebrew not found in PATH.", file=sys.stderr)
        return 2

    rows = run_audit(application_dirs_from_args(args), verbose=args.verbose)

    if args.format == "table":
        print_table(rows)
    else:
        output = render(rows, args.format)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"Audit report written to: {args.output}")
        else:
            print(output, end="")

    print("\nNo system changes were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
