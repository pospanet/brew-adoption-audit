from __future__ import annotations

from pathlib import Path

from .brew import BrewMetadata
from .bundle import discover_apps
from .confidence import confidence_for
from .models import AuditResult
from .recommendation import recommend
from .shell import ReadOnlyCommandRunner


def run_audit(
    application_dirs: list[Path],
    *,
    verbose: bool = False,
) -> list[AuditResult]:
    runner = ReadOnlyCommandRunner(verbose=verbose)
    brew = BrewMetadata(runner)
    apps = discover_apps(application_dirs, runner)

    results: list[AuditResult] = []

    for app in apps:
        brew_managed = brew.brew_managed_cask(app.app_bundle)
        candidates = brew.candidates_for(app)
        verified = brew.verified_cask_for(app, candidates)
        recommendation, command_preview, notes = recommend(
            app,
            brew_managed=brew_managed,
            verified_cask=verified,
            possible_casks=candidates,
        )

        results.append(
            AuditResult(
                app_name=app.name,
                app_bundle=app.app_bundle,
                path=app.path,
                bundle_id=app.bundle_id,
                version=app.version,
                app_store=app.app_store,
                brew_managed=brew_managed or "-",
                verified_cask=verified or "-",
                possible_casks=",".join(candidates) if candidates else "-",
                artifact_match=bool(verified),
                confidence=confidence_for(
                    app,
                    verified,
                    app_store=app.app_store,
                    brew_managed=brew_managed,
                ),
                recommendation=recommendation,
                command_preview=command_preview,
                notes=notes,
            )
        )

    return results
