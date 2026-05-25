"""Tests for the self-update command."""

import subprocess

from click.testing import CliRunner

from xhs_cli.cli import cli

runner = CliRunner()


def test_update_help_is_registered():
    result = runner.invoke(cli, ["update", "--help"])

    assert result.exit_code == 0
    assert "--check" in result.output
    assert "--dry-run" in result.output


def test_update_check_json_reports_current_and_latest(monkeypatch):
    monkeypatch.setattr("xhs_cli.commands.update.fetch_latest_version", lambda source: "0.8.8")

    result = runner.invoke(cli, ["update", "--check", "--json"])

    assert result.exit_code == 0
    assert '"current_version": "0.8.7"' in result.output
    assert '"latest_version": "0.8.8"' in result.output
    assert '"update_available": true' in result.output


def test_update_dry_run_prefers_detected_uv_tool(monkeypatch):
    monkeypatch.setattr("xhs_cli.commands.update.detect_install_method", lambda: "uv")
    monkeypatch.setattr("xhs_cli.commands.update.shutil.which", lambda name: f"/usr/bin/{name}")

    result = runner.invoke(cli, ["update", "--dry-run", "--json"])

    assert result.exit_code == 0
    assert '"method": "uv"' in result.output
    assert "uv tool upgrade xhs-cli-headless" in result.output


def test_update_source_github_uses_git_install_command(monkeypatch):
    monkeypatch.setattr("xhs_cli.commands.update.detect_install_method", lambda: "pip")
    monkeypatch.setattr("xhs_cli.commands.update.shutil.which", lambda name: f"/usr/bin/{name}")

    result = runner.invoke(cli, ["update", "--dry-run", "--source", "github", "--json"])

    assert result.exit_code == 0
    assert '"source": "github"' in result.output
    assert "uv tool install --force git+https://github.com/kyalpha313/xhs-cli-headless" in result.output


def test_update_fails_when_required_runner_is_missing(monkeypatch):
    monkeypatch.setattr("xhs_cli.commands.update.detect_install_method", lambda: "uv")
    monkeypatch.setattr("xhs_cli.commands.update.shutil.which", lambda _name: None)

    result = runner.invoke(cli, ["update", "--dry-run", "--json"])

    assert result.exit_code == 1
    assert '"code": "update_unavailable"' in result.output


def test_update_reports_subprocess_failure_as_structured_error(monkeypatch):
    monkeypatch.setattr("xhs_cli.commands.update.detect_install_method", lambda: "uv")
    monkeypatch.setattr("xhs_cli.commands.update.shutil.which", lambda name: f"/usr/bin/{name}")

    def fail_run(command, check):
        raise subprocess.CalledProcessError(2, command)

    monkeypatch.setattr("xhs_cli.commands.update.subprocess.run", fail_run)

    result = runner.invoke(cli, ["update", "--json"])

    assert result.exit_code == 1
    assert '"code": "update_failed"' in result.output
