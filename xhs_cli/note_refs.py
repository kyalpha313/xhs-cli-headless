"""Helpers for resolving and persisting note references across commands."""

from __future__ import annotations

from urllib.parse import urlparse

import click
import httpx

from .constants import USER_AGENT
from .cookies import get_note_by_index, save_note_index
from .formatter import parse_note_reference

_XHS_SHORT_HOSTS = {"xhslink.com", "www.xhslink.com"}


def _with_default_scheme(url: str) -> str:
    value = url.strip()
    if "://" in value:
        return value
    return f"https://{value}"


def _hostname(url: str) -> str:
    return (urlparse(_with_default_scheme(url)).hostname or "").lower()


def is_xhs_short_link(url: str) -> bool:
    """Return True for supported Xiaohongshu short-link hosts."""
    return _hostname(url) in _XHS_SHORT_HOSTS


def is_xiaohongshu_url(url: str) -> bool:
    """Return True for http(s) URLs owned by xiaohongshu.com."""
    parsed = urlparse(_with_default_scheme(url))
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.username or parsed.password:
        return False
    host = (parsed.hostname or "").lower()
    return host == "xiaohongshu.com" or host.endswith(".xiaohongshu.com")


def expand_xhs_short_link(url: str) -> str:
    """Expand an xhslink.com short link and require the final URL to stay on XHS."""
    short_url = _with_default_scheme(url)
    if not is_xhs_short_link(short_url):
        raise click.UsageError("Only xhslink.com short links can be expanded by this command.")

    try:
        with httpx.Client(follow_redirects=True, max_redirects=5, timeout=10.0) as client:
            with client.stream(
                "GET",
                short_url,
                headers={
                    "user-agent": USER_AGENT,
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
            ) as response:
                expanded = str(response.url)
    except httpx.TooManyRedirects as exc:
        raise click.UsageError("xhslink.com short link had too many redirects.") from exc
    except httpx.HTTPError as exc:
        raise click.UsageError(f"Could not expand xhslink.com short link: {exc}") from exc

    if not is_xiaohongshu_url(expanded):
        raise click.UsageError(
            "xhslink.com short link did not expand to a trusted xiaohongshu.com URL."
        )
    return expanded


def resolve_note_reference(id_or_url: str, *, xsec_token: str = "") -> tuple[str, str, str]:
    """Resolve a note reference from URL/ID or the last listing index."""
    if is_xhs_short_link(id_or_url):
        id_or_url = expand_xhs_short_link(id_or_url)
        if not is_xiaohongshu_url(id_or_url):
            raise click.UsageError(
                "xhslink.com short link did not expand to a trusted xiaohongshu.com URL."
            )

    if id_or_url.isdigit():
        entry = get_note_by_index(int(id_or_url))
        if entry is None:
            raise click.UsageError(
                f"Index {id_or_url} not found — run a listing command first "
                "(search / feed / hot / board / my-notes)"
            )
        return (
            entry["note_id"],
            xsec_token or entry.get("xsec_token", ""),
            entry.get("xsec_source", ""),
        )

    note_id, url_token, url_source = parse_note_reference(id_or_url)
    return note_id, xsec_token or url_token, url_source


def save_index_from_items(data: dict, *, xsec_source: str) -> None:
    """Persist ordered note references from list-style responses."""
    entries = []
    for item in data.get("items", []):
        note_card = item.get("note_card", {})
        note_id = item.get("id", note_card.get("note_id", ""))
        token = item.get("xsec_token", note_card.get("xsec_token", ""))
        if note_id:
            entries.append({
                "note_id": note_id,
                "xsec_token": token,
                "xsec_source": xsec_source if token else "",
            })
    save_note_index(entries)


def save_index_from_notes(notes: list[dict]) -> None:
    """Persist ordered note references from paged note payloads."""
    save_note_index([
        {
            "note_id": str(note.get("note_id", note.get("id", ""))).strip(),
            "xsec_token": str(note.get("xsec_token", "")).strip(),
            "xsec_source": "",
        }
        for note in notes
        if str(note.get("note_id", note.get("id", ""))).strip()
    ])
