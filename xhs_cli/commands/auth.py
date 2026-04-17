"""Authentication commands and saved-session utilities."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import click

from ..client import XhsClient
from ..command_normalizers import normalize_xhs_user_payload
from ..cookies import clear_cookies, get_cookie_path, get_cookies, load_saved_cookies, save_cookies
from ..exceptions import SessionExpiredError, XhsApiError
from ..formatter import (
    console,
    maybe_print_structured,
    print_success,
    render_user_info,
    success_payload,
)
from ._common import handle_errors, run_client_action, structured_output_options

AUTH_REQUIRED_COOKIES = ("a1", "web_session", "webId")
AUTH_RECOMMENDED_COOKIES = (
    "web_session_sec",
    "gid",
    "websectiga",
    "sec_poison_id",
    "xsecappid",
)
AUTH_SENSITIVE_COOKIES = (
    "a1",
    "web_session",
    "web_session_sec",
    "webId",
    "id_token",
    "websectiga",
    "sec_poison_id",
    "xsecappid",
)


def _emit_payload(data: dict[str, object], *, as_json: bool, as_yaml: bool) -> bool:
    """Emit a structured success payload when requested."""
    return maybe_print_structured(success_payload(data), as_json=as_json, as_yaml=as_yaml)


def _is_valid_login(user: dict[str, object]) -> bool:
    """Check whether the normalized user payload represents a real logged-in session."""
    if user.get("guest"):
        return False
    nickname = user.get("nickname", "")
    return bool(nickname and nickname != "Unknown")


def _print_login_success(user: dict[str, object]) -> None:
    """Print a concise login success message."""
    print_success(f"Logged in as: {user['nickname']} (ID: {user['red_id']})")


def _print_status_summary(user: dict[str, object]) -> None:
    """Render a short authenticated-user summary."""
    console.print("[bold green]✓ Logged in[/bold green]")
    console.print(f"  昵称: [bold]{user['nickname']}[/bold]")
    if user["red_id"]:
        console.print(f"  小红书号: {user['red_id']}")
    if user["ip_location"]:
        console.print(f"  IP 属地: {user['ip_location']}")
    if user["desc"]:
        console.print(f"  简介: {user['desc']}")


def _normalize_cookie_map(payload: Any) -> dict[str, str]:
    """Normalize supported cookie import payloads into the local storage shape."""
    if isinstance(payload, dict) and "cookies" in payload:
        return _normalize_cookie_map(payload["cookies"])

    if isinstance(payload, list):
        cookies: dict[str, str] = {}
        for item in payload:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            value = str(item.get("value", "")).strip()
            if name and value:
                cookies[name] = value
        return cookies

    if isinstance(payload, dict):
        cookies = {}
        for key, value in payload.items():
            name = str(key).strip()
            if not name or name == "saved_at" or value in (None, ""):
                continue
            if isinstance(value, (str, int, float, bool)):
                cookies[name] = str(value).strip()
        return {key: value for key, value in cookies.items() if value}

    raise XhsApiError("Unsupported cookie file format. Expected a JSON object or browser-cookie list.")


def _auth_recommendation(*, has_cookies: bool, missing_required: list[str], authenticated: bool) -> str:
    if authenticated:
        return "none"
    if not has_cookies:
        return "import_cookies"
    if missing_required:
        return "reimport_cookies"
    return "refresh_or_relogin"


def _doctor_payload(cookies: dict[str, str] | None) -> dict[str, Any]:
    """Build the diagnostic payload for the saved authentication state."""
    cookie_path = get_cookie_path()
    cookies = cookies or {}
    present_required = [name for name in AUTH_REQUIRED_COOKIES if cookies.get(name)]
    missing_required = [name for name in AUTH_REQUIRED_COOKIES if name not in present_required]
    present_recommended = [name for name in AUTH_RECOMMENDED_COOKIES if cookies.get(name)]

    payload: dict[str, Any] = {
        "cookie_path": str(cookie_path),
        "cookies_file_found": cookie_path.exists(),
        "cookie_count": len(cookies),
        "required_cookies_present": present_required,
        "required_cookies_missing": missing_required,
        "recommended_cookies_present": present_recommended,
        "login_status": "missing",
        "authenticated": False,
        "recommended_action": _auth_recommendation(
            has_cookies=bool(cookies),
            missing_required=missing_required,
            authenticated=False,
        ),
    }

    if not cookies:
        return payload

    if missing_required:
        payload["login_status"] = "partial"

    try:
        with XhsClient(cookies) as client:
            info = client.get_self_info()
        user = normalize_xhs_user_payload(info)
        payload["user"] = user
        payload["authenticated"] = _is_valid_login(user)
        if payload["authenticated"]:
            payload["login_status"] = "valid"
        elif payload["login_status"] == "missing":
            payload["login_status"] = "invalid"
    except XhsApiError as exc:
        if payload["login_status"] == "missing":
            payload["login_status"] = "invalid"
        payload["validation_error"] = {
            "code": exc.code or "api_error",
            "message": str(exc),
        }

    payload["recommended_action"] = _auth_recommendation(
        has_cookies=bool(cookies),
        missing_required=missing_required,
        authenticated=bool(payload["authenticated"]),
    )
    return payload


def _render_doctor_summary(data: dict[str, Any]) -> None:
    """Render a human-friendly auth diagnostic summary."""
    status = data["login_status"]
    authenticated = data["authenticated"]
    marker = "[bold green]✓[/bold green]" if authenticated else "[bold yellow]![/bold yellow]"
    console.print(f"{marker} auth doctor: {status}")
    console.print(f"  cookies file: {data['cookie_path']}")
    console.print(f"  required cookies present: {', '.join(data['required_cookies_present']) or '(none)'}")
    if data["required_cookies_missing"]:
        console.print(f"  missing required: {', '.join(data['required_cookies_missing'])}")
    if data.get("user", {}).get("nickname"):
        console.print(f"  current user: {data['user']['nickname']}")
    if data.get("validation_error"):
        console.print(f"  validation error: {data['validation_error']['message']}")
    console.print(f"  recommended action: {data['recommended_action']}")


def _render_import_summary(data: dict[str, Any]) -> None:
    """Render a concise import summary after saving cookies."""
    validation = data["validation"]
    print_success(f"Imported {data['imported_cookie_count']} cookies into {data['cookie_path']}")
    console.print(f"  login status: {validation['login_status']}")
    console.print(f"  recommended action: {validation['recommended_action']}")
    if validation.get("user", {}).get("nickname"):
        console.print(f"  current user: {validation['user']['nickname']}")
    elif validation.get("validation_error"):
        console.print(f"  validation error: {validation['validation_error']['message']}")


def _cookie_fingerprint(value: str) -> str:
    """Return a safe fingerprint for displaying sensitive cookie values."""
    if not value:
        return ""
    if len(value) <= 10:
        return f"{value[:2]}…{value[-2:]}"
    return f"{value[:4]}…{value[-4:]}"


def _inspect_payload(cookies: dict[str, str] | None) -> dict[str, Any]:
    cookie_path = get_cookie_path()
    cookies = cookies or {}

    present = {name: bool(cookies.get(name)) for name in AUTH_SENSITIVE_COOKIES}
    summary = {
        name: {
            "present": bool(cookies.get(name)),
            "length": len(cookies.get(name, "") or ""),
            "fingerprint": _cookie_fingerprint(cookies.get(name, "") or "") if cookies.get(name) else "",
        }
        for name in AUTH_SENSITIVE_COOKIES
    }

    saved_at = cookies.get("saved_at")
    try:
        saved_at_ts = float(saved_at) if saved_at is not None else None
    except (TypeError, ValueError):
        saved_at_ts = None

    missing_required = [name for name in AUTH_REQUIRED_COOKIES if not cookies.get(name)]
    return {
        "cookie_path": str(cookie_path),
        "cookies_file_found": cookie_path.exists(),
        "cookie_count": len(cookies),
        "saved_at": saved_at_ts,
        "required_cookies_missing": missing_required,
        "cookies": summary,
        "recommended_action": _auth_recommendation(
            has_cookies=bool(cookies),
            missing_required=missing_required,
            authenticated=False,
        ),
    }


def _render_inspect_summary(data: dict[str, Any]) -> None:
    console.print("[bold]auth inspect[/bold]")
    console.print(f"  cookies file: {data['cookie_path']}")
    console.print(f"  cookie count: {data['cookie_count']}")
    if data.get("saved_at"):
        console.print(f"  saved_at: {data['saved_at']}")
    if data["required_cookies_missing"]:
        console.print(f"  missing required: {', '.join(data['required_cookies_missing'])}")
    console.print(f"  recommended action: {data['recommended_action']}")

    console.print("  cookie fields:")
    for name, info in data["cookies"].items():
        if info["present"]:
            console.print(f"    - {name}: present (len={info['length']}, fp={info['fingerprint']})")
        else:
            console.print(f"    - {name}: missing")


@click.group()
def auth():
    """Authentication utilities for saved cookies and diagnostics."""


@click.command()
@click.option(
    "--cookie-source",
    type=str,
    default=None,
    help="Browser to read cookies from (default: auto-detect all installed browsers)",
)
@structured_output_options
@click.option("--qrcode", "use_qrcode", is_flag=True, default=False,
              help="Login via QR code (scan with Xiaohongshu app)")
@click.option("--qrcode-http", "use_qrcode_http", is_flag=True, default=False,
              help="Force the legacy pure-HTTP QR login flow")
@click.option("--print-link", is_flag=True, default=False,
              help="Always print the QR login URL in addition to terminal QR rendering")
@click.pass_context
def login(
    ctx,
    cookie_source: str | None,
    as_json: bool,
    as_yaml: bool,
    use_qrcode: bool,
    use_qrcode_http: bool,
    print_link: bool,
):
    """Log in by extracting cookies from browser, or via QR code."""

    def _qr_status(msg: str) -> None:
        click.echo(msg, err=as_json or as_yaml)

    if print_link and not (use_qrcode or use_qrcode_http):
        raise click.UsageError("--print-link must be used with --qrcode or --qrcode-http.")

    if use_qrcode or use_qrcode_http:
        def _login_with_qrcode() -> None:
            from ..qr_login import qrcode_login

            cookies = qrcode_login(
                prefer_browser_assisted=not use_qrcode_http,
                print_link=print_link,
                on_status=_qr_status,
            )

            # Verify by fetching user info (may return guest=true briefly)
            import time
            time.sleep(1)  # brief delay for session propagation
            with XhsClient(cookies) as client:
                info = client.get_self_info()
            user = normalize_xhs_user_payload(info)

            if user["guest"]:
                # Session not yet propagated; still valid
                if not _emit_payload(
                    {"authenticated": True, "user": {"id": user["id"]}},
                    as_json=as_json,
                    as_yaml=as_yaml,
                ):
                    print_success("Logged in (session saved)")
            else:
                if not _emit_payload({"authenticated": True, "user": user}, as_json=as_json, as_yaml=as_yaml):
                    _print_login_success(user)

        handle_errors(
            _login_with_qrcode,
            as_json=as_json,
            as_yaml=as_yaml,
            prefix="QR login failed",
        )
        return

    # Browser cookie extraction (default)
    if cookie_source is None:
        cookie_source = ctx.obj.get("cookie_source", "auto") if ctx.obj else "auto"

    def _login_with_browser() -> None:
        browser, cookies = get_cookies(cookie_source, force_refresh=True)
        # Verify by fetching user info, retry once if session not yet propagated
        try:
            with XhsClient(cookies) as client:
                info = client.get_self_info()
        except SessionExpiredError as exc:
            raise XhsApiError(
                f"Browser cookies were extracted from {browser}, but the session is expired. "
                "Try: xhs login --qrcode-http --print-link"
            ) from exc
        user = normalize_xhs_user_payload(info)

        if not _is_valid_login(user):
            time.sleep(2.5)
            with XhsClient(cookies) as client:
                info = client.get_self_info()
            user = normalize_xhs_user_payload(info)

        if not _is_valid_login(user):
            raise XhsApiError(
                f"Browser cookies were extracted from {browser}, but the session appears expired or invalid "
                "(guest or incomplete profile). Try: xhs login --qrcode-http --print-link"
            )

        print_success(f"Cookies extracted from {browser}")
        if not _emit_payload({"authenticated": True, "user": user}, as_json=as_json, as_yaml=as_yaml):
            _print_login_success(user)

    handle_errors(
        _login_with_browser,
        as_json=as_json,
        as_yaml=as_yaml,
        prefix="Login verification failed",
    )


@click.command()
@structured_output_options
@click.pass_context
def status(ctx, as_json: bool, as_yaml: bool):
    """Check current login status and user info."""
    def _show_status() -> None:
        info = run_client_action(ctx, lambda client: client.get_self_info())
        user = normalize_xhs_user_payload(info)

        if not _emit_payload({"authenticated": True, "user": user}, as_json=as_json, as_yaml=as_yaml):
            _print_status_summary(user)

    handle_errors(_show_status, as_json=as_json, as_yaml=as_yaml, prefix="Status check failed")


@click.command()
@structured_output_options
@click.pass_context
def logout(ctx, as_json: bool, as_yaml: bool):
    """Clear saved cookies and log out."""
    clear_cookies()
    if not _emit_payload({"logged_out": True}, as_json=as_json, as_yaml=as_yaml):
        print_success("Logged out — cookies cleared")


@click.command()
@structured_output_options
@click.pass_context
def whoami(ctx, as_json: bool, as_yaml: bool):
    """Show detailed profile of current user (level, fans, likes)."""
    def _show_profile() -> None:
        info = run_client_action(ctx, lambda client: client.get_self_info())
        user = normalize_xhs_user_payload(info)

        if not _emit_payload({"user": user}, as_json=as_json, as_yaml=as_yaml):
            render_user_info(info)

    handle_errors(_show_profile, as_json=as_json, as_yaml=as_yaml, prefix="Failed to get profile")


@auth.command("doctor")
@structured_output_options
def auth_doctor(as_json: bool, as_yaml: bool):
    """Inspect saved cookies and verify whether the current session is usable."""

    def _run() -> None:
        payload = _doctor_payload(load_saved_cookies())
        if not _emit_payload(payload, as_json=as_json, as_yaml=as_yaml):
            _render_doctor_summary(payload)

    handle_errors(_run, as_json=as_json, as_yaml=as_yaml, prefix="Auth doctor failed")


@auth.command("import")
@click.option("--file", "cookie_file", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@structured_output_options
def auth_import(cookie_file: Path, as_json: bool, as_yaml: bool):
    """Import cookies from a JSON file and immediately validate the session."""

    def _run() -> None:
        try:
            payload = json.loads(cookie_file.read_text())
        except OSError as exc:
            raise XhsApiError(f"Failed to read cookie file: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise XhsApiError(f"Cookie file is not valid JSON: {exc}") from exc

        cookies = _normalize_cookie_map(payload)
        if not cookies:
            raise XhsApiError("Cookie file did not contain any usable cookie fields.")

        save_cookies(cookies)
        validation = _doctor_payload(cookies)
        data = {
            "imported": True,
            "cookie_path": str(get_cookie_path()),
            "imported_cookie_count": len(cookies),
            "imported_cookie_names": sorted(cookies.keys()),
            "validation": validation,
        }
        if not _emit_payload(data, as_json=as_json, as_yaml=as_yaml):
            _render_import_summary(data)

    handle_errors(_run, as_json=as_json, as_yaml=as_yaml, prefix="Cookie import failed")


@auth.command("inspect")
@structured_output_options
def auth_inspect(as_json: bool, as_yaml: bool):
    """Inspect saved cookies without printing sensitive values."""

    def _run() -> None:
        payload = _inspect_payload(load_saved_cookies())
        if not _emit_payload(payload, as_json=as_json, as_yaml=as_yaml):
            _render_inspect_summary(payload)

    handle_errors(_run, as_json=as_json, as_yaml=as_yaml, prefix="Auth inspect failed")
