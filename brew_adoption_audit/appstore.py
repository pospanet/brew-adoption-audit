from __future__ import annotations

from pathlib import Path

from .shell import ReadOnlyCommandRunner


def is_app_store_app(runner: ReadOnlyCommandRunner, app_path: Path) -> bool:
    receipt_type = runner.stdout([
        "mdls",
        "-raw",
        "-name",
        "kMDItemAppStoreReceiptType",
        str(app_path),
    ])

    if receipt_type and receipt_type != "(null)":
        return True

    return (app_path / "Contents" / "_MASReceipt" / "receipt").exists()
