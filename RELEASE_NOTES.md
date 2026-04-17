# Release Notes Draft

## Summary

This release focuses on a stable headless CLI core for Xiaohongshu:

- Pure-HTTP QR login is verified live and suitable for non-GUI environments.
- Session tooling is expanded with `auth doctor`, `auth inspect`, and `auth import --file`.
- Core read flows are validated live: `search`, `search-user`, `topics`, `feed`, `hot`, `read`, `comments`.
- Core rollback-safe interactions are validated live: `like`, `favorite`, `comment`, `delete-comment`, `follow`, `unfollow`.
- Release documentation and validation tooling are aligned with the real supported scope.

## Highlights

### Headless Login

- Added `xhs login --qrcode-http --print-link`
- Verified the pure-HTTP QR flow live:
  - QR creation
  - scan confirmation
  - cookie persistence
  - post-login session validation

### Auth Tooling

- Added `xhs auth doctor`
- Added `xhs auth inspect`
- Added `xhs auth import --file cookies.json`
- Improved browser-cookie login fallback messaging when extracted cookies are already expired

### QR Login UX

- Added explicit QR URL printing support
- Routed QR progress messages away from structured stdout in `--yaml` / `--json` mode
- Improved timeout and repeated polling failure hints

### Reliability Fixes

- `sub-comments` now propagates cached or explicit `xsec_token` / `xsec_source`
- `reply` now retries once on Xiaohongshu rate-limit code `-9043` and returns a clearer actionable error if throttling persists
- Notification list failures now surface a clearer unsupported/fallback path instead of a vague raw API error

## Stable Scope

The following commands are suitable for the first public release:

- `xhs login --qrcode-http --print-link`
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

- `xhs login` browser-cookie path
- `xhs login --qrcode`
- `xhs sub-comments`
- `xhs reply`
- `xhs post`
- `xhs delete`

These commands remain in the CLI, but should not be marketed as stable in the first release.

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
