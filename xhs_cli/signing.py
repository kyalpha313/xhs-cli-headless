"""
Main API signing for edith.xiaohongshu.com

Thin adapter over the xhshow library, configured for macOS/Chrome.
Maintains a persistent SessionManager for realistic session simulation.

Public API (unchanged from previous implementation):
  - sign_main_api(method, uri, cookies, ...) -> dict of 5 headers
  - build_get_uri(uri, params) -> str
  - extract_uri(url) -> str
"""

from __future__ import annotations

from xhshow import CryptoConfig, SessionManager, Xhshow
from xhshow.utils.url_utils import extract_uri  # noqa: F401 — re-export

from .constants import (
    APP_ID,
    PLATFORM,
    SDK_VERSION,
    USER_AGENT,
    WINDOWS_PLATFORM,
    WINDOWS_USER_AGENT,
)

def _build_config(*, user_agent: str, platform: str) -> CryptoConfig:
    return CryptoConfig().with_overrides(
        PUBLIC_USERAGENT=user_agent,
        SIGNATURE_DATA_TEMPLATE={
            "x0": SDK_VERSION,
            "x1": APP_ID,
            "x2": platform,
            "x3": "",
            "x4": "",
        },
        SIGNATURE_XSCOMMON_TEMPLATE={
            "s0": 5,
            "s1": "",
            "x0": "1",
            "x1": SDK_VERSION,
            "x2": platform,
            "x3": APP_ID,
            "x4": "4.86.0",
            "x5": "",
            "x6": "",
            "x7": "",
            "x8": "",
            "x9": -596800761,
            "x10": 0,
            "x11": "normal",
        },
    )


_PROFILE_CONFIGS = {
    "default": _build_config(user_agent=USER_AGENT, platform=PLATFORM),
    "windows": _build_config(user_agent=WINDOWS_USER_AGENT, platform=WINDOWS_PLATFORM),
}
_PROFILE_SIGNERS = {name: Xhshow(config) for name, config in _PROFILE_CONFIGS.items()}
_PROFILE_SESSIONS = {name: SessionManager(config) for name, config in _PROFILE_CONFIGS.items()}


# ─── Public API ─────────────────────────────────────────────────────────────


def sign_main_api(
    method: str,
    uri: str,
    cookies: dict[str, str],
    params: dict[str, str | int | list[str]] | None = None,
    payload: dict | None = None,
    timestamp: float | None = None,
    profile: str = "default",
) -> dict[str, str]:
    """
    Generate all signing headers for a main API (edith.xiaohongshu.com) request.

    Returns dict with keys: x-s, x-s-common, x-t, x-b3-traceid, x-xray-traceid
    """
    xhshow = _PROFILE_SIGNERS[profile]
    session = _PROFILE_SESSIONS[profile]
    if method.upper() == "GET":
        return xhshow.sign_headers_get(
            uri, cookies, params=params, timestamp=timestamp, session=session,
        )
    return xhshow.sign_headers_post(
        uri, cookies, payload=payload, timestamp=timestamp, session=session,
    )


def build_get_uri(
    uri: str,
    params: dict[str, str | int | list[str]] | None = None,
) -> str:
    """Build URI with query parameters for GET requests."""
    if not params:
        return uri
    return _PROFILE_SIGNERS["default"].build_url(uri, params)
