# Release Validation Evidence

Updated: 2026-05-25

这份文档记录 `0.8.7` 的验证口径。命令是否默认支持、隐藏或不承诺，请以 [docs/capability-status.md](docs/capability-status.md) 为准。

## 自动化验证

发布前应运行：

```bash
uv run pytest tests/ -q
```

如果本机已有真实登录态，再运行：

```bash
uv run pytest -m smoke tests/test_smoke.py -q
```

本轮新增或重点覆盖：

- 内置 Agent skill 文件存在性
- 登录失效结构化恢复提示
- `code=-101` 归入 `not_authenticated`
- `/explore/<note_id>` URL 解析
- `/user/profile/<user_id>/<note_id>` URL 解析
- 当前移动端 SSR HTML fallback 的正文、图片和首屏评论解析
- `xhslink.com` 短链接明确提示先展开
- `xhs update --check`、`xhs update --dry-run` 和更新失败结构化错误
- wheel 强制包含文件同时进入 sdist，避免 `uv build` 从源码包构建 wheel 失败

## 真实验证建议

用户提供的测试笔记可用于发布前 smoke：

```text
https://www.xiaohongshu.com/user/profile/5c5a2a8b000000001a03d400/6a12f84b0000000035039932?xsec_token=ABHfeqNHItw0apRZKmOYILUgBFgRSFakHVonsnR2CqmrQ=&xsec_source=pc_user
```

建议验证：

```bash
xhs auth doctor --json
xhs read '<上方 URL>' --json
xhs comments '<上方 URL>' --json
xhs update --check --json
xhs update --dry-run --json
```

## 历史失败仍不默认承诺

以下能力仍不建议作为 Agent 默认入口：

- `delete`
- `sub-comments`
- `user`
- `user-posts`
- `favorites`
- `likes`
- `notifications`

## 发布前检查

- README 是否面向用户而不是开发者
- Release Notes 是否只写用户可感知变化
- `docs/capability-status.md` 是否与实际 `xhs --help` 一致
- `skills/` 和 `references/` 是否与当前能力边界一致
- 结构化错误是否仍符合 `SCHEMA.md`
- `uv build` 是否能一次性生成 sdist 和 wheel
