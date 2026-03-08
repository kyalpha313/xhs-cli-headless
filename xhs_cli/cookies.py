"""Cookie extraction and management for XHS API client."""

import json
import logging
import subprocess
import sys
from pathlib import Path

from .constants import CONFIG_DIR_NAME, COOKIE_FILE

logger = logging.getLogger(__name__)


def get_config_dir() -> Path:
    """Get or create config directory."""
    config_dir = Path.home() / CONFIG_DIR_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_cookie_path() -> Path:
    """Get cookie file path."""
    return get_config_dir() / COOKIE_FILE


def load_saved_cookies() -> dict[str, str] | None:
    """Load cookies from local storage."""
    cookie_path = get_cookie_path()
    if not cookie_path.exists():
        return None
    try:
        data = json.loads(cookie_path.read_text())
        if data.get("a1"):
            logger.debug("Loaded saved cookies from %s", cookie_path)
            return data
    except (OSError, json.JSONDecodeError) as e:
        logger.debug("Failed to load saved cookies: %s", e)
    return None


def save_cookies(cookies: dict[str, str]) -> None:
    """Save cookies to local storage with restricted permissions."""
    cookie_path = get_cookie_path()
    cookie_path.write_text(json.dumps(cookies, indent=2))
    cookie_path.chmod(0o600)
    logger.debug("Saved cookies to %s", cookie_path)


def clear_cookies() -> None:
    """Remove saved cookies."""
    cookie_path = get_cookie_path()
    if cookie_path.exists():
        cookie_path.unlink()
        logger.debug("Cleared cookies from %s", cookie_path)


def extract_browser_cookies(source: str = "chrome") -> dict[str, str] | None:
    """
    Extract XHS cookies from browser using browser-cookie3.

    Runs in a subprocess to avoid SQLite DB locks when the browser is running.
    """
    extract_script = '''
import json, sys
try:
    import browser_cookie3 as bc3
except ImportError:
    print(json.dumps({"error": "browser-cookie3 not installed"}))
    sys.exit(0)

browsers = {
    "chrome": bc3.chrome,
    "firefox": bc3.firefox,
    "edge": bc3.edge,
    "safari": bc3.safari,
    "brave": bc3.brave,
}

source = sys.argv[1]
loader = browsers.get(source)
if not loader:
    print(json.dumps({"error": f"Unknown browser: {source}"}))
    sys.exit(0)

try:
    cj = loader(domain_name=".xiaohongshu.com")
    cookies = {c.name: c.value for c in cj if "xiaohongshu.com" in (c.domain or "")}
    if cookies.get("a1"):
        print(json.dumps({"browser": source, "cookies": cookies}))
    else:
        print(json.dumps({"error": "no_a1_cookie"}))
except Exception as e:
    print(json.dumps({"error": str(e)}))
'''

    try:
        result = subprocess.run(
            [sys.executable, "-c", extract_script, source],
            capture_output=True,
            text=True,
            timeout=15,
        )

        if result.returncode != 0:
            logger.debug("Cookie extraction subprocess failed: %s", result.stderr)
            return None

        data = json.loads(result.stdout.strip())
        if "error" in data:
            logger.debug("Cookie extraction error: %s", data["error"])
            return None

        return data["cookies"]

    except subprocess.TimeoutExpired:
        logger.debug("Cookie extraction timed out")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        logger.debug("Cookie extraction parse error: %s", e)
        return None


def get_cookies(cookie_source: str = "chrome") -> dict[str, str]:
    """
    Multi-strategy cookie acquisition.

    1. Load saved cookies
    2. Extract from browser
    3. Raise error if all fail
    """
    # 1. Try saved cookies first
    saved = load_saved_cookies()
    if saved:
        return saved

    # 2. Try browser extraction
    from .exceptions import NoCookieError

    extracted = extract_browser_cookies(cookie_source)
    if extracted:
        save_cookies(extracted)
        return extracted

    raise NoCookieError(cookie_source)


def cookies_to_string(cookies: dict[str, str]) -> str:
    """Format cookies as a cookie header string."""
    return "; ".join(f"{k}={v}" for k, v in cookies.items())
