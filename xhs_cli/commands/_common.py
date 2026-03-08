"""Common helpers for CLI commands."""

from ..client import XhsClient
from ..cookies import get_cookies


def get_client(ctx) -> XhsClient:
    """Get an XhsClient from the click context."""
    cookie_source = ctx.obj.get("cookie_source", "chrome") if ctx.obj else "chrome"
    cookies = get_cookies(cookie_source)
    return XhsClient(cookies)
