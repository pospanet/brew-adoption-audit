from __future__ import annotations

from typing import Any


def extract_app_artifacts(cask_json: dict[str, Any] | None) -> list[str]:
    if not cask_json:
        return []

    result: list[str] = []
    for cask in cask_json.get("casks", []):
        for artifact in cask.get("artifacts", []):
            if not isinstance(artifact, dict) or "app" not in artifact:
                continue

            app_artifact = artifact["app"]
            if isinstance(app_artifact, list) and app_artifact:
                result.append(str(app_artifact[0]))
            elif isinstance(app_artifact, str):
                result.append(app_artifact)

    return result
