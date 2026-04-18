# Skill Notice

This repository ships the `xhs` CLI only.

It does not provide production Agent skill definitions anymore.

## Why

- This fork is focused on a stable headless CLI surface.
- Agent skills have a different lifecycle from the CLI itself.
- Keeping skills in this repository caused the instructions to drift away from the real CLI behavior.

## Current Recommendation

- Use this repository for the CLI runtime and release artifacts only.
- Keep Agent skill wrappers in a separate repository.
- Document only the stable CLI commands there.

## Auth Baseline

- Recommended login command: `xhs login`
- Explicit browser-cookie import path: `xhs login --browser`
- Browser-assisted QR path: `xhs login --qrcode`

## Status

The old combined skill instructions were intentionally removed from this repository to avoid misleading users and Agents.
