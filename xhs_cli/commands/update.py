"""Self-update command for the CLI and bundled agent skills."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from urllib.error import URLError
from urllib.request import urlopen

import click

from .. import __version__
from ..exceptions import XhsApiError
from ..formatter import console, maybe_print_structured, print_success, success_payload
from ._common import handle_errors, structured_output_options

PACKAGE_NAME = "xhs-cli-headless"
GITHUB_REPO_URL = "https://github.com/kyalpha313/xhs-cli-headless"
GITHUB_INSTALL_SPEC = f"git+{GITHUB_REPO_URL}"


def fetch_latest_version(source: str) -> str | None:
    """Fetch the latest published version for the chosen source."""
    if source == "github":
        return None
    try:
        with urlopen(f"https://pypi.org/pypi/{PACKAGE_NAME}/json", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError):
        return None
    version = payload.get("info", {}).get("version")
    return str(version) if version else None


def detect_install_method() -> str:
    """Best-effort detection of the current installation manager."""
    executable = str(sys.argv[0])
    prefix = sys.prefix.lower()
    executable_lower = executable.lower()

    if "pipx" in prefix or "/pipx/" in executable_lower:
        return "pipx"
    if "/uv/tools/" in prefix or "/uv/tools/" in executable_lower or "\\uv\\tools\\" in executable_lower:
        return "uv"
    if shutil.which("uv"):
        return "uv"
    if shutil.which("pipx"):
        return "pipx"
    return "pip"


def build_update_command(*, source: str, method: str) -> list[str]:
    """Build the update command without executing it."""
    if source == "github":
        if not shutil.which("uv"):
            raise XhsApiError(
                "Updating from GitHub requires uv. Install uv first or use: xhs update --source pypi",
                code="update_unavailable",
            )
        return ["uv", "tool", "install", "--force", GITHUB_INSTALL_SPEC]

    if method == "uv":
        if not shutil.which("uv"):
            raise XhsApiError("uv was selected but is not available on PATH.", code="update_unavailable")
        return ["uv", "tool", "upgrade", PACKAGE_NAME]
    if method == "pipx":
        if not shutil.which("pipx"):
            raise XhsApiError("pipx was selected but is not available on PATH.", code="update_unavailable")
        return ["pipx", "upgrade", PACKAGE_NAME]
    if method == "pip":
        return [sys.executable, "-m", "pip", "install", "--upgrade", PACKAGE_NAME]
    raise XhsApiError(f"Unsupported update method: {method}", code="update_unavailable")


def _command_text(command: list[str]) -> str:
    return " ".join(command)


@click.command("update")
@click.option("--check", is_flag=True, help="Only check whether a newer version is available.")
@click.option("--dry-run", is_flag=True, help="Show the update command without running it.")
@click.option(
    "--source",
    type=click.Choice(["pypi", "github"]),
    default="pypi",
    show_default=True,
    help="Package source to update from.",
)
@structured_output_options
def update(check: bool, dry_run: bool, source: str, as_json: bool, as_yaml: bool):
    """Update xhs CLI and bundled agent skills."""

    def _run():
        method = detect_install_method()
        latest_version = fetch_latest_version(source) if check else None
        update_available = bool(latest_version and latest_version != __version__)

        if check:
            payload = {
                "current_version": __version__,
                "latest_version": latest_version,
                "update_available": update_available,
                "source": source,
                "method": method,
            }
            if not maybe_print_structured(success_payload(payload), as_json=as_json, as_yaml=as_yaml):
                latest = latest_version or "unknown"
                console.print(f"current: {__version__}")
                console.print(f"latest: {latest}")
                console.print(f"update available: {'yes' if update_available else 'no'}")
            return payload

        command = build_update_command(source=source, method=method)
        payload = {
            "current_version": __version__,
            "source": source,
            "method": method,
            "command": command,
            "command_text": _command_text(command),
            "dry_run": dry_run,
        }
        if dry_run:
            if not maybe_print_structured(success_payload(payload), as_json=as_json, as_yaml=as_yaml):
                console.print(_command_text(command))
            return payload

        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as exc:
            raise XhsApiError(
                f"Update command failed with exit code {exc.returncode}: {_command_text(command)}",
                code="update_failed",
            ) from exc
        payload["updated"] = True
        if not maybe_print_structured(success_payload(payload), as_json=as_json, as_yaml=as_yaml):
            print_success("Updated xhs CLI and bundled agent skills.")
        return payload

    return handle_errors(_run, as_json=as_json, as_yaml=as_yaml)
