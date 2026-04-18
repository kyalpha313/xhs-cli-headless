"""Tests for CLI commands using Click's test runner."""

import json

import click
import pytest
import yaml
from click.testing import CliRunner

from xhs_cli.cli import cli
from xhs_cli.exceptions import SessionExpiredError

runner = CliRunner()

FAKE_NOTE_RESPONSE = {
    "items": [
        {
            "note_card": {
                "title": "Test Note",
                "desc": "body",
                "user": {"nickname": "Author"},
                "interact_info": {
                    "liked_count": "100",
                    "collected_count": "50",
                    "comment_count": "10",
                    "share_count": "5",
                },
                "tag_list": [],
                "image_list": [],
            }
        }
    ]
}


def _assert_qrcode_kwargs(expected_print_link: bool, **kwargs):
    assert kwargs.keys() == {"prefer_browser_assisted", "print_link", "on_status"}
    assert kwargs["prefer_browser_assisted"] is False
    assert kwargs["print_link"] is expected_print_link
    assert callable(kwargs["on_status"])
    return {
        "a1": "a1-http",
        "webId": "webid-http",
        "web_session": "session-http",
    }


class TestCliBasic:
    """Test CLI basics without requiring cookies."""

    def test_version(self):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0." in result.output  # dynamic version from importlib.metadata

    def test_help(self):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "xhs" in result.output
        assert "search" in result.output
        assert "read" in result.output

    def test_search_help(self):
        result = runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0
        assert "keyword" in result.output.lower() or "KEYWORD" in result.output

    def test_read_help(self):
        result = runner.invoke(cli, ["read", "--help"])
        assert result.exit_code == 0

    def test_login_help(self):
        result = runner.invoke(cli, ["login", "--help"])
        assert result.exit_code == 0
        assert "--qrcode-http" in result.output
        assert "--print-link" in result.output
        assert "--browser" not in result.output

    def test_auth_help(self):
        result = runner.invoke(cli, ["auth", "--help"])
        assert result.exit_code == 0
        assert "doctor" in result.output
        assert "import" in result.output
        assert "inspect" in result.output

    def test_status_help(self):
        result = runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0

    def test_all_commands_registered(self):
        result = runner.invoke(cli, ["--help"])
        commands_in_help = {
            line.strip().split()[0]
            for line in result.output.splitlines()
            if line.startswith("  ") and line.strip() and not line.strip().startswith("-")
        }
        commands_expected = [
            # Auth
            "auth", "login", "status", "logout", "whoami",
            # Reading
            "search", "read", "comments", "feed", "hot", "topics", "search-user", "my-notes",
            "unread",
            # Interactions
            "like", "favorite", "unfavorite", "comment", "reply", "delete-comment",
            # Social
            "follow", "unfollow", "board",
        ]
        for cmd in commands_expected:
            assert cmd in commands_in_help, f"Command '{cmd}' not found in CLI help"

        commands_hidden = [
            "sub-comments",
            "user",
            "user-posts",
            "favorites",
            "likes",
            "notifications",
            "post",
            "delete",
        ]
        for cmd in commands_hidden:
            assert cmd not in commands_in_help, f"Command '{cmd}' should not be exposed in CLI help"

    def test_whoami_help(self):
        result = runner.invoke(cli, ["whoami", "--help"])
        assert result.exit_code == 0

    def test_reply_help(self):
        result = runner.invoke(cli, ["reply", "--help"])
        assert result.exit_code == 0

    def test_board_command_accepts_url(self, monkeypatch):
        captured = {}

        class FakeClient:
            def __init__(self, cookies):
                self.cookies = cookies

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def get_board_from_html(self, board_id):
                captured["board_id"] = board_id
                return {
                    "board_id": board_id,
                    "name": "Board Title",
                    "desc": "",
                    "note_count": 1,
                    "notes": [{"note_id": "note-1", "title": "Hello", "xsec_token": "tok"}],
                }

        monkeypatch.setattr("xhs_cli.commands._common.load_saved_cookies", lambda: {"a1": "cookie"})
        monkeypatch.setattr("xhs_cli.commands._common.XhsClient", FakeClient)

        result = runner.invoke(
            cli,
            ["board", "https://www.xiaohongshu.com/board/board-123?source=web_user_page", "--json"],
        )

        assert result.exit_code == 0
        assert captured["board_id"] == "board-123"
        payload = json.loads(result.output)
        assert payload["ok"] is True
        assert payload["data"]["board_id"] == "board-123"

    def test_board_help(self):
        result = runner.invoke(cli, ["board", "--help"])
        assert result.exit_code == 0

    def test_auth_doctor_reports_missing_cookie_file(self, monkeypatch, tmp_path):
        monkeypatch.setattr("xhs_cli.commands.auth.get_cookie_path", lambda: tmp_path / "cookies.json")
        monkeypatch.setattr("xhs_cli.commands.auth.load_saved_cookies", lambda: None)

        result = runner.invoke(cli, ["auth", "doctor", "--yaml"])

        assert result.exit_code == 0
        payload = yaml.safe_load(result.output)
        assert payload["ok"] is True
        assert payload["data"]["cookies_file_found"] is False
        assert payload["data"]["authenticated"] is False
        assert payload["data"]["recommended_action"] == "import_cookies"

    def test_auth_doctor_reports_valid_saved_session(self, monkeypatch, tmp_path):
        monkeypatch.setattr("xhs_cli.commands.auth.get_cookie_path", lambda: tmp_path / "cookies.json")
        monkeypatch.setattr(
            "xhs_cli.commands.auth.load_saved_cookies",
            lambda: {"a1": "a1", "web_session": "sess", "webId": "webid"},
        )

        class FakeClient:
            def __init__(self, cookies):
                self.cookies = cookies

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def get_self_info(self):
                return {
                    "guest": False,
                    "basic_info": {
                        "user_id": "u-1",
                        "nickname": "Alice",
                        "red_id": "alice001",
                    },
                }

        monkeypatch.setattr("xhs_cli.commands.auth.XhsClient", FakeClient)

        result = runner.invoke(cli, ["auth", "doctor", "--yaml"])

        assert result.exit_code == 0
        payload = yaml.safe_load(result.output)
        assert payload["data"]["login_status"] == "valid"
        assert payload["data"]["authenticated"] is True
        assert payload["data"]["user"]["username"] == "alice001"
        assert payload["data"]["domains"]["main"]["login_status"] == "valid"
        assert payload["data"]["domains"]["creator"]["login_status"] == "unknown"

    def test_auth_doctor_separates_main_and_creator_domain_status(self, monkeypatch, tmp_path):
        monkeypatch.setattr("xhs_cli.commands.auth.get_cookie_path", lambda: tmp_path / "cookies.json")
        monkeypatch.setattr(
            "xhs_cli.commands.auth.load_saved_cookies",
            lambda: {"a1": "a1", "web_session": "sess", "webId": "webid"},
        )

        class FakeClient:
            def __init__(self, cookies):
                self.cookies = cookies

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def get_self_info(self):
                return {
                    "guest": False,
                    "basic_info": {
                        "user_id": "u-1",
                        "nickname": "Alice",
                        "red_id": "alice001",
                    },
                }

            def get_creator_note_list(self, page=0):
                raise SessionExpiredError()

        monkeypatch.setattr("xhs_cli.commands.auth.XhsClient", FakeClient)

        result = runner.invoke(cli, ["auth", "doctor", "--yaml"])

        assert result.exit_code == 0
        payload = yaml.safe_load(result.output)
        assert payload["data"]["login_status"] == "valid"
        assert payload["data"]["authenticated"] is True
        assert payload["data"]["domains"]["main"]["login_status"] == "valid"
        assert payload["data"]["domains"]["creator"]["login_status"] == "invalid"
        assert payload["data"]["domains"]["creator"]["authenticated"] is False
        assert "Session expired" in payload["data"]["domains"]["creator"]["validation_error"]["message"]
        assert payload["data"]["recommended_action"] == "none"

    def test_auth_import_file_supports_browser_cookie_list(self, monkeypatch, tmp_path):
        source_file = tmp_path / "cookies.json"
        source_file.write_text(json.dumps({
            "cookies": [
                {"name": "a1", "value": "a1-token"},
                {"name": "web_session", "value": "session-token"},
                {"name": "webId", "value": "webid-token"},
            ]
        }))

        saved = []
        monkeypatch.setattr("xhs_cli.commands.auth.get_cookie_path", lambda: tmp_path / "saved-cookies.json")
        monkeypatch.setattr("xhs_cli.commands.auth.save_cookies", lambda cookies: saved.append(cookies))

        class FakeClient:
            def __init__(self, cookies):
                self.cookies = cookies

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def get_self_info(self):
                return {
                    "guest": False,
                    "basic_info": {
                        "user_id": "u-1",
                        "nickname": "Alice",
                        "red_id": "alice001",
                    },
                }

        monkeypatch.setattr("xhs_cli.commands.auth.XhsClient", FakeClient)

        result = runner.invoke(cli, ["auth", "import", "--file", str(source_file), "--yaml"])

        assert result.exit_code == 0
        assert saved == [{
            "a1": "a1-token",
            "web_session": "session-token",
            "webId": "webid-token",
        }]
        payload = yaml.safe_load(result.output)
        assert payload["data"]["imported"] is True
        assert payload["data"]["imported_cookie_count"] == 3
        assert payload["data"]["validation"]["authenticated"] is True

    def test_auth_import_fields_supports_direct_values(self, monkeypatch, tmp_path):
        saved = []
        monkeypatch.setattr("xhs_cli.commands.auth.get_cookie_path", lambda: tmp_path / "saved-cookies.json")
        monkeypatch.setattr("xhs_cli.commands.auth.save_cookies", lambda cookies: saved.append(cookies))

        class FakeClient:
            def __init__(self, cookies):
                self.cookies = cookies

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def get_self_info(self):
                return {
                    "guest": False,
                    "basic_info": {
                        "user_id": "u-1",
                        "nickname": "Alice",
                        "red_id": "alice001",
                    },
                }

        monkeypatch.setattr("xhs_cli.commands.auth.XhsClient", FakeClient)

        result = runner.invoke(
            cli,
            [
                "auth",
                "import-fields",
                "--a1",
                "a1-token",
                "--web-session",
                "session-token",
                "--webid",
                "webid-token",
                "--yaml",
            ],
        )

        assert result.exit_code == 0
        assert saved == [{
            "a1": "a1-token",
            "web_session": "session-token",
            "webId": "webid-token",
        }]
        payload = yaml.safe_load(result.output)
        assert payload["data"]["source"] == "fields"
        assert payload["data"]["validation"]["authenticated"] is True

    def test_auth_import_fields_requires_minimum_cookies(self):
        result = runner.invoke(
            cli,
            ["auth", "import-fields", "--a1", "a1-token", "--yaml"],
        )

        assert result.exit_code != 0
        payload = yaml.safe_load(result.output)
        assert payload["ok"] is False
        assert payload["error"]["code"] == "api_error"
        assert "Missing required cookie fields" in payload["error"]["message"]

    def test_auth_import_fields_interactive_shows_all_fields_in_plain_text(self, monkeypatch, tmp_path):
        saved = []
        prompts = []
        monkeypatch.setattr("xhs_cli.commands.auth.get_cookie_path", lambda: tmp_path / "saved-cookies.json")
        monkeypatch.setattr("xhs_cli.commands.auth.save_cookies", lambda cookies: saved.append(cookies))

        class FakeClient:
            def __init__(self, cookies):
                self.cookies = cookies

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def get_self_info(self):
                return {
                    "guest": False,
                    "basic_info": {
                        "user_id": "u-1",
                        "nickname": "Alice",
                        "red_id": "alice001",
                    },
                }

        values = {
            "a1": "a1-token",
            "web_session": "session-token",
            "webId": "webid-token",
            "web_session_sec (optional)": "",
            "gid (optional)": "",
            "websectiga (optional)": "",
            "sec_poison_id (optional)": "",
            "xsecappid (optional)": "",
            "id_token (optional)": "",
        }

        def fake_prompt(text, **kwargs):
            prompts.append((text, kwargs))
            return values[text]

        monkeypatch.setattr("xhs_cli.commands.auth.XhsClient", FakeClient)
        monkeypatch.setattr("xhs_cli.commands.auth.click.prompt", fake_prompt)

        result = runner.invoke(cli, ["auth", "import-fields", "--interactive", "--yaml"])

        assert result.exit_code == 0
        assert saved == [{
            "a1": "a1-token",
            "web_session": "session-token",
            "webId": "webid-token",
        }]
        prompt_map = {text: kwargs for text, kwargs in prompts}
        for field in values:
            assert prompt_map[field].get("hide_input") is not True

    def test_auth_inspect_masks_cookie_values(self, monkeypatch, tmp_path):
        monkeypatch.setattr("xhs_cli.commands.auth.get_cookie_path", lambda: tmp_path / "cookies.json")
        monkeypatch.setattr(
            "xhs_cli.commands.auth.load_saved_cookies",
            lambda: {
                "a1": "abcdef1234567890",
                "web_session": "session-secret-value",
                "webId": "webid-value",
                "saved_at": 1776436245.0,
            },
        )

        result = runner.invoke(cli, ["auth", "inspect", "--yaml"])

        assert result.exit_code == 0
        payload = yaml.safe_load(result.output)
        assert payload["ok"] is True
        assert payload["data"]["cookies"]["a1"]["present"] is True
        assert payload["data"]["cookies"]["a1"]["fingerprint"] == "abcd…7890"
        assert payload["data"]["cookies"]["web_session"]["length"] == len("session-secret-value")
        assert payload["data"]["cookies"]["id_token"]["present"] is False

    def test_login_default_uses_headless_qr_and_prints_link(self, monkeypatch):
        monkeypatch.setattr(
            "xhs_cli.qr_login.qrcode_login",
            lambda **kwargs: _assert_qrcode_kwargs(True, **kwargs),
        )

        class FakeClient:
            def __init__(self, cookies):
                self.cookies = cookies

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def get_self_info(self):
                return {
                    "guest": False,
                    "basic_info": {
                        "user_id": "u-1",
                        "nickname": "Alice",
                        "red_id": "alice001",
                    },
                }
        
        monkeypatch.setattr("xhs_cli.commands.auth.XhsClient", FakeClient)

        result = runner.invoke(cli, ["login", "--yaml"])

        assert result.exit_code == 0
        payload = yaml.safe_load(result.output)
        assert payload["data"]["authenticated"] is True
        assert payload["data"]["user"]["username"] == "alice001"

    def test_login_qrcode_http_uses_http_flow(self, monkeypatch):
        monkeypatch.setattr(
            "xhs_cli.qr_login.qrcode_login",
            lambda **kwargs: _assert_qrcode_kwargs(False, **kwargs),
        )

        class FakeClient:
            def __init__(self, cookies):
                self.cookies = cookies

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def get_self_info(self):
                return {
                    "guest": False,
                    "basic_info": {
                        "user_id": "u-1",
                        "nickname": "Alice",
                        "red_id": "alice001",
                    },
                }

        monkeypatch.setattr("xhs_cli.commands.auth.XhsClient", FakeClient)

        result = runner.invoke(cli, ["login", "--qrcode-http", "--yaml"])

        assert result.exit_code == 0
        payload = yaml.safe_load(result.output)
        assert payload["data"]["authenticated"] is True
        assert payload["data"]["user"]["username"] == "alice001"

    def test_login_browser_invalid_session_points_to_qrcode_http(self, monkeypatch):
        monkeypatch.setattr(
            "xhs_cli.commands.auth.get_cookies",
            lambda cookie_source, force_refresh=False: (
                "chrome",
                {"a1": "a1", "web_session": "sess", "webId": "webid"},
            ),
        )

        class FakeClient:
            def __init__(self, cookies):
                self.cookies = cookies

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def get_self_info(self):
                return {"guest": True, "basic_info": {}}

        monkeypatch.setattr("xhs_cli.commands.auth.XhsClient", FakeClient)
        monkeypatch.setattr("xhs_cli.commands.auth.time.sleep", lambda _seconds: None)

        result = runner.invoke(cli, ["login", "--browser", "--yaml"])

        assert result.exit_code == 1
        combined = result.output + (str(result.exception) if result.exception else "")
        assert "xhs login" in combined
        assert "Cookies extracted from chrome" not in combined

    def test_login_browser_expired_session_points_to_default_login(self, monkeypatch):
        monkeypatch.setattr(
            "xhs_cli.commands.auth.get_cookies",
            lambda cookie_source, force_refresh=False: (
                "chrome",
                {"a1": "a1", "web_session": "sess", "webId": "webid"},
            ),
        )

        class FakeClient:
            def __init__(self, cookies):
                self.cookies = cookies

            def __enter__(self):
                raise SessionExpiredError()

            def __exit__(self, *args):
                return False

        monkeypatch.setattr("xhs_cli.commands.auth.XhsClient", FakeClient)

        result = runner.invoke(cli, ["login", "--browser", "--yaml"])

        assert result.exit_code == 1
        combined = result.output + (str(result.exception) if result.exception else "")
        assert "xhs login" in combined

    def test_login_qrcode_yaml_routes_status_lines_to_stderr(self, monkeypatch):
        def fake_qr(**kwargs):
            kwargs["on_status"]("QR URL: https://example.com/qr")
            return {
                "a1": "a1-http",
                "webId": "webid-http",
                "web_session": "session-http",
            }

        monkeypatch.setattr("xhs_cli.qr_login.qrcode_login", fake_qr)
        echo_calls = []
        original_echo = click.echo

        def fake_echo(message=None, file=None, nl=True, err=False, color=None):
            if message == "QR URL: https://example.com/qr":
                echo_calls.append(
                    {
                        "message": message,
                        "err": err,
                    }
                )
            return original_echo(message=message, file=file, nl=nl, err=err, color=color)

        monkeypatch.setattr("xhs_cli.commands.auth.click.echo", fake_echo)

        class FakeClient:
            def __init__(self, cookies):
                self.cookies = cookies

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def get_self_info(self):
                return {
                    "guest": False,
                    "basic_info": {
                        "user_id": "u-1",
                        "nickname": "Alice",
                        "red_id": "alice001",
                    },
                }

        monkeypatch.setattr("xhs_cli.commands.auth.XhsClient", FakeClient)

        result = runner.invoke(cli, ["login", "--qrcode-http", "--yaml"])

        assert result.exit_code == 0
        payload = yaml.safe_load(result.output)
        assert payload["data"]["authenticated"] is True
        assert {"message": "QR URL: https://example.com/qr", "err": True} in echo_calls

    def test_login_print_link_rejected_with_browser(self):
        result = runner.invoke(cli, ["login", "--browser", "--print-link"])

        assert result.exit_code != 0
        assert "--print-link cannot be used with --browser." in result.output

    def test_hot_help(self):
        result = runner.invoke(cli, ["hot", "--help"])
        assert result.exit_code == 0
        assert "category" in result.output.lower()

    def test_unread_help(self):
        result = runner.invoke(cli, ["unread", "--help"])
        assert result.exit_code == 0

    def test_my_notes_help(self):
        result = runner.invoke(cli, ["my-notes", "--help"])
        assert result.exit_code == 0

    def test_status_auto_yaml_when_stdout_is_not_tty(self, monkeypatch):
        monkeypatch.setenv("OUTPUT", "auto")
        monkeypatch.setattr(
            "xhs_cli.commands.auth.run_client_action",
            lambda ctx, action: {"nickname": "Alice", "red_id": "alice001"},
        )

        result = runner.invoke(cli, ["status"])

        assert result.exit_code == 0
        payload = yaml.safe_load(result.output)
        assert payload["ok"] is True
        assert payload["schema_version"] == "1"
        assert payload["data"]["authenticated"] is True
        assert payload["data"]["user"]["name"] == "Alice"

    def test_whoami_auto_yaml_when_stdout_is_not_tty(self, monkeypatch):
        monkeypatch.setenv("OUTPUT", "auto")
        monkeypatch.setattr(
            "xhs_cli.commands.auth.run_client_action",
            lambda ctx, action: {"nickname": "Alice", "red_id": "alice001", "user_id": "u-1"},
        )

        result = runner.invoke(cli, ["whoami"])

        assert result.exit_code == 0
        payload = yaml.safe_load(result.output)
        assert payload["ok"] is True
        assert payload["data"]["user"]["username"] == "alice001"

    def test_read_error_yaml_when_not_logged_in(self, monkeypatch):
        monkeypatch.setenv("OUTPUT", "auto")
        monkeypatch.setattr(
            "xhs_cli.commands._common.load_saved_cookies",
            lambda: None,
        )

        result = runner.invoke(cli, ["read", "abc", "--yaml"])

        assert result.exit_code != 0
        payload = yaml.safe_load(result.output)
        assert payload["ok"] is False
        assert payload["error"]["code"] == "not_authenticated"

    def test_status_reports_not_authenticated_when_session_expired(self, monkeypatch):
        monkeypatch.setenv("OUTPUT", "auto")

        def fake_run_client_action(ctx, action):
            raise SessionExpiredError()

        monkeypatch.setattr("xhs_cli.commands.auth.run_client_action", fake_run_client_action)

        result = runner.invoke(cli, ["status", "--yaml"])

        assert result.exit_code != 0
        payload = yaml.safe_load(result.output)
        assert payload["ok"] is False
        assert payload["error"]["code"] == "not_authenticated"

    def test_logout_supports_structured_output(self):
        from xhs_cli.commands import auth

        original_clear_cookies = auth.clear_cookies
        auth.clear_cookies = lambda: None
        try:
            result = runner.invoke(cli, ["logout", "--yaml"])
        finally:
            auth.clear_cookies = original_clear_cookies

        assert result.exit_code == 0
        payload = yaml.safe_load(result.output)
        assert payload["ok"] is True
        assert payload["data"]["logged_out"] is True

    def test_comments_rich_output_handles_string_reply_counts(self, monkeypatch):
        monkeypatch.setenv("OUTPUT", "rich")
        monkeypatch.setattr(
            "xhs_cli.commands.reading.run_client_action",
            lambda ctx, action: {
                "comments": [
                    {
                        "user_info": {"nickname": "tester"},
                        "content": "hello",
                        "like_count": "12",
                        "sub_comment_count": "2",
                    }
                ]
            },
        )

        result = runner.invoke(cli, ["comments", "note-123"])

        assert result.exit_code == 0
        assert "tester" in result.output
        assert "2 replies" in result.output

    def test_search_rich_output_shortens_visible_links(self, monkeypatch):
        monkeypatch.setenv("OUTPUT", "rich")
        monkeypatch.setattr(
            "xhs_cli.commands.reading.handle_command",
            lambda ctx, action, render, as_json, as_yaml: render({
                "items": [
                    {
                        "id": "69ad061d000000002603326d",
                        "xsec_token": "very-long-token-value",
                        "note_card": {
                            "title": "测试标题",
                            "user": {"nickname": "tester"},
                            "interact_info": {"liked_count": "12"},
                            "type": "normal",
                        },
                    }
                ],
                "has_more": False,
            }),
        )

        result = runner.invoke(cli, ["search", "openclaw"])

        assert result.exit_code == 0
        assert "search_result/69ad061d" in result.output
        assert "very-long-token-value" not in result.output

    def test_feed_rich_output_shortens_visible_links(self, monkeypatch):
        monkeypatch.setenv("OUTPUT", "rich")
        monkeypatch.setattr(
            "xhs_cli.commands.reading.handle_command",
            lambda ctx, action, render, as_json, as_yaml: render({
                "items": [
                    {
                        "id": "69ad061d000000002603326d",
                        "xsec_token": "another-very-long-token",
                        "note_card": {
                            "title": "推荐内容",
                            "user": {"nickname": "tester"},
                            "interact_info": {"liked_count": "9"},
                        },
                    }
                ]
            }),
        )

        result = runner.invoke(cli, ["feed"])

        assert result.exit_code == 0
        assert "explore/69ad061d" in result.output
        assert "another-very-long-token" not in result.output

    def test_read_help_mentions_short_index(self):
        result = runner.invoke(cli, ["read", "--help"])
        assert result.exit_code == 0
        assert "index" in result.output.lower()

    def test_comments_help_mentions_short_index(self):
        result = runner.invoke(cli, ["comments", "--help"])
        assert result.exit_code == 0
        assert "index" in result.output.lower()

    def test_read_index_resolves_note_context(self, monkeypatch):
        monkeypatch.setattr(
            "xhs_cli.note_refs.get_note_by_index",
            lambda idx: {
                "note_id": "note-abc",
                "xsec_token": "token-abc",
                "xsec_source": "pc_search",
            } if idx == 1 else None,
        )

        called = {}

        class FakeClient:
            def get_note_detail(self, note_id, **kwargs):
                called["note_id"] = note_id
                called["kwargs"] = kwargs
                return FAKE_NOTE_RESPONSE

        def fake_handle_command(ctx, action, render, as_json, as_yaml):
            action(FakeClient())
            return None

        monkeypatch.setattr("xhs_cli.commands.reading.handle_command", fake_handle_command)

        result = runner.invoke(cli, ["read", "1"])

        assert result.exit_code == 0
        assert called["note_id"] == "note-abc"
        assert called["kwargs"]["xsec_token"] == "token-abc"
        assert called["kwargs"]["xsec_source"] == "pc_search"

    def test_comments_index_resolves_note_context(self, monkeypatch):
        monkeypatch.setattr(
            "xhs_cli.note_refs.get_note_by_index",
            lambda idx: {
                "note_id": "note-abc",
                "xsec_token": "token-abc",
                "xsec_source": "pc_search",
            } if idx == 1 else None,
        )

        called = {}

        class FakeClient:
            def get_comments(self, note_id, cursor="", **kwargs):
                called["note_id"] = note_id
                called["cursor"] = cursor
                called["kwargs"] = kwargs
                return {"comments": []}

        def fake_run_client_action(ctx, action):
            return action(FakeClient())

        monkeypatch.setattr("xhs_cli.commands.reading.run_client_action", fake_run_client_action)

        result = runner.invoke(cli, ["comments", "1", "--yaml"])

        assert result.exit_code == 0
        assert called["note_id"] == "note-abc"
        assert called["kwargs"]["xsec_token"] == "token-abc"
        assert called["kwargs"]["xsec_source"] == "pc_search"

    def test_read_index_not_found_returns_usage_error(self, monkeypatch):
        monkeypatch.setattr("xhs_cli.note_refs.get_note_by_index", lambda idx: None)

        result = runner.invoke(cli, ["read", "999"])

        assert result.exit_code != 0
        assert "999" in result.output

    def test_search_empty_results_clear_previous_index(self, monkeypatch):
        from xhs_cli.note_refs import save_index_from_items

        saved = []
        monkeypatch.setattr("xhs_cli.note_refs.save_note_index", lambda items: saved.append(items))

        save_index_from_items({"items": []}, xsec_source="pc_search")

        assert saved == [[]]

    @pytest.mark.parametrize(
        ("command", "extra_args", "method_name"),
        [
            ("like", [], "like_note"),
            ("like", ["--undo"], "unlike_note"),
            ("favorite", [], "favorite_note"),
            ("unfavorite", [], "unfavorite_note"),
        ],
    )
    def test_short_index_resolves_for_note_actions(self, monkeypatch, command, extra_args, method_name):
        monkeypatch.setattr(
            "xhs_cli.note_refs.get_note_by_index",
            lambda idx: {
                "note_id": "note-abc",
                "xsec_token": "token-abc",
                "xsec_source": "pc_search",
            } if idx == 1 else None,
        )

        called = {}

        class FakeClient:
            def __getattr__(self, name):
                if name != method_name:
                    raise AttributeError(name)

                def _call(note_id):
                    called["method"] = name
                    called["note_id"] = note_id
                    return {"ok": True}

                return _call

        def fake_handle_command(ctx, action, render, as_json, as_yaml):
            action(FakeClient())
            return None

        monkeypatch.setattr("xhs_cli.commands.interactions.handle_command", fake_handle_command)

        result = runner.invoke(cli, [command, "1", *extra_args])

        assert result.exit_code == 0
        assert called == {"method": method_name, "note_id": "note-abc"}

    def test_short_index_resolves_for_comment(self, monkeypatch):
        monkeypatch.setattr(
            "xhs_cli.note_refs.get_note_by_index",
            lambda idx: {
                "note_id": "note-abc",
                "xsec_token": "token-abc",
                "xsec_source": "pc_search",
            } if idx == 1 else None,
        )

        called = {}

        class FakeClient:
            def post_comment(self, note_id, content):
                called["note_id"] = note_id
                called["content"] = content
                return {"ok": True}

        def fake_handle_command(ctx, action, render, as_json, as_yaml):
            action(FakeClient())
            return None

        monkeypatch.setattr("xhs_cli.commands.interactions.handle_command", fake_handle_command)

        result = runner.invoke(cli, ["comment", "1", "-c", "hello"])

        assert result.exit_code == 0
        assert called == {"note_id": "note-abc", "content": "hello"}

    def test_my_notes_saves_index_entries(self, monkeypatch):
        saved = []
        monkeypatch.setattr("xhs_cli.note_refs.save_note_index", lambda items: saved.append(items))

        def fake_handle_command(ctx, action, render, as_json, as_yaml):
            class FakeClient:
                def get_creator_note_list(self, page=0):
                    return {
                        "note_list": [
                            {"note_id": "note-1"},
                            {"id": "note-2"},
                        ]
                    }

            data = action(FakeClient())
            render(data)
            return None

        monkeypatch.setattr("xhs_cli.commands.creator.handle_command", fake_handle_command)

        result = runner.invoke(cli, ["my-notes"])

        assert result.exit_code == 0
        assert saved == [[
            {"note_id": "note-1", "xsec_token": "", "xsec_source": ""},
            {"note_id": "note-2", "xsec_token": "", "xsec_source": ""},
        ]]
