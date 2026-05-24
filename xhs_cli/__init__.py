"""xhs-cli-headless: Xiaohongshu CLI via reverse-engineered API."""

from pathlib import Path

import tomllib


def _source_version() -> str | None:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    try:
        data = tomllib.loads(pyproject.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return None
    version_value = data.get("project", {}).get("version")
    return str(version_value) if version_value else None


try:
    from importlib.metadata import version

    __version__ = _source_version() or version("xhs-cli-headless")
except Exception:
    __version__ = _source_version() or "0.0.0"
