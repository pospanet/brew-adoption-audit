from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class ReadOnlyCommandRunner:
    """Small subprocess wrapper with Homebrew auto-update disabled.

    The runner is intentionally generic, but the project only uses it for read-only
    commands such as `which`, `mdls`, `brew list`, `brew search`, and `brew info`.
    """

    def __init__(self, *, verbose: bool = False) -> None:
        self.verbose = verbose

    def run(self, argv: list[str]) -> CommandResult:
        env = os.environ.copy()
        env["HOMEBREW_NO_AUTO_UPDATE"] = "1"
        env["HOMEBREW_NO_INSTALL_FROM_API"] = "0"

        if self.verbose:
            print("[read-only] " + " ".join(argv), file=sys.stderr)

        proc = subprocess.run(
            argv,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=env,
        )
        return CommandResult(tuple(argv), proc.returncode, proc.stdout.strip(), proc.stderr.strip())

    def stdout(self, argv: list[str]) -> str:
        result = self.run(argv)
        return result.stdout if result.returncode == 0 else ""
