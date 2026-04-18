# v0.8.2

## 新功能

- 新增 `xhs auth import-fields`
  - 支持直接传入 `a1`、`web_session`、`webId` 等字段
  - 支持 `--interactive` 交互式粘贴浏览器 / F12 中复制的 cookie 字段
- 新增登录恢复文档 `docs/browser-cookie-recovery.md`
  - 说明当扫码确认后触发额外验证码时，如何在用户自己的浏览器中完成验证，再把字段导回服务器 CLI

## Bug 修复

- 修正二维码登录状态提示
  - 原先在“已确认但尚未完成会话”阶段会显示 `Login confirmed!`
  - 现在改为更准确的“已确认，正在完成登录”
- 改进二维码登录触发验证码后的错误提示
  - 明确告诉用户可以使用 `xhs auth import --file` 或 `xhs auth import-fields --interactive`
- 改进验证码冷却日志文案
  - 明确说明冷却只是避免重试风暴，不代表验证码已经解决

## Stable Scope

The following commands are suitable for the current stable release:

- `xhs login`
- `xhs login --qrcode-http`
- `xhs status`
- `xhs whoami`
- `xhs auth doctor`
- `xhs auth inspect`
- `xhs auth import --file`
- `xhs search`
- `xhs search-user`
- `xhs topics`
- `xhs feed`
- `xhs hot`
- `xhs read`
- `xhs comments`
- `xhs my-notes`
- `xhs unread`
- `xhs like` / `xhs like --undo`
- `xhs favorite` / `xhs unfavorite`
- `xhs comment` / `xhs delete-comment`
- `xhs follow` / `xhs unfollow`

## Experimental / Limited

- `xhs login --browser`
- `xhs login --qrcode`
- `xhs sub-comments`
- `xhs reply`
- `xhs post`
- `xhs delete`

These capabilities remain in source for future work, but should not be exposed or marketed as stable in the current release.

## Unsupported In Current Public Web API

- `xhs user`
- `xhs user-posts`
- `xhs favorites`
- `xhs likes`
- `xhs notifications`

These should be hidden from release messaging or clearly marked unsupported/experimental.

## Validation

Recommended release validation flow:

```bash
uv run pytest tests/test_client.py tests/test_cli.py tests/test_qr_login.py tests/test_cookies.py -q
uv run pytest -m smoke tests/test_smoke.py -q
uv run python scripts/live_release_validation.py > live_release_report.yaml
```

Optional gated passes:

```bash
uv run python scripts/live_release_validation.py --enable-creator-write-tests
uv run python scripts/live_release_validation.py --enable-browser-login-check
```

See `release_test_matrix.md` for the command-by-command release classification.
