# 能力状态总览

更新时间：2026-05-24

这份文档说明 `xhs-cli-headless` `0.8.6` 当前对外承诺的能力边界。这里的“支持”指默认命令面和 Agent skill 都可以路由；“隐藏 / 不承诺”指源码可能存在，但不建议 Agent 默认调用。

## 默认支持

### 认证与会话

| 命令 | 当前状态 | 备注 |
| --- | --- | --- |
| `xhs login` | 支持 | 默认 headless 二维码登录，终端展示二维码和链接 |
| `xhs login --qrcode-http` | 支持 | 与默认登录同一路径 |
| `xhs status` | 支持 | 检查当前登录态 |
| `xhs whoami` | 支持 | 获取当前账号信息 |
| `xhs auth doctor` | 支持 | 诊断主站 / creator 双域会话 |
| `xhs auth inspect` | 支持 | 检查本地 cookies 字段，不打印敏感值 |
| `xhs auth import --file` | 支持 | 导入 cookies 文件 |
| `xhs auth import-fields --interactive` | 支持 | 交互式导入关键字段 |
| `xhs logout` | 支持 | 清空本地登录态 |

### 只读发现与阅读

| 命令 | 当前状态 | 备注 |
| --- | --- | --- |
| `xhs search` | 支持 | 搜索笔记 |
| `xhs search-user` | 支持 | 搜索用户 |
| `xhs topics` | 支持 | 搜索话题 |
| `xhs feed` | 支持 | 推荐流 |
| `xhs hot` | 支持 | 热榜 |
| `xhs read` | 支持 | 支持标准 note URL；HTML fallback 可解析当前移动端 SSR 结构 |
| `xhs comments` | 支持 | 评论 API 通常需要有效登录态和 `xsec_token` |
| `xhs board` | 支持 | 通过 HTML fallback 读取收藏专辑 |
| `xhs my-notes` | 支持 | creator 列表 |
| `xhs unread` | 支持 | 未读数量 |

### 互动与社交

| 命令 | 当前状态 | 备注 |
| --- | --- | --- |
| `xhs like` / `xhs like --undo` | 支持 | 写操作，Agent 必须先确认 |
| `xhs favorite` / `xhs unfavorite` | 支持 | 写操作，Agent 必须先确认 |
| `xhs comment` | 支持 | 写操作，Agent 必须先确认 |
| `xhs reply` | 支持 | 写操作，Agent 必须先确认 |
| `xhs delete-comment` | 支持 | 写操作，Agent 必须先确认 |
| `xhs follow` / `xhs unfollow` | 支持 | 写操作，Agent 必须先确认 |

## 内置 Agent Skill

`0.8.6` 起，本仓库内置 Agent 文档：

- `skills/SKILL.md`
- `skills/xhs-auth/SKILL.md`
- `skills/xhs-search/SKILL.md`
- `skills/xhs-read/SKILL.md`
- `skills/xhs-social/SKILL.md`
- `skills/xhs-ops/SKILL.md`
- `references/capability-boundary.md`
- `references/cli-command-map.md`
- `references/safety-rules.md`

这些文件随仓库和发布包一起分发，用于指导 Agent 选择命令、处理登录失效、确认写操作和规避不稳定能力。

## 隐藏 / 不默认承诺

| 命令 | 当前状态 | 备注 |
| --- | --- | --- |
| `xhs post` | 隐藏 | 历史上验证过可发布私密图文，但不作为 Agent 默认能力 |
| `xhs delete` | 隐藏且不承诺 | 当前 creator 删除接口不稳定 |
| `xhs sub-comments` | 隐藏且不承诺 | 当前 public web API 下不稳定 |
| `xhs user` | 隐藏且不承诺 | 当前 public web API 下不稳定 |
| `xhs user-posts` | 隐藏且不承诺 | 当前 public web API 下不稳定 |
| `xhs favorites` | 隐藏且不承诺 | 使用 `board` 作为替代 |
| `xhs likes` | 隐藏且不承诺 | 当前不作为默认能力 |
| `xhs notifications` | 隐藏且不承诺 | 使用 `unread` 作为轻量替代 |
| `xhs login --browser` | 隐藏 | 本机辅助路径，不作为服务器 / Agent 默认入口 |
| `xhs login --qrcode` | 隐藏 | 浏览器辅助二维码路径，不作为默认入口 |

## 替代路线

- 收藏列表：优先使用 `xhs board <board_id_or_url>`
- 通知详情：当前仅承诺 `xhs unread`
- 用户主页 / 用户发帖：当前不承诺稳定读取
- 删除笔记：当前不承诺稳定执行
- 短链接：先展开 `xhslink.com`，再把标准 `xiaohongshu.com` URL 传给 `xhs read`
