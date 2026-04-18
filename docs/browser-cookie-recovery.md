# Browser Cookie Recovery

When `xhs login` reaches QR confirmation but Xiaohongshu requires an additional captcha, the most reliable fallback is:

1. finish the verification in your own browser
2. copy the resulting cookie fields
3. import them back into the headless CLI

This guide is designed for users running the CLI on a headless Linux server.

## When To Use This

Use this fallback when:

- `xhs login` reports that the QR code was scanned and confirmed
- but the session is not finalized because Xiaohongshu required an extra captcha or verification step

Do not use this flow if the normal `xhs login` command already succeeds.

## Recommended Path

Use your own browser to complete the login or captcha, then import the resulting cookies into the server-side CLI.

## Step 1: Finish Login In Your Browser

- Open `https://www.xiaohongshu.com/`
- Log in with the same account
- Complete any captcha / slider / extra verification that Xiaohongshu requires
- Confirm that you are fully logged in inside the browser before continuing

## Step 2: Open Browser DevTools

In your browser:

- Open the Xiaohongshu page
- Press `F12`, or open the browser developer tools
- Go to the cookies storage view

Typical locations:

- Chrome / Edge:
  - `Application` -> `Storage` -> `Cookies` -> `https://www.xiaohongshu.com`
- Firefox:
  - `Storage` -> `Cookies` -> `https://www.xiaohongshu.com`

## Step 3: Copy The Minimum Required Fields

Minimum required fields for the current CLI flow:

- `a1`
- `web_session`
- `webId`

Optional but recommended if present:

- `web_session_sec`
- `gid`
- `websectiga`
- `sec_poison_id`
- `xsecappid`
- `id_token`

## Step 4: Import Fields Into The Headless CLI

### Interactive import

If you want the CLI to prompt for fields one by one:

```bash
xhs auth import-fields --interactive
```

### Direct import

If you want to pass the fields directly:

```bash
xhs auth import-fields \
  --a1 "<A1>" \
  --web-session "<WEB_SESSION>" \
  --webid "<WEBID>"
```

You can also include optional fields:

```bash
xhs auth import-fields \
  --a1 "<A1>" \
  --web-session "<WEB_SESSION>" \
  --webid "<WEBID>" \
  --web-session-sec "<WEB_SESSION_SEC>" \
  --gid "<GID>"
```

## Step 5: Verify The Imported Session

After import, verify the session:

```bash
xhs auth doctor --yaml
xhs status --yaml
```

If both commands show a valid authenticated session, the recovery succeeded.

## If Import Still Fails

- Re-open the browser and confirm that the account is fully logged in
- Re-copy the required cookie fields
- Prefer `xhs auth import-fields --interactive` to avoid missing a required field
- If available, export a full browser cookie JSON and use:

```bash
xhs auth import --file cookies.json
```

## Current Scope

This is an MVP fallback designed for:

- headless Linux servers
- users with any desktop browser and any desktop OS
- environments where the server itself cannot open a GUI browser

It is intentionally simpler and more reliable than trying to complete the captcha inside the server-side CLI.
