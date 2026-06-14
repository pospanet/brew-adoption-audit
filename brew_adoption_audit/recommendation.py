from __future__ import annotations

from .aliases import is_vendor_managed
from .models import AppBundle, Recommendation


def recommend(
    app: AppBundle,
    *,
    brew_managed: str,
    verified_cask: str,
    possible_casks: list[str],
) -> tuple[Recommendation, str, str]:
    if app.app_store:
        return (
            Recommendation.LEAVE_APP_STORE,
            "",
            "Installed from Mac App Store; keep App Store as update source.",
        )

    if brew_managed:
        return (
            Recommendation.ALREADY_BREW,
            "",
            f"Already managed by Homebrew cask '{brew_managed}'.",
        )

    if is_vendor_managed(app.bundle_id):
        return (
            Recommendation.MANUAL_REVIEW,
            "",
            "Likely vendor-managed application; verify licensing/updater before Brew adoption.",
        )

    if verified_cask:
        return (
            Recommendation.SAFE_TO_ADOPT,
            f"brew install --cask --adopt {verified_cask}",
            "Homebrew cask artifact matches the installed .app bundle name.",
        )

    if possible_casks:
        return (
            Recommendation.MANUAL_REVIEW,
            "",
            "Possible cask found, but artifact match was not verified.",
        )

    return (
        Recommendation.NO_CASK_FOUND,
        "",
        "No reliable Homebrew cask candidate found.",
    )
