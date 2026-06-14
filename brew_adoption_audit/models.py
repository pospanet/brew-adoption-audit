from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Recommendation(StrEnum):
    LEAVE_APP_STORE = "LEAVE_APP_STORE"
    ALREADY_BREW = "ALREADY_BREW"
    SAFE_TO_ADOPT = "SAFE_TO_ADOPT"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    NO_CASK_FOUND = "NO_CASK_FOUND"


@dataclass(frozen=True)
class AppBundle:
    name: str
    app_bundle: str
    path: str
    bundle_id: str
    version: str
    app_store: bool


@dataclass(frozen=True)
class AuditResult:
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
    recommendation: Recommendation
    command_preview: str
    notes: str
