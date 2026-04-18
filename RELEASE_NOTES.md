# Release Notes Draft for v0.8.1

## Summary

This release focuses on a stable headless CLI core for Xiaohongshu and aligns the package for the next public distribution pass:

- Pure-HTTP QR login is verified live and suitable for non-GUI environments.
- Session tooling is expanded with `auth doctor`, `auth inspect`, and `auth import --file`.
- Core read flows are validated live: `search`, `search-user`, `topics`, `feed`, `hot`, `read`, `comments`.
- Core rollback-safe interactions are validated live: `like`, `favorite`, `comment`, `delete-comment`, `follow`, `unfollow`.
- Release documentation and validation tooling are aligned with the real supported scope.
- The distribution package name is now `xhs-cli-headless`.

## Highlights

### Headless Login

- `xhs login` is now the default recommended headless QR login entry
- `xhs login --qrcode-http` remains as the explicit pure-HTTP equivalent
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

### Release Surface

- The default CLI help now exposes only the stable command surface
- Hidden / unsupported commands are kept in source for future work, but are no longer part of the default release messaging
- Non-login commands now use the saved session only, instead of silently re-extracting browser cookies

### Packaging And Attribution

- Added `LICENSE` and `NOTICE`
- Added a repository release checklist
- Updated package metadata to keep upstream author credit and current maintainer metadata
- Added GitHub Release artifact publishing and prepared the workflow for future PyPI publishing

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
