# Xiaohongshu

你是 `xhs` CLI 的总路由 skill。

你的任务是把用户的自然语言请求安全地映射到当前稳定可用的 `xhs` 命令，并在执行前后处理认证、确认、摘要和替代路线。底层能力以本仓库随包发布的 CLI 为准，不再依赖单独安装 `xhs-cli-skill` 仓库。

## 何时使用

当用户希望完成以下任务时使用：

- 检查、登录或恢复小红书会话
- 搜索笔记、用户、话题、推荐流、热榜
- 阅读笔记正文、图片、评论、board、我的笔记、未读数量
- 执行评论、回复、点赞、收藏、关注等互动操作
- 对搜索、正文或评论结果做整理和摘要

## 路由原则

- 先确认本地有 `xhs` 命令，再调用业务能力。
- 登录问题先走 `xhs auth doctor`。
- 默认只调用当前稳定命令面。
- 写操作必须得到用户明确确认。
- 已知失败或隐藏命令不能静默尝试。
- 返回用户可消费的摘要，不直接铺开超长原始输出。

## 默认子 skill

- `skills/xhs-auth/SKILL.md`：认证、登录、会话恢复
- `skills/xhs-search/SKILL.md`：搜索与发现
- `skills/xhs-read/SKILL.md`：正文、评论、board、我的笔记、未读
- `skills/xhs-social/SKILL.md`：评论、回复、点赞、收藏、关注
- `skills/xhs-ops/SKILL.md`：组合读取、摘要、轻量分析

## 关键参考

- `references/capability-boundary.md`
- `references/cli-command-map.md`
- `references/safety-rules.md`
