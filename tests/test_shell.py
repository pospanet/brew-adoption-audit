from unittest.mock import patch

from brew_adoption_audit.shell import ReadOnlyCommandRunner


def test_runner_env_has_homebrew_no_auto_update():
    """Verify HOMEBREW_NO_AUTO_UPDATE is set to disable auto-update."""
    runner = ReadOnlyCommandRunner()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.__class__.__enter__ = lambda self: self
        mock_run.return_value.__class__.__exit__ = lambda self, *args: None
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""

        runner.run(["brew", "info"])

        call_kwargs = mock_run.call_args.kwargs
        assert "env" in call_kwargs
        assert call_kwargs["env"]["HOMEBREW_NO_AUTO_UPDATE"] == "1"


def test_runner_env_does_not_set_homebrew_no_install_from_api():
    """Verify HOMEBREW_NO_INSTALL_FROM_API is NOT set.
    
    Homebrew treats the presence of this variable as boolean true,
    regardless of value. Setting it (even to "0") disables the JSON API.
    This test ensures the root cause bug cannot be reintroduced.
    """
    runner = ReadOnlyCommandRunner()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.__class__.__enter__ = lambda self: self
        mock_run.return_value.__class__.__exit__ = lambda self, *args: None
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""

        runner.run(["brew", "info"])

        call_kwargs = mock_run.call_args.kwargs
        assert "env" in call_kwargs
        assert "HOMEBREW_NO_INSTALL_FROM_API" not in call_kwargs["env"]
