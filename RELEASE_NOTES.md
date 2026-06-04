# Unreleased

## 行为修复

- `xhs read` 支持自动展开 `xhslink.com` 短链接，并限制最终 URL 必须属于 `xiaohongshu.com`。
- 公开视频 / 公开笔记 URL 在没有登录态时也会尝试 HTML fallback，不再被 `not_authenticated` 预先阻断。
- `xhs board` 改为公开 HTML fallback 路径，不要求先存在本地 cookies。

## Agent 规则

- 更新内置 skill 和参考文档：公开视频短链解析应先走“短链展开 + HTML fallback”，fallback 失败后再引导登录。

# v0.8.7

## 新功能

- 新增 `xhs update`
  - `xhs update --check` 检查当前版本与最新版本
  - `xhs update --dry-run` 只展示将执行的更新命令
  - `xhs update --source github` 支持从 GitHub 源更新
  - 更新 CLI 的同时也更新随包发布的 Agent skill

## 发布链路修复

- 修复 `release_test_matrix.md` 未进入 sdist 导致 `uv build` 从源码包构建 wheel 失败的问题
- 简化 GitHub 发布 workflow：发布资产构建一次，PyPI 发布复用同一份 dist artifact
- 保留 CI。它在 `v0.8.6` 发布中抓到了真实问题：
  - Python 3.10 不支持 `tomllib`
  - sdist/wheel 包含规则不一致

## 验证

- 新增 `xhs update` 行为测试
- 新增发布打包规则测试，确保 wheel 强制包含的文件也进入 sdist

# v0.8.6

## 新功能

- CLI 与 Agent skill 合并发布
  - 新增 `skills/` 和 `references/`，内置 Agent 路由、认证恢复、能力边界和安全规则
  - 不再需要单独安装 `xhs-cli-skill` 才能获得 Agent 使用指南
- 新增 Agent 辅助脚本
  - `scripts/run_xhs.py`：统一包装 `xhs` 命令，返回结构化执行结果
  - `scripts/smoke_check.py`：快速检查环境、登录诊断和基础只读链路
- 登录失效错误更适合 Agent 处理
  - `not_authenticated` 错误现在包含恢复步骤
  - `code=-101` 的“无登录信息”被归入登录失效，而不是普通 API 错误
- 阅读链路增强
  - 支持解析 `/explore/<note_id>` 和 `/user/profile/<user_id>/<note_id>` 两类标准笔记 URL
  - 当前 HTML fallback 能解析移动端 SSR 结构中的标题、正文、作者、正文图片和首屏评论数据
  - 正文图片计数只来自笔记 `imageList`，不再混入头像或相关推荐封面
  - 对 `xhslink.com` 短链接给出明确提示：需先展开为标准小红书 URL

## 文档

- README 重写为中文用户文档
  - 安装、登录、Agent 恢复流程、支持能力和边界更清晰
  - 删除旧的本机绝对路径链接
- 更新能力边界和 release 验证口径

## 兼容性

- 默认命令面保持保守，不新增高风险写能力
- `post`、`delete`、`sub-comments`、`user`、`user-posts`、`favorites`、`likes`、`notifications` 仍不作为 Agent 默认能力承诺

## 验证

- 新增单元测试覆盖内置 skill 文件、认证恢复提示、URL 解析和 HTML fallback 解析
- 发布前应运行：

```bash
uv run pytest tests/ -q
uv run pytest -m smoke tests/test_smoke.py -q
```
