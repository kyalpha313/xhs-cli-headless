# Capability Boundary

这份文档定义 `xhs` CLI 和内置 skill 在 `0.8.9` 的稳定能力边界。

核心原则：只包装稳定 CLI 能力，不把隐藏命令和已知失败命令误暴露给 Agent。

## 默认支持

### 认证与会话

- `xhs login`
- `xhs login --qr-output <png>`
- `xhs login --qrcode-http`
- `xhs status`
- `xhs whoami`
- `xhs auth doctor`
- `xhs auth inspect`
- `xhs auth import --file`
- `xhs auth import-fields --interactive`
- `xhs logout`

### 只读发现与阅读

- `xhs search`
- `xhs search-user`
- `xhs topics`
- `xhs feed`
- `xhs hot`
- `xhs read`（公开 `xiaohongshu.com` URL / `xhslink.com` 短链可匿名走 HTML fallback）
- `xhs comments`
- `xhs board`（通过公开 HTML fallback，不要求先登录）
- `xhs my-notes`
- `xhs unread`

### 互动与社交

- `xhs like` / `xhs like --undo`
- `xhs favorite` / `xhs unfavorite`
- `xhs comment`
- `xhs reply`
- `xhs delete-comment`
- `xhs follow` / `xhs unfollow`

## 隐藏或不默认路由

- `xhs post`
- `xhs delete`
- `xhs sub-comments`
- `xhs user`
- `xhs user-posts`
- `xhs favorites`
- `xhs likes`
- `xhs notifications`
- `xhs login --browser`
- `xhs login --qrcode`

## 替代路线

| 用户需求 | 不要默认走 | 推荐替代 |
| --- | --- | --- |
| 查看收藏列表 | `favorites` | `board <board_id_or_url>` |
| 查看新消息数量 | `notifications` | `unread` |
| 查看用户主页/发帖 | `user` / `user-posts` | 说明当前不承诺 |
| 删除自己发布的笔记 | `delete` | 说明当前不承诺 |
| 读取公开视频短链 | 手动要求用户展开或先登录 | `read <xhslink.com_url>`，自动安全展开后匿名 HTML fallback |

## 文档同步

命令面发生变化时，必须同步更新：

1. `README.md`
2. `RELEASE_NOTES.md`
3. `docs/capability-status.md`
4. `references/cli-command-map.md`
5. 相关 `skills/*/SKILL.md`
