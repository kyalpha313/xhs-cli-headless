"""Parse note data from Xiaohongshu HTML pages (SSR __INITIAL_STATE__).

This module provides an alternative to the feed API for reading notes.
The HTML endpoint embeds note data in a server-rendered `window.__INITIAL_STATE__`
object, which does not require a valid xsec_token to access.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .exceptions import XhsApiError

logger = logging.getLogger(__name__)

# Regex to extract the __INITIAL_STATE__ JSON blob from the HTML.
_STATE_PATTERN = re.compile(r"window\.__INITIAL_STATE__=({.*?})\s*</script>", re.DOTALL)
_SSR_STATE_PATTERN = re.compile(
    r"window\.__INITIAL_SSR_STATE__\s*=\s*(\{[\s\S]*?\})\s*(?:;|</script>)",
    re.DOTALL,
)


def parse_initial_state(html: str) -> dict[str, Any]:
    """Extract and parse `window.__INITIAL_STATE__` from an XHS note page.

    The server-rendered HTML contains a global state object with note data.
    XHS uses bare `undefined` values in the JS object which are not valid JSON,
    so we replace them before parsing.
    """
    match = _STATE_PATTERN.search(html)
    if not match:
        raise XhsApiError("Could not parse __INITIAL_STATE__ from HTML")

    raw = match.group(1)

    # Replace bare `undefined` with empty string (not valid JSON)
    cleaned = re.sub(r":\s*undefined", ':""', raw)
    cleaned = re.sub(r",\s*undefined", ',""', cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise XhsApiError(f"Failed to parse __INITIAL_STATE__ JSON: {exc}") from None


def extract_note_from_state(
    state: dict[str, Any],
    note_id: str,
) -> dict[str, Any]:
    """Extract a single note dict from the parsed __INITIAL_STATE__.

    The state structure is:
        state.note.noteDetailMap[note_id].note -> full note object
    """
    detail_map = state.get("note", {}).get("noteDetailMap", {})
    if not detail_map:
        raise XhsApiError("Note not found in HTML state: empty noteDetailMap")

    # Try exact noteId first, then fall back to first entry
    entry = detail_map.get(note_id)
    if entry is None:
        entry = next(iter(detail_map.values()), None)

    if entry and isinstance(entry, dict) and "note" in entry:
        return entry["note"]

    raise XhsApiError("Note not found in HTML state")


def _image_url(image: dict[str, Any]) -> str:
    url = image.get("url") or ""
    if url:
        return url
    info_list = image.get("infoList") or image.get("info_list") or []
    if isinstance(info_list, list):
        for item in info_list:
            if isinstance(item, dict) and item.get("url"):
                return str(item["url"])
    return ""


def _normalize_mobile_note(note: dict[str, Any]) -> dict[str, Any]:
    user = note.get("user") or {}
    interact = note.get("interactInfo") or note.get("interact_info") or {}
    images = note.get("imageList") or note.get("image_list") or []
    tags = note.get("tagList") or note.get("tag_list") or []
    normalized_images = [
        {
            "url": _image_url(image),
            "width": image.get("width", 0),
            "height": image.get("height", 0),
            "file_id": image.get("fileId") or image.get("file_id") or "",
        }
        for image in images
        if isinstance(image, dict) and _image_url(image)
    ]
    return {
        "note_id": note.get("noteId") or note.get("note_id") or note.get("id") or "",
        "title": note.get("title") or note.get("displayTitle") or "",
        "desc": note.get("desc") or "",
        "type": note.get("type") or "",
        "user": {
            "nickname": user.get("nickname") or user.get("nickName") or "",
            "user_id": user.get("userId") or user.get("user_id") or user.get("id") or "",
            "avatar": user.get("avatar") or user.get("image") or "",
        },
        "interact_info": {
            "liked_count": interact.get("likedCount") or interact.get("liked_count") or "0",
            "collected_count": interact.get("collectedCount") or interact.get("collected_count") or "0",
            "comment_count": interact.get("commentCount") or interact.get("comment_count") or "0",
            "share_count": interact.get("shareCount") or interact.get("share_count") or "0",
        },
        "tag_list": [
            {"name": tag.get("name") or tag.get("tagName") or ""}
            for tag in tags
            if isinstance(tag, dict) and (tag.get("name") or tag.get("tagName"))
        ],
        "image_list": normalized_images,
    }


def extract_note_from_mobile_state(state: dict[str, Any], note_id: str) -> dict[str, Any]:
    note_data = state.get("noteData", {})
    data = note_data.get("data", {}) if isinstance(note_data, dict) else {}
    note = data.get("noteData", {}) if isinstance(data, dict) else {}
    if not isinstance(note, dict) or not note:
        raise XhsApiError("Note not found in mobile HTML state")

    normalized = _normalize_mobile_note(note)
    if note_id and normalized["note_id"] and normalized["note_id"] != note_id:
        raise XhsApiError("Note not found in mobile HTML state")

    comment_page = data.get("commentData", {}) if isinstance(data, dict) else {}
    return {
        "items": [
            {
                "id": normalized["note_id"],
                "note_card": normalized,
            }
        ],
        "comments": comment_page.get("comments", []) if isinstance(comment_page, dict) else [],
        "comment_page": comment_page if isinstance(comment_page, dict) else {},
        "source": "html",
    }


def extract_note_from_html(html: str, note_id: str) -> dict[str, Any]:
    """High-level: parse HTML → extract note in one step."""
    state = parse_initial_state(html)
    try:
        return extract_note_from_mobile_state(state, note_id)
    except XhsApiError:
        note = extract_note_from_state(state, note_id)
        return {
            "items": [
                {
                    "id": note_id,
                    "note_card": note,
                }
            ],
            "source": "html",
        }


def parse_initial_ssr_state(html: str) -> dict[str, Any]:
    """Extract and parse `window.__INITIAL_SSR_STATE__` from HTML."""
    match = _SSR_STATE_PATTERN.search(html)
    if not match:
        raise XhsApiError("Could not parse __INITIAL_SSR_STATE__ from HTML")

    raw = match.group(1)
    cleaned = re.sub(r"\bundefined\b", "null", raw)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise XhsApiError(f"Failed to parse __INITIAL_SSR_STATE__ JSON: {exc}") from None


def extract_board_from_ssr_state(state: dict[str, Any], board_id: str) -> dict[str, Any]:
    main = state.get("Main")
    if not isinstance(main, dict):
        raise XhsApiError("Board not found in SSR HTML state")

    album_info = main.get("albumInfo", {})
    notes_detail = main.get("notesDetail", [])
    notes = notes_detail if isinstance(notes_detail, list) else []

    return {
        "board_id": board_id,
        "name": album_info.get("name") or album_info.get("title") or "",
        "desc": album_info.get("desc") or "",
        "note_count": album_info.get("noteCount") or album_info.get("note_count") or len(notes),
        "notes": [
            {
                "note_id": note.get("id") or note.get("noteId") or note.get("note_id") or "",
                "xsec_token": note.get("xsecToken") or note.get("xsec_token") or "",
                "title": note.get("title") or note.get("displayTitle") or "",
                "type": note.get("type") or "",
                "author": (note.get("user") or {}).get("nickname")
                or (note.get("user") or {}).get("nickName")
                or "",
                "cover": ((note.get("cover") or {}).get("url") or "").split("?")[0],
            }
            for note in notes
            if isinstance(note, dict)
        ],
    }


def extract_board_from_state(state: dict[str, Any], board_id: str) -> dict[str, Any]:
    board = state.get("board", {})
    board_details = board.get("boardDetails", {})
    board_feeds_map = board.get("boardFeedsMap", {})

    detail_map = board_details.get("_rawValue", board_details) if isinstance(board_details, dict) else {}
    feeds_map = board_feeds_map.get("_rawValue", board_feeds_map) if isinstance(board_feeds_map, dict) else {}

    detail = detail_map.get(board_id, {}) if isinstance(detail_map, dict) else {}
    feed_entry = feeds_map.get(board_id, {}) if isinstance(feeds_map, dict) else {}
    if not feed_entry and isinstance(feeds_map, dict):
        first_key = next((key for key in feeds_map if key != "_rawValue"), "")
        feed_entry = feeds_map.get(first_key, {}) if first_key else {}

    notes = feed_entry.get("notes", []) if isinstance(feed_entry, dict) else []
    detail = detail if isinstance(detail, dict) else {}

    return {
        "board_id": board_id,
        "name": detail.get("name") or detail.get("title") or "",
        "desc": detail.get("desc") or "",
        "note_count": detail.get("noteCount") or detail.get("note_count") or len(notes),
        "notes": [
            {
                "note_id": note.get("id") or note.get("noteId") or note.get("note_id") or "",
                "xsec_token": note.get("xsecToken") or note.get("xsec_token") or "",
                "title": note.get("title") or note.get("displayTitle") or "",
                "type": note.get("type") or "",
                "author": (note.get("user") or {}).get("nickname")
                or (note.get("user") or {}).get("nickName")
                or "",
                "cover": ((note.get("cover") or {}).get("url") or "").split("?")[0],
            }
            for note in notes
            if isinstance(note, dict)
        ],
    }


def extract_board_from_html(html: str, board_id: str) -> dict[str, Any]:
    """High-level: parse board HTML from SSR or legacy state."""
    try:
        state = parse_initial_ssr_state(html)
        return extract_board_from_ssr_state(state, board_id)
    except XhsApiError:
        state = parse_initial_state(html)
        return extract_board_from_state(state, board_id)
