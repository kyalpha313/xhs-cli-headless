"""Cookie extraction and management for XHS API client."""

from __future__ import annotations

import functools
import json
import logging
import subprocess
import sys
import time
from pathlib import Path

from .constants import CONFIG_DIR_NAME, COOKIE_FILE

logger = logging.getLogger(__name__)

# Cookie TTL: warn and attempt browser refresh after 7 days
COOKIE_TTL_DAYS = 7
_COOKIE_TTL_SECONDS = COOKIE_TTL_DAYS * 86400



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
    """Save cookies to local storage with restricted permissions and TTL timestamp."""
    cookie_path = get_cookie_path()
    payload = {**cookies, "saved_at": time.time()}
    cookie_path.write_text(json.dumps(payload, indent=2))
    cookie_path.chmod(0o600)
    logger.debug("Saved cookies to %s", cookie_path)


def clear_cookies() -> None:
    """Remove saved cookies."""
    cookie_path = get_cookie_path()
    if cookie_path.exists():
        cookie_path.unlink()
        logger.debug("Cleared cookies from %s", cookie_path)


@functools.lru_cache(maxsize=1)
def _available_browsers() -> tuple[str, ...]:
    """List all browser names supported by browser_cookie3 (cached)."""
    import inspect

    import browser_cookie3 as bc3

    return tuple(sorted(
        name
        for name in dir(bc3)
        if not name.startswith("_")
        and name != "load"  # 'load' tries all browsers; skip in auto-detect
        and callable(getattr(bc3, name))
        and hasattr(getattr(bc3, name), "__code__")
        and "domain_name" in inspect.signature(getattr(bc3, name)).parameters
    ))


def _get_browser_loader(source: str):
    """Get browser cookie loader from browser_cookie3 by name."""
    import browser_cookie3 as bc3

    loader = getattr(bc3, source, None)
    if loader is None or not callable(loader):
        available = _available_browsers()
        raise ValueError(
            f"Unknown browser: {source!r}. Available: {', '.join(available)}"
        )
    return loader


def _extract_in_process(source: str) -> dict[str, str] | None:
    """Extract cookies in-process for macOS Keychain compatibility."""
    try:
        loader = _get_browser_loader(source)
    except ImportError:
        logger.debug("browser_cookie3 not installed, skipping in-process extraction")
        return None
    except ValueError as exc:
        logger.debug("%s", exc)
        return None

    try:
        jar = loader(domain_name=".xiaohongshu.com")
    except Exception as exc:
        logger.debug("%s in-process extraction failed: %s", source, exc)
        return None

    cookies = {cookie.name: cookie.value for cookie in jar if "xiaohongshu.com" in (cookie.domain or "")}
    if cookies.get("a1"):
        logger.debug("Loaded XHS cookies from %s in-process", source)
        return cookies

    logger.debug("No usable a1 cookie found in %s in-process extraction", source)
    return None


def _extract_via_subprocess(source: str) -> dict[str, str] | None:
    """Extract cookies via subprocess to avoid browser SQLite locks."""
    extract_script = '''
import json, sys
try:
    import browser_cookie3 as bc3
except ImportError:
    print(json.dumps({"error": "browser-cookie3 not installed"}))
    sys.exit(0)

source = sys.argv[1]
loader = getattr(bc3, source, None)
if not loader or not callable(loader):
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


def extract_browser_cookies(source: str = "auto") -> tuple[str, dict[str, str]] | None:
    """
    Extract XHS cookies from browser using browser-cookie3.

    When *source* is ``"auto"``, tries every browser supported by browser_cookie3
    concurrently and returns the first one that has valid cookies.

    Returns ``(browser_name, cookies)`` on success, or ``None``.
    """
    if source != "auto":
        cookies = _extract_in_process(source)
        if cookies:
            return source, cookies
        cookies = _extract_via_subprocess(source)
        if cookies:
            return source, cookies
        return None

    # Auto-detect: try all available browsers
    try:
        browsers = _available_browsers()
    except ImportError:
        logger.debug("browser_cookie3 not installed")
        return None

    for browser in browsers:
        logger.debug("Auto-detect: trying %s …", browser)
        cookies = _extract_in_process(browser)
        if cookies:
            return browser, cookies
        cookies = _extract_via_subprocess(browser)
        if cookies:
            return browser, cookies

    return None


def get_cookies(
    cookie_source: str = "auto", *, force_refresh: bool = False
) -> tuple[str, dict[str, str]]:
    """
    Multi-strategy cookie acquisition with TTL-based auto-refresh.

    Returns ``(browser_name, cookies)``.

    1. Load saved cookies (skip if stale > 7 days)
    2. Extract from browser (auto-detect if *cookie_source* is ``"auto"``)
    3. Raise error if all fail
    """
    # 1. Try saved cookies first
    if not force_refresh:
        saved = load_saved_cookies()
        if saved:
            saved_at = saved.pop("saved_at", 0)
            if saved_at and (time.time() - float(saved_at)) > _COOKIE_TTL_SECONDS:
                logger.info(
                    "Cookies older than %d days, attempting browser refresh",
                    COOKIE_TTL_DAYS,
                )
                result = extract_browser_cookies(cookie_source)
                if result:
                    save_cookies(result[1])
                    return result
                logger.warning(
                    "Cookie refresh failed; using existing cookies (age: %d+ days)",
                    COOKIE_TTL_DAYS,
                )
            return "saved", saved

    # 2. Try browser extraction
    from .exceptions import NoCookieError

    result = extract_browser_cookies(cookie_source)
    if result:
        save_cookies(result[1])
        return result

    raise NoCookieError(cookie_source)


def cookies_to_string(cookies: dict[str, str]) -> str:
    """Format cookies as a cookie header string."""
    return "; ".join(f"{k}={v}" for k, v in cookies.items())
