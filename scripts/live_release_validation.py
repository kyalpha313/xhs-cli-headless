from __future__ import annotations

import argparse
import base64
import tempfile
import time
from pathlib import Path

import yaml
from click.testing import CliRunner

from xhs_cli.cli import cli
from xhs_cli.cookies import get_cookie_path, load_saved_cookies, save_cookies


runner = CliRunner()


def normalize_output(text: str):
    text = text.strip()
    if not text:
        return None
    try:
        return yaml.safe_load(text)
    except Exception:
        return text


def extract_error(payload):
    if isinstance(payload, dict) and payload.get("ok") is False:
        err = payload.get("error") or {}
        return err.get("code"), err.get("message")
    return None, None


def extract_data(payload):
    if isinstance(payload, dict) and payload.get("ok") is True:
        return payload.get("data")
    return None


def find_first_comment_id(data):
    if not isinstance(data, dict):
        return ""
    for key in ("comments", "items", "comment_list"):
        value = data.get(key)
        if not isinstance(value, list):
            continue
        for item in value:
            if not isinstance(item, dict):
                continue
            for candidate_key in ("id", "comment_id"):
                if item.get(candidate_key):
                    return str(item[candidate_key])
            comment_info = item.get("comment_info") or {}
            for candidate_key in ("id", "comment_id"):
                if comment_info.get(candidate_key):
                    return str(comment_info[candidate_key])
    return ""


def find_user_id_from_search_user(data):
    if not isinstance(data, dict):
        return ""
    for key in ("user_info_dtos", "users", "items"):
        users = data.get(key)
        if not isinstance(users, list):
            continue
        for item in users:
            if not isinstance(item, dict):
                continue
            base = item.get("user_base_dto") or item.get("basic_info") or item
            user_id = base.get("user_id") or base.get("id")
            if user_id:
                return str(user_id)
    return ""


def find_note_id(data):
    if not isinstance(data, dict):
        return ""
    for key in ("note_id", "id"):
        if data.get(key):
            return str(data[key])
    for key in ("note", "data", "note_card"):
        nested = data.get(key)
        if not isinstance(nested, dict):
            continue
        for candidate_key in ("note_id", "id"):
            if nested.get(candidate_key):
                return str(nested[candidate_key])
    return ""


def invoke(*args: str):
    result = runner.invoke(cli, [*args, "--yaml"])
    payload = normalize_output(result.output)
    return result, payload


def record(report, name: str, result, payload, note: str = ""):
    error_code, error_message = extract_error(payload)
    status = "passed" if result.exit_code == 0 and error_code is None else "failed"
    report["results"].append(
        {
            "name": name,
            "status": status,
            "exit_code": result.exit_code,
            "error_code": error_code,
            "error_message": error_message,
            "note": note,
        }
    )
    return status == "passed"


def record_skip(report, name: str, note: str):
    report["results"].append(
        {
            "name": name,
            "status": "skipped",
            "exit_code": None,
            "error_code": None,
            "error_message": None,
            "note": note,
        }
    )


def main():
    parser = argparse.ArgumentParser(description="Live release validation for xhs CLI")
    parser.add_argument(
        "--enable-creator-write-tests",
        action="store_true",
        help="Run post/delete validation. Keep disabled unless delete rollback has been verified for the current session type.",
    )
    parser.add_argument(
        "--enable-browser-login-check",
        action="store_true",
        help="Run browser cookie extraction login check at the end and then restore the saved session.",
    )
    args = parser.parse_args()

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "results": [],
        "summary": {},
        "options": {
            "enable_creator_write_tests": args.enable_creator_write_tests,
            "enable_browser_login_check": args.enable_browser_login_check,
        },
    }

    self_info = {}
    note_id = ""
    xsec_token = ""
    parent_comment_id = ""
    other_user_id = ""

    baseline_commands = [
        ("status", ["status"], "baseline auth check"),
        ("whoami", ["whoami"], ""),
        ("search", ["search", "测试"], "seed note target"),
        ("search-user", ["search-user", "美食达人"], ""),
        ("topics", ["topics", "旅行"], ""),
        ("feed", ["feed"], ""),
        ("hot", ["hot", "-c", "food"], ""),
        ("favorites", ["favorites"], ""),
        ("likes", ["likes"], ""),
        ("my-notes", ["my-notes"], ""),
        ("notifications-mentions", ["notifications", "--type", "mentions", "--num", "5"], ""),
        ("notifications-likes", ["notifications", "--type", "likes", "--num", "5"], ""),
        ("notifications-connections", ["notifications", "--type", "connections", "--num", "5"], ""),
        ("unread", ["unread"], ""),
    ]

    saved_search_user_payload = None

    for name, argv, note in baseline_commands:
        result, payload = invoke(*argv)
        ok = record(report, name, result, payload, note=note)
        data = extract_data(payload)
        if name == "whoami" and ok and isinstance(data, dict):
            self_info = data
        if name == "search" and ok and isinstance(data, dict):
            items = data.get("items") or []
            if items:
                first = items[0]
                note_card = first.get("note_card") or {}
                note_id = str(first.get("id") or note_card.get("note_id") or "")
                xsec_token = str(first.get("xsec_token") or note_card.get("xsec_token") or "")
                author = note_card.get("user") or {}
                author_user_id = str(author.get("user_id") or "")
                if author_user_id:
                    other_user_id = author_user_id
        if name == "search-user":
            saved_search_user_payload = payload

    self_user_id = str(self_info.get("id") or self_info.get("user_id") or "")

    if saved_search_user_payload:
        found = find_user_id_from_search_user(extract_data(saved_search_user_payload) or {})
        if found and found != self_user_id:
            other_user_id = found

    if self_user_id:
        result, payload = invoke("user", self_user_id)
        record(report, "user", result, payload, note="self user id")
        result, payload = invoke("user-posts", self_user_id)
        record(report, "user-posts", result, payload, note="self user id")
    else:
        record_skip(report, "user", "Could not determine current user id")
        record_skip(report, "user-posts", "Could not determine current user id")

    if note_id:
        if xsec_token:
            result, payload = invoke("read", note_id, "--xsec-token", xsec_token)
        else:
            result, payload = invoke("read", note_id)
        record(report, "read", result, payload)

        if xsec_token:
            result, payload = invoke("comments", note_id, "--xsec-token", xsec_token)
        else:
            result, payload = invoke("comments", note_id)
        comments_ok = record(report, "comments", result, payload)
        if comments_ok:
            parent_comment_id = find_first_comment_id(extract_data(payload) or {})
        if parent_comment_id:
            result, payload = invoke("sub-comments", note_id, parent_comment_id)
            record(report, "sub-comments", result, payload, note="first top-level comment")
        else:
            record_skip(report, "sub-comments", "No top-level comment id found")
    else:
        for name in ("read", "comments", "sub-comments"):
            record_skip(report, name, "No note target discovered from search")

    if note_id:
        result, payload = invoke("like", note_id)
        record(report, "like", result, payload, note="write test; rolled back by like --undo")
        result, payload = invoke("like", note_id, "--undo")
        record(report, "like-undo", result, payload, note="rollback for like")

        result, payload = invoke("favorite", note_id)
        record(report, "favorite", result, payload, note="write test; rolled back by unfavorite")
        result, payload = invoke("unfavorite", note_id)
        record(report, "unfavorite", result, payload, note="rollback for favorite")

        unique = str(int(time.time()))
        result, payload = invoke("comment", note_id, "-c", f"release test {unique}")
        comment_ok = record(report, "comment", result, payload, note="write test; will delete if comment id is returned")
        comment_id = ""
        if comment_ok:
            data = extract_data(payload) or {}
            comment = data.get("comment") or {}
            if isinstance(comment, dict):
                comment_id = str(comment.get("id") or comment.get("comment_id") or "")
            if not comment_id:
                comment_id = str(data.get("id") or data.get("comment_id") or "")
        if comment_id:
            result, payload = invoke("delete-comment", note_id, comment_id, "-y")
            record(report, "delete-comment", result, payload, note="rollback for comment")
        else:
            record_skip(report, "delete-comment", "Comment id not returned; no delete target available")

        if parent_comment_id:
            result, payload = invoke("reply", note_id, "--comment-id", parent_comment_id, "-c", f"release reply {unique}")
            reply_ok = record(report, "reply", result, payload, note="write test; will delete if reply id is returned")
            reply_id = ""
            if reply_ok:
                data = extract_data(payload) or {}
                comment = data.get("comment") or {}
                if isinstance(comment, dict):
                    reply_id = str(comment.get("id") or comment.get("comment_id") or "")
                if not reply_id:
                    reply_id = str(data.get("id") or data.get("comment_id") or "")
            if reply_id:
                result, payload = invoke("delete-comment", note_id, reply_id, "-y")
                record(report, "delete-comment-reply", result, payload, note="rollback for reply")
            else:
                record_skip(report, "delete-comment-reply", "Reply id not returned; no delete target available")
        else:
            record_skip(report, "reply", "No parent comment id available")
            record_skip(report, "delete-comment-reply", "No reply created")
    else:
        for name in (
            "like",
            "like-undo",
            "favorite",
            "unfavorite",
            "comment",
            "delete-comment",
            "reply",
            "delete-comment-reply",
        ):
            record_skip(report, name, "No note target discovered from search")

    if other_user_id and other_user_id != self_user_id:
        result, payload = invoke("follow", other_user_id)
        record(report, "follow", result, payload, note="write test; rolled back by unfollow")
        result, payload = invoke("unfollow", other_user_id)
        record(report, "unfollow", result, payload, note="rollback for follow")
    else:
        record_skip(report, "follow", "No safe non-self user target found")
        record_skip(report, "unfollow", "No safe non-self user target found")

    if args.enable_creator_write_tests:
        png_path = Path(tempfile.gettempdir()) / "xhs-release-test.png"
        png_path.write_bytes(
            base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+cJ6kAAAAASUVORK5CYII="
            )
        )
        post_title = f"CLI Release Test {int(time.time())}"
        result, payload = invoke(
            "post",
            "--title",
            post_title,
            "--body",
            "Temporary private release validation post",
            "--images",
            str(png_path),
            "--private",
        )
        post_ok = record(report, "post", result, payload, note="disposable private note")
        post_note_id = find_note_id(extract_data(payload) or {}) if post_ok else ""
        if post_note_id:
            result, payload = invoke("delete", post_note_id, "-y")
            record(report, "delete-post", result, payload, note="rollback for private test post")
        else:
            record_skip(report, "delete-post", "Post failed or note id not returned")
    else:
        record_skip(
            report,
            "post",
            "Skipped by design. Enable only after creator delete rollback is verified for the current login/session type.",
        )
        record_skip(
            report,
            "delete-post",
            "Skipped because creator write tests are disabled.",
        )

    if args.enable_browser_login_check:
        # Browser extraction can overwrite the currently valid saved session, so back it up
        # and restore it after the check to keep the rest of the release environment stable.
        backup_cookies = load_saved_cookies() or {}
        result, payload = invoke("login")
        record(report, "login-browser", result, payload, note="browser extraction path; saved session restored afterwards")
        if backup_cookies:
            save_cookies({k: v for k, v in backup_cookies.items() if k != "saved_at"})
        else:
            cookie_path = get_cookie_path()
            if cookie_path.exists():
                cookie_path.unlink()
    else:
        record_skip(
            report,
            "login-browser",
            "Skipped by design to avoid overwriting the validated session during the main release pass.",
        )

    record_skip(report, "login --qrcode", "Manual browser-assisted QR scan not re-run in this automated pass")

    summary = {}
    for item in report["results"]:
        summary[item["status"]] = summary.get(item["status"], 0) + 1
    report["summary"] = summary
    print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False))


if __name__ == "__main__":
    main()
