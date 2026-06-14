from brew_adoption_audit.models import AppBundle, Recommendation
from brew_adoption_audit.recommendation import recommend


def app(**kwargs):
    base = dict(
        name="Code",
        app_bundle="Visual Studio Code.app",
        path="/Applications/Visual Studio Code.app",
        bundle_id="com.microsoft.VSCode",
        version="1.0",
        app_store=False,
    )
    base.update(kwargs)
    return AppBundle(**base)


def test_leave_app_store():
    rec, command, notes = recommend(app(app_store=True), brew_managed="", verified_cask="", possible_casks=[])
    assert rec == Recommendation.LEAVE_APP_STORE
    assert command == ""
    assert "App Store" in notes


def test_already_brew():
    rec, command, notes = recommend(app(), brew_managed="visual-studio-code", verified_cask="", possible_casks=[])
    assert rec == Recommendation.ALREADY_BREW
    assert command == ""


def test_safe_to_adopt():
    rec, command, notes = recommend(
        app(),
        brew_managed="",
        verified_cask="visual-studio-code",
        possible_casks=["visual-studio-code"],
    )
    assert rec == Recommendation.SAFE_TO_ADOPT
    assert command == "brew install --cask --adopt visual-studio-code"


def test_manual_review_for_unverified_possible_cask():
    rec, command, notes = recommend(app(), brew_managed="", verified_cask="", possible_casks=["code"])
    assert rec == Recommendation.MANUAL_REVIEW
    assert command == ""
