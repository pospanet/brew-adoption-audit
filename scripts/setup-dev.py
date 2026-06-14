#!/usr/bin/env python3
from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)


def venv_python() -> Path:
    if platform.system() == "Windows":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def main() -> int:
    if not VENV.exists():
        run([sys.executable, "-m", "venv", str(VENV)])

    py = venv_python()

    run([str(py), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(py), "-m", "pip", "install", "-e", ".[dev]"])

    print()
    print("Development environment ready.")
    print(f"Python: {py}")
    print()
    print("Next:")
    print("  VS Code: Python: Select Interpreter -> .venv")
    print("  Run tests: .venv/bin/pytest or .venv\\Scripts\\pytest.exe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())