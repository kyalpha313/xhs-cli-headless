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
  - `xhs read <note_id_or_url> --yaml`
  - `xhs comments <note_id_or_url> --yaml`
  - `xhs login`

## Release Classification

### Auth

| Command | Status | Evidence | Notes |
| --- | --- | --- | --- |
| `login` | `verified-live` | Real manual run + CLI/unit tests | Default release entry now uses the verified headless QR flow and prints the login link automatically. |
| `login --qrcode` | `tested-local` | QR/unit tests | Browser-assisted QR path has local coverage; pure browser-assisted live run not re-verified manually. |
| `login --qrcode-http` | `verified-live` | Real manual run | Explicit pure-HTTP QR path is equivalent to the default release login flow. |
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
| `sub-comments` | `tested-local` | Local tests + token propagation fix | Retained in source only; not exposed in the default CLI surface for this release. |
| `user` | `known-broken` | Manual live repro | Current public web API returns `HTTP 406` / `{"code":-1,"success":false}`; removed from the default CLI surface. |
| `user-posts` | `known-broken` | Manual live repro | Same failure mode as `user`; removed from the default CLI surface. |

### Social / Collection

| Command | Status | Evidence | Notes |
| --- | --- | --- | --- |
| `favorites` | `known-broken` | Live release report | Current public web API returned `code -1`; removed from the default CLI surface. |
| `likes` | `known-broken` | Live release report | Current public web API returned `code -1`; removed from the default CLI surface. |
| `follow` | `verified-live` | Live release report | Real follow/unfollow rollback succeeded. |
| `unfollow` | `verified-live` | Live release report | Real follow/unfollow rollback succeeded. |

### Interactions

| Command | Status | Evidence | Notes |
| --- | --- | --- | --- |
| `like` | `verified-live` | Live release report | Real like/unlike rollback succeeded. |
| `favorite` | `verified-live` | Live release report | Real favorite/unfavorite rollback succeeded. |
| `unfavorite` | `verified-live` | Live release report | Real favorite/unfavorite rollback succeeded. |
| `comment` | `verified-live` | Live release report | Real comment/delete-comment rollback succeeded. |
| `reply` | `tested-local` | Local tests + rate-limit handling fix | Retained in source only; not exposed in the default CLI surface for this release. |
| `delete-comment` | `verified-live` | Live release report | Real comment delete rollback succeeded. |

### Creator

| Command | Status | Evidence | Notes |
| --- | --- | --- | --- |
| `my-notes` | `verified-live` | Live release report | Real API success in the full release pass. |
| `post` | `untested-high-risk` | Creator tests exist | Retained in source only; not exposed in the default CLI surface for this release. |
| `delete` | `untested-high-risk` | Creator tests exist | Retained in source only; not exposed in the default CLI surface for this release. |

### Notifications

| Command | Status | Evidence | Notes |
| --- | --- | --- | --- |
| `notifications` | `known-broken` | Live release report + clearer fallback | Current public web API returned `code -1`; removed from the default CLI surface. |
| `unread` | `verified-live` | Live release report | Real API success in the full release pass. |

## Release Recommendation

### Safe To Ship First

- `login`
- `login --qrcode-http`
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
- browser cookie extraction path of `login --browser`
- browser-assisted `login --qrcode`

## Suggested Final Release Pass

1. Re-run `uv run pytest -m smoke tests/test_smoke.py -q`
2. Manually verify `login`
3. Run `uv run python scripts/live_release_validation.py > live_release_report.yaml`
4. Confirm removed commands stay out of the default CLI surface
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
