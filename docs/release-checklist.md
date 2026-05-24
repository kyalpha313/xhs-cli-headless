# Release Checklist

This checklist is for the current `xhs-cli-headless` CLI release process.

## A. Repository Files

These items should live in the repository and be versioned:

- `README.md` matches the current default command surface
- `RELEASE_NOTES.md` matches the release scope
- `release_test_matrix.md` matches verified / hidden / unsupported commands
- `LICENSE` is present
- `NOTICE` is present
- `.github/workflows/ci.yml` passes
- `.github/workflows/publish.yml` can build release artifacts and publish to PyPI when configured
- `.github/ISSUE_TEMPLATE/*` references the current CLI and installation flow

## B. Pre-Release Validation

Run before tagging a release:

```bash
uv run pytest -q
uv run xhs --help
uv run xhs login --help
```

Recommended minimum live validation:

```bash
xhs login
xhs status --yaml
xhs whoami --yaml
xhs search "小红书" --yaml
xhs read <note_id_or_url> --yaml
xhs comments <note_id_or_url> --yaml
```

## C. GitHub Web Settings

These items must be checked in the GitHub repository settings or release UI:

- Repository description matches the current fork positioning
- Homepage URL points to the current repository or docs entrypoint
- Topics reflect the real scope:
  - `xiaohongshu`
  - `cli`
  - `headless`
  - `agent`
  - `automation`
- Social preview image is valid
- Default branch is correct
- Branch protection is enabled for `main` if desired
- Actions are enabled
- Release page uses the current release notes
- PyPI trusted publishing or API token is configured if PyPI release is enabled

## D. PyPI Readiness

Check before the first PyPI release:

- Package name ownership is confirmed
- Versioning strategy is confirmed
- PyPI project metadata is acceptable
- Test package build succeeds:

```bash
uv build
```

- Publish credentials are configured:
  - trusted publishing preferred
  - API token fallback if needed
- Install path after release is documented:
  - `uv tool install xhs-cli-headless`
  - `pipx install xhs-cli-headless`

## E. Packaging Decisions

Current distribution recommendation:

- PyPI install after the release workflow publishes `xhs-cli-headless`
- GitHub source install remains available for unreleased commits:
  - `uv tool install git+https://github.com/kyalpha313/xhs-cli-headless`

Package name:

- `xhs-cli-headless`

Current non-goals:

- No unstable commands in the default CLI surface
- No direct browser automation embedded in the CLI runtime

## F. Bundled Agent Skills

The release package should include:

- `skills/SKILL.md`
- `skills/xhs-*/*.md`
- `references/*.md`
- `scripts/run_xhs.py`
- `scripts/smoke_check.py`
