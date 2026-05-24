"""xhs-cli-headless: Xiaohongshu CLI via reverse-engineered API."""

import re
from pathlib import Path


def _source_version() -> str | None:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    try:
        text = pyproject.read_text()
    except OSError:
        return None
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', text)
    return match.group(1) if match else None


try:
    from importlib.metadata import version

    __version__ = _source_version() or version("xhs-cli-headless")
except Exception:
    __version__ = _source_version() or "0.0.0"
