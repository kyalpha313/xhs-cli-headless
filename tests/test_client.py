"""Unit tests for XHS client request payloads, cookies, and endpoint selection."""

from collections import OrderedDict

import httpx
import pytest

from xhs_cli.client import XhsClient
from xhs_cli.cookies import cache_note_context, get_cached_note_context
from xhs_cli.exceptions import UnsupportedOperationError, XhsApiError
from xhs_cli.html_parser import extract_board_from_html


class TestFavorites:
    def test_unfavorite_uses_note_ids_payload(self, monkeypatch):
        captured = {}

        def fake_post(self, uri, data, header_overrides=None):
            captured["uri"] = uri
            captured["data"] = data
            return True

        monkeypatch.setattr(XhsClient, "_main_api_post", fake_post)

        client = XhsClient({"a1": "cookie"})
        try:
            client.unfavorite_note("note-123")
        finally:
            client.close()

        assert captured["uri"] == "/api/sns/web/v1/note/uncollect"
        assert captured["data"] == {"note_ids": "note-123"}


class TestCreatorEndpoints:
    def test_creator_note_list_uses_v2_endpoint(self, monkeypatch):
        captured = {}

        def fake_get(self, uri, params=None):
            captured["uri"] = uri
            captured["params"] = params
            return {"notes": [], "page": -1}

        monkeypatch.setattr(XhsClient, "_creator_get", fake_get)

        client = XhsClient({"a1": "cookie"})
        try:
            result = client.get_creator_note_list(page=2)
        finally:
            client.close()

        assert result["page"] == -1
        assert captured["uri"] == "/api/galaxy/v2/creator/note/user/posted"
        assert captured["params"] == {"tab": 0, "page": 2}

    def test_delete_note_raises_unsupported_for_404(self, monkeypatch):
        def fake_post(self, uri, data, header_overrides=None, method="POST"):
            raise XhsApiError(
                "API error: {\"status\": 404}",
                response={"status": 404},
            )

        monkeypatch.setattr(XhsClient, "_creator_post", fake_post)

        client = XhsClient({"a1": "cookie"})
        try:
            with pytest.raises(UnsupportedOperationError, match="Delete note is currently unavailable"):
                client.delete_note("note-123")
        finally:
            client.close()

    def test_delete_note_tries_multiple_candidates_before_success(self, monkeypatch):
        calls = []

        def fake_post(self, uri, data, header_overrides=None, method="POST"):
            calls.append((uri, data, header_overrides, method))
            if len(calls) < 3:
                raise XhsApiError(
                    "API error: {\"code\": -1, \"result\": -100, \"msg\": \"登录已过期\"}",
                    code=-1,
                    response={"code": -1, "result": -100, "msg": "登录已过期"},
                )
            return {"ok": True}

        monkeypatch.setattr(XhsClient, "_creator_post", fake_post)

        client = XhsClient({"a1": "cookie"})
        try:
            result = client.delete_note("note-123")
        finally:
            client.close()

        assert result == {"ok": True}
        assert calls[:3] == [
            (
                "/api/galaxy/creator/note/delete",
                {"note_id": "note-123"},
                {"referer": "https://creator.xiaohongshu.com/publish/notes"},
                "POST",
            ),
            (
                "/api/galaxy/creator/note/delete",
                {"noteId": "note-123"},
                {"referer": "https://creator.xiaohongshu.com/publish/notes"},
                "POST",
            ),
            (
                "/api/galaxy/creator/note/delete",
                {"id": "note-123"},
                {"referer": "https://creator.xiaohongshu.com/publish/notes"},
                "POST",
            ),
        ]

    def test_delete_note_maps_repeated_login_expired_to_unsupported(self, monkeypatch):
        def fake_post(self, uri, data, header_overrides=None, method="POST"):
            raise XhsApiError(
                "API error: {\"code\": -1, \"result\": -100, \"msg\": \"\\u767b\\u5f55\\u5df2\\u8fc7\\u671f\"}",
                code=-1,
                response={"code": -1, "result": -100, "msg": "登录已过期"},
            )

        monkeypatch.setattr(XhsClient, "_creator_post", fake_post)

        client = XhsClient({"a1": "cookie"})
        try:
            with pytest.raises(UnsupportedOperationError, match="creator-side login expired"):
                client.delete_note("note-123")
        finally:
            client.close()


class TestTransportCookies:
    def test_request_with_retry_merges_response_cookies(self, monkeypatch):
        request = httpx.Request("POST", "https://edith.xiaohongshu.com/api/test")
        response = httpx.Response(
            200,
            headers=[
                ("set-cookie", "web_session=real-session; Path=/; Domain=.xiaohongshu.com"),
                ("set-cookie", "web_session_sec=real-sec; Path=/; Domain=.xiaohongshu.com"),
            ],
            json={"success": True, "data": {"ok": True}},
            request=request,
        )

        class _FakeHttpClient:
            def request(self, method, url, **kwargs):
                return response

            def close(self):
                return None

        client = XhsClient({"a1": "cookie", "web_session": "guest-session"}, request_delay=0)
        client._http = _FakeHttpClient()
        try:
            resp = client._request_with_retry("POST", "https://edith.xiaohongshu.com/api/test")
        finally:
            client.close()

        assert resp is response
        assert client.cookies["web_session"] == "real-session"
        assert client.cookies["web_session_sec"] == "real-sec"


class TestReadingEndpointBehavior:
    def test_extract_board_from_ssr_html(self):
        html = """
<script>
window.__INITIAL_SSR_STATE__ = {"Main":{"albumInfo":{"name":"Board A","desc":"desc","noteCount":2},"notesDetail":[{"id":"n1","xsecToken":"t1","title":"One","type":"normal","user":{"nickname":"Alice"},"cover":{"url":"https://img/1.jpg?x-oss=1"}},{"id":"n2","xsecToken":"t2","displayTitle":"Two","type":"video","user":{"nickName":"Bob"},"cover":{"url":"https://img/2.jpg"}}]}};
</script>
"""
        data = extract_board_from_html(html, "board-1")
        assert data["board_id"] == "board-1"
        assert data["name"] == "Board A"
        assert data["desc"] == "desc"
        assert data["note_count"] == 2
        assert data["notes"][0]["note_id"] == "n1"
        assert data["notes"][0]["xsec_token"] == "t1"
        assert data["notes"][0]["author"] == "Alice"
        assert data["notes"][0]["cover"] == "https://img/1.jpg"

    def test_extract_board_from_legacy_html(self):
        html = """
<script>
window.__INITIAL_STATE__={"board":{"boardDetails":{"board-2":{"name":"Legacy Board","desc":"old","noteCount":1}},"boardFeedsMap":{"board-2":{"notes":[{"noteId":"n9","xsec_token":"tok-9","displayTitle":"Legacy note","type":"normal","user":{"nickname":"Carol"},"cover":{"url":"https://img/9.jpg?foo=1"}}]}}}}</script>
"""
        data = extract_board_from_html(html, "board-2")
        assert data["board_id"] == "board-2"
        assert data["name"] == "Legacy Board"
        assert data["desc"] == "old"
        assert data["note_count"] == 1
        assert data["notes"][0]["note_id"] == "n9"
        assert data["notes"][0]["xsec_token"] == "tok-9"
        assert data["notes"][0]["author"] == "Carol"
        assert data["notes"][0]["cover"] == "https://img/9.jpg"

    def test_get_board_from_html_uses_board_page_fetch(self, monkeypatch):
        html = """
<script>
window.__INITIAL_SSR_STATE__ = {"Main":{"albumInfo":{"title":"Board Title"},"notesDetail":[]}};
</script>
"""

        def fake_fetch(self, board_id):
            assert board_id == "board-123"
            return html

        monkeypatch.setattr(XhsClient, "_fetch_board_html", fake_fetch)

        client = XhsClient({"a1": "cookie"})
        try:
            data = client.get_board_from_html("board-123")
        finally:
            client.close()

        assert data["board_id"] == "board-123"
        assert data["name"] == "Board Title"

    def test_get_user_info_retries_with_windows_profile_after_code_minus_one(self, monkeypatch):
        calls = []

        def fake_get(self, uri, params=None, sign_profile="default"):
            calls.append((uri, params, sign_profile))
            if sign_profile == "default":
                raise XhsApiError(
                    "API error: {\"code\": -1, \"success\": false}",
                    code=-1,
                    response={"code": -1, "success": False},
                )
            return {"user_id": "user-123"}

        monkeypatch.setattr(XhsClient, "_main_api_get", fake_get)

        client = XhsClient({"a1": "cookie"})
        try:
            result = client.get_user_info("user-123")
        finally:
            client.close()

        assert result == {"user_id": "user-123"}
        assert calls == [
            (
                "/api/sns/web/v1/user/otherinfo",
                {"target_user_id": "user-123"},
                "default",
            ),
            (
                "/api/sns/web/v1/user/otherinfo",
                {"target_user_id": "user-123"},
                "windows",
            ),
        ]

    def test_get_user_info_maps_code_minus_one_to_unsupported_operation(self, monkeypatch):
        def fake_get(self, uri, params=None, sign_profile="default"):
            raise XhsApiError(
                "API error: {\"code\": -1, \"success\": false}",
                code=-1,
                response={"code": -1, "success": False},
            )

        monkeypatch.setattr(XhsClient, "_main_api_get", fake_get)

        client = XhsClient({"a1": "cookie"})
        try:
            with pytest.raises(UnsupportedOperationError, match="User profile lookup is currently unavailable"):
                client.get_user_info("user-123")
        finally:
            client.close()

    def test_get_user_notes_retries_with_windows_profile_after_code_minus_one(self, monkeypatch):
        calls = []

        def fake_get(self, uri, params=None, sign_profile="default"):
            calls.append((uri, params, sign_profile))
            if sign_profile == "default":
                raise XhsApiError(
                    "API error: {\"code\": -1, \"success\": false}",
                    code=-1,
                    response={"code": -1, "success": False},
                )
            return {"notes": []}

        monkeypatch.setattr(XhsClient, "_main_api_get", fake_get)

        client = XhsClient({"a1": "cookie"})
        try:
            result = client.get_user_notes("user-123")
        finally:
            client.close()

        assert result == {"notes": []}
        assert calls == [
            (
                "/api/sns/web/v1/user_posted",
                {
                    "num": 30,
                    "cursor": "",
                    "user_id": "user-123",
                    "image_scenes": "FD_WM_WEBP",
                },
                "default",
            ),
            (
                "/api/sns/web/v1/user_posted",
                {
                    "num": 30,
                    "cursor": "",
                    "user_id": "user-123",
                    "image_scenes": "FD_WM_WEBP",
                },
                "windows",
            ),
        ]

    def test_get_user_notes_maps_code_minus_one_to_unsupported_operation(self, monkeypatch):
        def fake_get(self, uri, params=None, sign_profile="default"):
            raise XhsApiError(
                "API error: {\"code\": -1, \"success\": false}",
                code=-1,
                response={"code": -1, "success": False},
            )

        monkeypatch.setattr(XhsClient, "_main_api_get", fake_get)

        client = XhsClient({"a1": "cookie"})
        try:
            with pytest.raises(UnsupportedOperationError, match="User posts lookup is currently unavailable"):
                client.get_user_notes("user-123")
        finally:
            client.close()

    def test_get_user_favorites_retries_with_windows_profile_after_code_minus_one(self, monkeypatch):
        calls = []

        def fake_get(self, uri, params=None, sign_profile="default"):
            calls.append((uri, params, sign_profile))
            if sign_profile == "default":
                raise XhsApiError(
                    "API error: {\"code\": -1, \"success\": false}",
                    code=-1,
                    response={"code": -1, "success": False},
                )
            return {"notes": []}

        monkeypatch.setattr(XhsClient, "_main_api_get", fake_get)

        client = XhsClient({"a1": "cookie"})
        try:
            result = client.get_user_favorites("user-123")
        finally:
            client.close()

        assert result == {"notes": []}
        assert calls[-1][2] == "windows"
        assert calls[0][0] == "/api/sns/web/v2/note/collect/page"

    def test_get_sub_comments_uses_resolved_xsec_context(self, monkeypatch):
        captured = {}

        def fake_get(self, uri, params=None):
            captured["uri"] = uri
            captured["params"] = params
            return {"comments": []}

        monkeypatch.setattr(XhsClient, "_main_api_get", fake_get)
        monkeypatch.setattr(
            XhsClient,
            "resolve_xsec_context",
            lambda self, note_id, xsec_token, xsec_source: ("token-abc", "pc_search"),
        )

        client = XhsClient({"a1": "cookie"})
        try:
            client.get_sub_comments("note-123", "comment-123")
        finally:
            client.close()

        assert captured["uri"] == "/api/sns/web/v2/comment/sub/page"
        assert captured["params"]["xsec_token"] == "token-abc"
        assert captured["params"]["xsec_source"] == "pc_search"

    def test_reply_comment_retries_rate_limited_once(self, monkeypatch):
        calls = {"count": 0}

        def fake_post(self, uri, data, header_overrides=None):
            calls["count"] += 1
            if calls["count"] == 1:
                raise XhsApiError(
                    "API error: {\"code\": -9043}",
                    code=-9043,
                    response={"code": -9043},
                )
            return {"success": True}

        monkeypatch.setattr(XhsClient, "_main_api_post", fake_post)
        monkeypatch.setattr("xhs_cli.client_mixins.time.sleep", lambda _seconds: None)

        client = XhsClient({"a1": "cookie"})
        try:
            result = client.reply_comment("note-123", "comment-123", "hello")
        finally:
            client.close()

        assert result == {"success": True}
        assert calls["count"] == 2

    def test_reply_comment_maps_persistent_rate_limit_to_clear_error(self, monkeypatch):
        def fake_post(self, uri, data, header_overrides=None):
            raise XhsApiError(
                "API error: {\"code\": -9043}",
                code=-9043,
                response={"code": -9043},
            )

        monkeypatch.setattr(XhsClient, "_main_api_post", fake_post)
        monkeypatch.setattr("xhs_cli.client_mixins.time.sleep", lambda _seconds: None)

        client = XhsClient({"a1": "cookie"})
        try:
            with pytest.raises(XhsApiError, match="Reply was rate-limited"):
                client.reply_comment("note-123", "comment-123", "hello")
        finally:
            client.close()

    def test_notification_mentions_maps_code_minus_one_to_unsupported_operation(self, monkeypatch):
        def fake_get(self, uri, params=None, sign_profile="default"):
            raise XhsApiError(
                "API error: {\"code\": -1, \"success\": false}",
                code=-1,
                response={"code": -1, "success": False},
            )

        monkeypatch.setattr(XhsClient, "_main_api_get", fake_get)
        client = XhsClient({"a1": "cookie"})
        try:
            with pytest.raises(UnsupportedOperationError, match="Notification list is currently unavailable"):
                client.get_notification_mentions()
        finally:
            client.close()

    def test_notification_mentions_retries_with_windows_profile_after_code_minus_one(self, monkeypatch):
        calls = []

        def fake_get(self, uri, params=None, sign_profile="default"):
            calls.append((uri, params, sign_profile))
            if sign_profile == "default":
                raise XhsApiError(
                    "API error: {\"code\": -1, \"success\": false}",
                    code=-1,
                    response={"code": -1, "success": False},
                )
            return {"messages": []}

        monkeypatch.setattr(XhsClient, "_main_api_get", fake_get)
        client = XhsClient({"a1": "cookie"})
        try:
            result = client.get_notification_mentions()
        finally:
            client.close()

        assert result == {"messages": []}
        assert calls[-1][2] == "windows"
        assert calls[0][0] == "/api/sns/web/v1/you/mentions"

    def test_notification_likes_maps_code_minus_one_to_unsupported_operation(self, monkeypatch):
        def fake_get(self, uri, params=None, sign_profile="default"):
            raise XhsApiError(
                "API error: {\"code\": -1, \"success\": false}",
                code=-1,
                response={"code": -1, "success": False},
            )

        monkeypatch.setattr(XhsClient, "_main_api_get", fake_get)
        client = XhsClient({"a1": "cookie"})
        try:
            with pytest.raises(UnsupportedOperationError, match="Notification list is currently unavailable"):
                client.get_notification_likes()
        finally:
            client.close()

    def test_notification_connections_maps_code_minus_one_to_unsupported_operation(self, monkeypatch):
        def fake_get(self, uri, params=None, sign_profile="default"):
            raise XhsApiError(
                "API error: {\"code\": -1, \"success\": false}",
                code=-1,
                response={"code": -1, "success": False},
            )

        monkeypatch.setattr(XhsClient, "_main_api_get", fake_get)
        client = XhsClient({"a1": "cookie"})
        try:
            with pytest.raises(UnsupportedOperationError, match="Notification list is currently unavailable"):
                client.get_notification_connections()
        finally:
            client.close()

    def test_get_note_detail_prefers_cached_xsec_source(self, monkeypatch):
        captured = {}

        def fake_get_note_by_id(self, note_id, xsec_token="", xsec_source="pc_feed"):
            captured["note_id"] = note_id
            captured["token"] = xsec_token
            captured["source"] = xsec_source
            return {"items": [{"note_card": {"title": "ok"}}]}

        monkeypatch.setattr(XhsClient, "get_note_by_id", fake_get_note_by_id)
        cache_note_context("note-123", "token-xyz", "pc_search")

        client = XhsClient({"a1": "cookie"})
        try:
            client.get_note_detail("note-123")
        finally:
            client.close()

        assert captured == {
            "note_id": "note-123",
            "token": "token-xyz",
            "source": "pc_search",
        }

    def test_search_notes_uses_browser_like_prewarm_sequence(self, monkeypatch):
        calls = []

        monkeypatch.setattr("xhs_cli.client_mixins._SEARCH_SESSION_CACHE", OrderedDict())
        monkeypatch.setattr("xhs_cli.client_mixins._SEARCH_SESSION_CACHE_LOADED", True)

        def fake_get(self, uri, params=None):
            calls.append(("GET", uri, params))
            return {"ok": True}

        def fake_post(self, uri, data, header_overrides=None):
            calls.append(("POST", uri, data))
            if uri == "/api/sns/web/v1/search/notes":
                return {"items": [], "has_more": False}
            return {"ok": True}

        monkeypatch.setattr(XhsClient, "_main_api_get", fake_get)
        monkeypatch.setattr(XhsClient, "_main_api_post", fake_post)

        client = XhsClient({"a1": "cookie"})
        try:
            client.search_notes("openclaw prompt", page=2)
        finally:
            client.close()

        assert [call[1] for call in calls] == [
            "/api/sns/web/v1/search/onebox",
            "/api/sns/web/v1/search/filter",
            "/api/sns/web/v1/search/notes",
            "/api/sns/web/v1/search/recommend",
        ]

        notes_payload = calls[2][2]
        assert notes_payload["page"] == 2
        assert notes_payload["filters"][0]["type"] == "sort_type"
        assert notes_payload["filters"][1]["type"] == "filter_note_type"

    def test_search_notes_reuses_search_id_across_pages(self, monkeypatch):
        calls = []

        monkeypatch.setattr("xhs_cli.client_mixins._SEARCH_SESSION_CACHE", OrderedDict())
        monkeypatch.setattr("xhs_cli.client_mixins._SEARCH_SESSION_CACHE_LOADED", True)

        def fake_get(self, uri, params=None):
            calls.append(("GET", uri, params))
            return {"ok": True}

        def fake_post(self, uri, data, header_overrides=None):
            calls.append(("POST", uri, data))
            if uri == "/api/sns/web/v1/search/notes":
                return {"items": [], "has_more": False}
            return {"ok": True}

        monkeypatch.setattr(XhsClient, "_main_api_get", fake_get)
        monkeypatch.setattr(XhsClient, "_main_api_post", fake_post)

        client = XhsClient({"a1": "cookie"})
        try:
            client.search_notes("openclaw", page=1)
            client.search_notes("openclaw", page=2)
        finally:
            client.close()

        notes_calls = [call for call in calls if call[1] == "/api/sns/web/v1/search/notes"]
        assert len(notes_calls) == 2
        assert notes_calls[0][2]["search_id"] == notes_calls[1][2]["search_id"]

        onebox_calls = [call for call in calls if call[1] == "/api/sns/web/v1/search/onebox"]
        filter_calls = [call for call in calls if call[1] == "/api/sns/web/v1/search/filter"]
        recommend_calls = [call for call in calls if call[1] == "/api/sns/web/v1/search/recommend"]
        assert len(onebox_calls) == 1
        assert len(filter_calls) == 1
        assert len(recommend_calls) == 1

    def test_search_notes_reuses_search_id_after_cache_reload(self, monkeypatch, tmp_path):
        first_calls = []
        second_calls = []

        monkeypatch.setattr("xhs_cli.client_mixins.get_config_dir", lambda: tmp_path)
        monkeypatch.setattr("xhs_cli.client_mixins._SEARCH_SESSION_CACHE", OrderedDict())
        monkeypatch.setattr("xhs_cli.client_mixins._SEARCH_SESSION_CACHE_LOADED", False)
        monkeypatch.setattr("xhs_cli.client_mixins._SEARCH_SESSION_CACHE_PATH", None)

        def fake_get_first(self, uri, params=None):
            first_calls.append(("GET", uri, params))
            return {"ok": True}

        def fake_post_first(self, uri, data, header_overrides=None):
            first_calls.append(("POST", uri, data))
            if uri == "/api/sns/web/v1/search/notes":
                return {"items": [], "has_more": False}
            return {"ok": True}

        monkeypatch.setattr(XhsClient, "_main_api_get", fake_get_first)
        monkeypatch.setattr(XhsClient, "_main_api_post", fake_post_first)

        client = XhsClient({"a1": "cookie"})
        try:
            client.search_notes("openclaw", page=1)
        finally:
            client.close()

        monkeypatch.setattr("xhs_cli.client_mixins._SEARCH_SESSION_CACHE", OrderedDict())
        monkeypatch.setattr("xhs_cli.client_mixins._SEARCH_SESSION_CACHE_LOADED", False)
        monkeypatch.setattr("xhs_cli.client_mixins._SEARCH_SESSION_CACHE_PATH", None)

        def fake_get_second(self, uri, params=None):
            second_calls.append(("GET", uri, params))
            return {"ok": True}

        def fake_post_second(self, uri, data, header_overrides=None):
            second_calls.append(("POST", uri, data))
            if uri == "/api/sns/web/v1/search/notes":
                return {"items": [], "has_more": False}
            return {"ok": True}

        monkeypatch.setattr(XhsClient, "_main_api_get", fake_get_second)
        monkeypatch.setattr(XhsClient, "_main_api_post", fake_post_second)

        client = XhsClient({"a1": "cookie"})
        try:
            client.search_notes("openclaw", page=2)
        finally:
            client.close()

        first_notes_call = next(call for call in first_calls if call[1] == "/api/sns/web/v1/search/notes")
        second_notes_call = next(call for call in second_calls if call[1] == "/api/sns/web/v1/search/notes")
        assert first_notes_call[2]["search_id"] == second_notes_call[2]["search_id"]
        assert [call[1] for call in second_calls] == ["/api/sns/web/v1/search/notes"]

    def test_get_note_detail_invalidates_cached_context_after_feed_failure(self, monkeypatch):
        cache_note_context("note-123", "stale-token", "pc_search")

        def fake_get_note_by_id(self, note_id, xsec_token="", xsec_source="pc_feed"):
            raise XhsApiError("stale token")

        def fake_get_note_from_html(self, note_id, xsec_token="", xsec_source="pc_feed"):
            return {"items": [{"note_card": {"title": "html-ok"}}]}

        monkeypatch.setattr(XhsClient, "get_note_by_id", fake_get_note_by_id)
        monkeypatch.setattr(XhsClient, "get_note_from_html", fake_get_note_from_html)

        client = XhsClient({"a1": "cookie"})
        try:
            result = client.get_note_detail("note-123")
        finally:
            client.close()

        assert result["items"][0]["note_card"]["title"] == "html-ok"
        assert get_cached_note_context("note-123") == {}
