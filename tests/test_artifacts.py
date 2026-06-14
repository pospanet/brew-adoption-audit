from brew_adoption_audit.artifacts import extract_app_artifacts


def test_extract_app_artifacts_from_brew_json():
    payload = {
        "casks": [
            {
                "artifacts": [
                    {"app": ["Visual Studio Code.app"]},
                    {"binary": ["code"]},
                    {"app": "Raycast.app"},
                ]
            }
        ]
    }

    assert extract_app_artifacts(payload) == ["Visual Studio Code.app", "Raycast.app"]


def test_extract_app_artifacts_handles_none():
    assert extract_app_artifacts(None) == []


def test_extract_app_artifacts_real_brew_schema():
    payload = {
        "casks": [
            {
                "artifacts": [
                    {
                        "uninstall": [
                            {
                                "launchctl": "com.microsoft.VSCode.ShipIt"
                            }
                        ]
                    },
                    {
                        "app": [
                            "Visual Studio Code.app"
                        ],
                        "target": "/Applications/Visual Studio Code.app"
                    },
                    {
                        "binary": [
                            "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
                        ]
                    },
                    {
                        "zap": [
                            {
                                "trash": [
                                    "~/.vscode"
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    assert "Visual Studio Code.app" in extract_app_artifacts(payload)


def test_extract_app_artifacts_pkg_only_cask_has_no_app():
    payload = {
        "casks": [
            {
                "artifacts": [
                    {
                        "uninstall": [
                            {
                                "delete": [
                                    "/Applications/OneDrive.app"
                                ]
                            }
                        ]
                    },
                    {
                        "pkg": [
                            "OneDrive.pkg"
                        ]
                    },
                    {
                        "zap": [
                            {
                                "trash": [
                                    "~/Library/Caches/com.microsoft.OneDrive"
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    assert extract_app_artifacts(payload) == []


def test_extract_app_artifacts_empty_app_list():
    """Empty app list should not add anything to result."""
    payload = {"casks": [{"artifacts": [{"app": []}]}]}
    assert extract_app_artifacts(payload) == []


def test_extract_app_artifacts_multi_element_app_list():
    """When app is a list with multiple elements, only the first is used."""
    payload = {"casks": [{"artifacts": [{"app": ["A.app", "B.app"]}]}]}
    assert extract_app_artifacts(payload) == ["A.app"]


def test_extract_app_artifacts_multiple_casks():
    """Artifacts from multiple casks should be aggregated."""
    payload = {
        "casks": [
            {
                "artifacts": [
                    {"app": ["A.app"]}
                ]
            },
            {
                "artifacts": [
                    {"app": ["B.app"]}
                ]
            }
        ]
    }
    assert extract_app_artifacts(payload) == ["A.app", "B.app"]


def test_extract_app_artifacts_target_rename():
    """Documents current behavior: only source app name is extracted, not target.
    
    If a cask uses target: to rename an app during installation, the parser
    returns only the source name. This is a documented limitation.
    """
    payload = {
        "casks": [
            {
                "artifacts": [
                    {
                        "app": ["Source.app"],
                        "target": "/Applications/Renamed.app"
                    }
                ]
            }
        ]
    }
    assert extract_app_artifacts(payload) == ["Source.app"]
