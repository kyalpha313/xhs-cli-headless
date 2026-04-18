"""Constants for XHS API client."""

EDITH_HOST = "https://edith.xiaohongshu.com"
CREATOR_HOST = "https://creator.xiaohongshu.com"
HOME_URL = "https://www.xiaohongshu.com"
UPLOAD_HOST = "https://ros-upload.xiaohongshu.com"

CHROME_VERSION = "145"
WINDOWS_CHROME_VERSION = "142"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    f"Chrome/{CHROME_VERSION}.0.0.0 Safari/537.36"
)
WINDOWS_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    f"Chrome/{WINDOWS_CHROME_VERSION}.0.0.0 Safari/537.36 "
    f"Edg/{WINDOWS_CHROME_VERSION}.0.0.0"
)
WINDOWS_SEC_CH_UA = (
    f'"Not:A-Brand";v="99", "Google Chrome";v="{WINDOWS_CHROME_VERSION}", '
    f'"Chromium";v="{WINDOWS_CHROME_VERSION}", "Microsoft Edge";v="{WINDOWS_CHROME_VERSION}"'
)

SDK_VERSION = "4.2.6"
APP_ID = "xhs-pc-web"
PLATFORM = "macOS"
WINDOWS_PLATFORM = "Windows"

# Config directory
CONFIG_DIR_NAME = ".xiaohongshu-cli"
COOKIE_FILE = "cookies.json"
TOKEN_CACHE_FILE = "token_cache.json"
INDEX_CACHE_FILE = "index_cache.json"
