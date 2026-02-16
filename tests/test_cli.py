"""Tests for the CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from wfm.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


class TestCLI:
    def test_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "WFM Block" in result.output

    def test_status_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0
        assert "Show all APs" in result.output

    def test_recheck_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["recheck", "--help"])
        assert result.exit_code == 0
        assert "Re-run SSID mismatch check" in result.output

    def test_setup_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["setup", "--help"])
        assert result.exit_code == 0
        assert "Re-run credential" in result.output

    def test_setup_prompts(self, runner: CliRunner, tmp_path: Path) -> None:
        """Setup command should prompt for credentials."""
        with patch("wfm.cli.KEY_PATH", tmp_path / ".env.key"), \
             patch("wfm.cli.ENV_PATH", tmp_path / ".env"):
            result = runner.invoke(
                cli,
                ["setup"],
                input="admin\npassword123\n192.168.1.1\n",
            )
            assert result.exit_code == 0
            assert "Setup complete" in result.output
