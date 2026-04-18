"""xhs-cli-headless: Xiaohongshu CLI via reverse-engineered API."""

try:
    from importlib.metadata import version

    __version__ = version("xhs-cli-headless")
except Exception:
    __version__ = "0.0.0"
