"""Custom exceptions for XHS API client."""


class XhsApiError(Exception):
    """Base exception for XHS API errors."""

    def __init__(
        self,
        message: str,
        code: int | str | None = None,
        response: dict | None = None,
        recovery: dict | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.response = response
        self.recovery = recovery


AUTH_RECOVERY = {
    "summary": "当前没有可用的小红书登录态，Agent 应先恢复会话再重试业务命令。",
    "steps": [
        {
            "command": "xhs auth doctor --json",
            "description": "诊断本地 cookies 和主站 / creator 会话是否可用。",
        },
        {
            "command": "xhs login",
            "description": "通过终端二维码和登录链接重新登录，适合首次登录或会话过期。",
        },
        {
            "command": "xhs auth import --file <cookies.json>",
            "description": "导入已有 cookies 文件，适合从浏览器或其他机器迁移登录态。",
        },
        {
            "command": "xhs auth import-fields --interactive",
            "description": "交互式粘贴 a1、web_session、webId 等字段恢复会话。",
        },
        {
            "command": "xhs status --json",
            "description": "恢复后验证当前账号是否可用。",
        },
    ],
}


class NeedVerifyError(XhsApiError):
    """Raised when XHS requires captcha verification."""

    def __init__(self, verify_type: str, verify_uuid: str):
        super().__init__(f"Captcha required: type={verify_type}, uuid={verify_uuid}")
        self.verify_type = verify_type
        self.verify_uuid = verify_uuid


class SessionExpiredError(XhsApiError):
    """Raised when the session has expired."""

    def __init__(self, message: str = "Session expired — please re-login with: xhs login", code: int = -100):
        super().__init__(
            message,
            code=code,
            recovery=AUTH_RECOVERY,
        )


class IpBlockedError(XhsApiError):
    """Raised when IP is blocked by XHS."""

    def __init__(self):
        super().__init__("IP blocked by XHS — try a different network", code=300012)


class SignatureError(XhsApiError):
    """Raised when signature verification fails."""

    def __init__(self):
        super().__init__("Signature verification failed", code=300015)


class UnsupportedOperationError(XhsApiError):
    """Raised when the current web API no longer supports an exposed CLI action."""

    def __init__(self, message: str):
        super().__init__(message, code="unsupported_operation")


class NoCookieError(XhsApiError):
    """Raised when no valid cookies are found."""

    def __init__(self, source: str, details: str = ""):
        if source == "saved":
            msg = "No saved login session was found."
        elif source == "auto":
            msg = "No 'a1' cookie found for xiaohongshu.com in any installed browser."
        else:
            msg = f"No 'a1' cookie found for xiaohongshu.com in {source}."
        if details:
            msg += f"\n{details}"
        msg += "\n\nTroubleshooting:\n"
        if source == "saved":
            msg += "  1. Run: xhs login\n"
            msg += "  2. Or import an existing session: xhs auth import --file cookies.json\n"
            msg += "  3. If you must reuse browser cookies: xhs login --browser --cookie-source <browser>"
        else:
            msg += "  1. Open a browser and visit https://www.xiaohongshu.com/\n"
            msg += "  2. Make sure you are logged in\n"
            msg += "  3. Try: xhs login --browser --cookie-source <browser>"
        super().__init__(msg, recovery=AUTH_RECOVERY)
