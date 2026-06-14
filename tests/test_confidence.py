from brew_adoption_audit.confidence import confidence_for
from brew_adoption_audit.models import AppBundle


def make_app(bundle_id="com.microsoft.VSCode", app_store=False):
    return AppBundle(
        name="Code",
        app_bundle="Visual Studio Code.app",
        path="/Applications/Visual Studio Code.app",
        bundle_id=bundle_id,
        version="1.0",
        app_store=app_store,
    )


def test_confidence_app_store():
    assert confidence_for(make_app(app_store=True), "", app_store=True, brew_managed="") == 100


def test_confidence_bundle_mapping_match():
    assert confidence_for(make_app(), "visual-studio-code", app_store=False, brew_managed="") == 95


def test_confidence_verified_without_mapping():
    assert confidence_for(make_app("example.bundle"), "some-cask", app_store=False, brew_managed="") == 85


def test_confidence_none():
    assert confidence_for(make_app(), "", app_store=False, brew_managed="") == 0
