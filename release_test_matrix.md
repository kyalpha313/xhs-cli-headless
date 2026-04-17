# Release Test Matrix

Updated: 2026-04-17

## Legend

- `verified-live`: Ran successfully against the real Xiaohongshu API in this workspace/session.
- `tested-local`: Covered by local/unit tests in this workspace, but not re-verified manually against the live API in this release pass.
- `known-broken`: Reproduced as unavailable or rejected by the current public web API.
- `untested-high-risk`: Exposed by the CLI, but not yet verified in this release pass. Requires validation before release.

## Evidence Summary

- Full local regression subsets passed:
  - `uv run pytest tests/test_qr_login.py tests/test_cli.py tests/test_client.py tests/test_cookies.py -q`
  - Result: `93 passed`
- Real CLI smoke tests passed:
  - `uv run pytest -m smoke tests/test_smoke.py -q`
  - Result: `11 passed`
- Real manual validation completed in this workspace:
  - `xhs auth import --file xhs_cli/test/cookies.json --yaml`
  - `xhs auth doctor --yaml`
  - `xhs auth inspect --yaml`
  - `xhs status --yaml`
  - `xhs whoami --yaml`
  - `xhs search "小红书" --yaml`
  - `xhs read 1 --yaml`
  - `xhs comments 1 --yaml`
  - `xhs login --qrcode-http --print-link`

## Release Classification

### Auth

| Command | Status | Evidence | Notes |
| --- | --- | --- | --- |
| `login` | `tested-local` | CLI/unit tests + live fallback check | Browser extraction may surface expired browser sessions; the CLI now points users to `xhs login --qrcode-http --print-link`. |
| `login --qrcode` | `tested-local` | QR/unit tests | Browser-assisted QR path has local coverage; pure browser-assisted live run not re-verified manually. |
| `login --qrcode-http --print-link` | `verified-live` | Real manual run | Pure-HTTP QR flow succeeded end-to-end, including scan, confirmation, cookie persistence, and session validation. |
| `status` | `verified-live` | Manual + smoke | Returned `authenticated: true` after imported cookies and after QR login. |
| `whoami` | `verified-live` | Smoke | Passed real smoke test. |
| `logout` | `tested-local` | CLI/unit tests | Not re-run manually to avoid discarding the current valid session during release prep. |
| `auth doctor` | `verified-live` | Manual | Validated both imported cookies and QR-created session. |
| `auth inspect` | `verified-live` | Manual | Verified masked cookie summary on the saved local session. |
| `auth import --file` | `verified-live` | Manual | Imported the provided `cookies.json` successfully and validated the resulting session. |

### Read-only Discovery / Reading

| Command | Status | Evidence | Notes |
| --- | --- | --- | --- |
| `search` | `verified-live` | Manual + smoke | Real API success. |
| `search-user` | `verified-live` | Live release report | Real API success in the full release pass. |
| `topics` | `verified-live` | Smoke | Passed real smoke test. |
| `feed` | `verified-live` | Smoke | Passed real smoke test. |
| `hot` | `verified-live` | Smoke | Passed real smoke test. |
| `read` | `verified-live` | Manual + smoke | Real API success, including short-index flow. |
| `comments` | `verified-live` | Manual + smoke | Real API success, including short-index flow. |
| `sub-comments` | `tested-local` | Local tests + token propagation fix | Now resolves note references and forwards `xsec_token`; still needs a stable live note/comment target for final confirmation. |
| `user` | `known-broken` | Manual live repro | Current public web API returns `HTTP 406` / `{"code":-1,"success":false}`; CLI now surfaces `unsupported_operation`. |
| `user-posts` | `known-broken` | Manual live repro | Same failure mode as `user`; CLI now surfaces `unsupported_operation`. |

### Social / Collection

| Command | Status | Evidence | Notes |
| --- | --- | --- | --- |
| `favorites` | `known-broken` | Live release report | Current public web API returned `code -1`; do not advertise for this release. |
| `likes` | `known-broken` | Live release report | Current public web API returned `code -1`; do not advertise for this release. |
| `follow` | `verified-live` | Live release report | Real follow/unfollow rollback succeeded. |
| `unfollow` | `verified-live` | Live release report | Real follow/unfollow rollback succeeded. |

### Interactions

| Command | Status | Evidence | Notes |
| --- | --- | --- | --- |
| `like` | `verified-live` | Live release report | Real like/unlike rollback succeeded. |
| `favorite` | `verified-live` | Live release report | Real favorite/unfavorite rollback succeeded. |
| `unfavorite` | `verified-live` | Live release report | Real favorite/unfavorite rollback succeeded. |
| `comment` | `verified-live` | Live release report | Real comment/delete-comment rollback succeeded. |
| `reply` | `tested-local` | Local tests + rate-limit handling fix | Pre-fix live failure was `-9043` (rate limit). Command now retries once and returns a clearer actionable error on persistent throttling. |
| `delete-comment` | `verified-live` | Live release report | Real comment delete rollback succeeded. |

### Creator

| Command | Status | Evidence | Notes |
| --- | --- | --- | --- |
| `my-notes` | `verified-live` | Live release report | Real API success in the full release pass. |
| `post` | `untested-high-risk` | Creator tests exist | Write operation; must be validated with a disposable note before release. |
| `delete` | `untested-high-risk` | Creator tests exist | Creator delete can fail even when a regular session looks valid; keep behind a controlled pass only. |

### Notifications

| Command | Status | Evidence | Notes |
| --- | --- | --- | --- |
| `notifications` | `known-broken` | Live release report + clearer fallback | Current public web API returned `code -1`; CLI now surfaces `unsupported_operation` and suggests `xhs unread`. |
| `unread` | `verified-live` | Live release report | Real API success in the full release pass. |

## Release Recommendation

### Safe To Ship First

- `login --qrcode-http --print-link`
- `status`
- `whoami`
- `auth doctor`
- `auth inspect`
- `auth import --file`
- `search`
- `search-user`
- `topics`
- `feed`
- `hot`
- `read`
- `comments`
- `my-notes`
- `unread`
- `like`
- `favorite`
- `unfavorite`
- `comment`
- `delete-comment`
- `follow`
- `unfollow`

### Must Be Marked Unsupported Or Hidden Before Release

- `user`
- `user-posts`
- `favorites`
- `likes`
- `notifications`

### Must Be Validated Before Release If Kept

- `sub-comments`
- `reply`
- `post`
- `delete`
- browser cookie extraction path of `login`
- browser-assisted `login --qrcode`

## Suggested Final Release Pass

1. Re-run `uv run pytest -m smoke tests/test_smoke.py -q`
2. Manually verify `login --qrcode-http --print-link`
3. Run `uv run python scripts/live_release_validation.py > live_release_report.yaml`
4. Decide whether to hide or clearly label `user` and `user-posts`
5. Run creator write tests only when delete rollback is verified for the current session type:
   `uv run python scripts/live_release_validation.py --enable-creator-write-tests`
6. Run browser cookie extraction check only as a separate optional pass:
   `uv run python scripts/live_release_validation.py --enable-browser-login-check`
7. Freeze the final supported command list in README / release notes

## Updated Strategy

- Default release validation now aims for **one manual login only**.
- The main pass reuses the same authenticated session for read-only coverage and rollback-safe write checks.
- Creator `post/delete` is now treated as a separately gated pass, because a failed `delete` may leave orphaned test content.
- Browser-cookie `login` is also separated from the main pass so it does not overwrite a known-good QR session mid-run.
