from __future__ import annotations

from .aliases import BUNDLE_ID_TO_CASK
from .models import AppBundle


def confidence_for(app: AppBundle, verified_cask: str, *, app_store: bool, brew_managed: str) -> int:
    if app_store or brew_managed:
        return 100
    if not verified_cask:
        return 0
    if BUNDLE_ID_TO_CASK.get(app.bundle_id) == verified_cask:
        return 95
    return 85
