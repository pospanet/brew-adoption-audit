from __future__ import annotations

import json
import re
from typing import Any

from .aliases import BUNDLE_ID_TO_CASK
from .artifacts import extract_app_artifacts
from .models import AppBundle
from .shell import ReadOnlyCommandRunner


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


class BrewMetadata:
    def __init__(self, runner: ReadOnlyCommandRunner) -> None:
        self.runner = runner
        self._installed_casks: set[str] | None = None
        self._all_casks: set[str] | None = None
        self._cask_json: dict[str, dict[str, Any] | None] = {}

    def installed_casks(self) -> set[str]:
        if self._installed_casks is None:
            out = self.runner.stdout(["brew", "list", "--cask"])
            self._installed_casks = {line.strip() for line in out.splitlines() if line.strip()}
        return self._installed_casks

    def all_casks(self) -> set[str]:
        if self._all_casks is None:
            out = self.runner.stdout(["brew", "search", "--casks"])
            self._all_casks = {line.strip() for line in out.splitlines() if line.strip()}
        return self._all_casks

    def cask_json(self, cask: str) -> dict[str, Any] | None:
        if cask not in self._cask_json:
            raw = self.runner.stdout(["brew", "info", "--json=v2", "--cask", cask])
            try:
                self._cask_json[cask] = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                self._cask_json[cask] = None
        return self._cask_json[cask]

    def app_artifacts(self, cask: str) -> list[str]:
        return extract_app_artifacts(self.cask_json(cask))

    def brew_managed_cask(self, app_bundle: str) -> str:
        for cask in sorted(self.installed_casks()):
            if app_bundle in self.app_artifacts(cask):
                return cask
        return ""

    def candidates_for(self, app: AppBundle) -> list[str]:
        all_casks = self.all_casks()
        candidates: list[str] = []

        mapped = BUNDLE_ID_TO_CASK.get(app.bundle_id)
        if mapped:
            candidates.append(mapped)

        name_slug = slug(app.name)
        bundle_slug = slug(app.app_bundle.removesuffix(".app"))

        aliases = {
            name_slug,
            bundle_slug,
            name_slug.replace("code", "visual-studio-code"),
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
            if name_slug and (cask == name_slug or cask.startswith(name_slug + "-")):
                if cask not in candidates:
                    candidates.append(cask)
            elif bundle_slug and (cask == bundle_slug or cask.startswith(bundle_slug + "-")):
                if cask not in candidates:
                    candidates.append(cask)

        return candidates

    def verified_cask_for(self, app: AppBundle, candidates: list[str]) -> str:
        for cask in candidates:
            if app.app_bundle in self.app_artifacts(cask):
                return cask
        return ""
