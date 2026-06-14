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
    """Subprocess wrapper for metadata-only commands.

    Homebrew auto-update is disabled for every command.

    IMPORTANT: HOMEBREW_NO_INSTALL_FROM_API MUST NOT be set.
    Homebrew treats the presence of this environment variable as boolean true,
    regardless of its value (even "0" or "false"). Setting it disables the JSON API,
    causing brew info to fail for non-installed casks. We intentionally omit this
    variable to enable API lookups for artifact verification.
    """

    def __init__(self, *, verbose: bool = False) -> None:
        self.verbose = verbose

    def run(self, argv: list[str]) -> CommandResult:
        env = os.environ.copy()
        env["HOMEBREW_NO_AUTO_UPDATE"] = "1"
        # Do NOT set HOMEBREW_NO_INSTALL_FROM_API — see class docstring

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
