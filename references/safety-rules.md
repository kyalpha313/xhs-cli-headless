# Safety Rules

## 总原则

- 优先只读命令。
- 写操作必须确认。
- 登录问题先诊断，不盲目重试业务命令。
- 遇到隐藏或已知失败能力时，先说明边界，再给替代路线。

## 写操作

以下命令属于写操作：

- `like`
- `like --undo`
- `favorite`
- `unfavorite`
- `comment`
- `reply`
- `delete-comment`
- `follow`
- `unfollow`

执行前必须确认：

1. 目标明确。
2. 参数完整。
3. 用户明确授权。
4. 登录状态有效。

## 登录恢复

发现 `not_authenticated`、`session_expired`、`No saved login session`、`Session expired` 等错误时，Agent 应按顺序处理：

1. 运行 `xhs auth doctor --json`。
2. 如果没有有效会话，引导用户执行 `xhs login`。
3. 如果用户已有 cookies 文件，使用 `xhs auth import --file <file>`。
4. 如果用户只能从浏览器复制字段，使用 `xhs auth import-fields --interactive`。

## 禁止默认尝试

- 不默认调用 `post`。
- 不默认调用 `delete`。
- 不默认调用 `favorites`、`likes`、`notifications`。
- 不默认调用 `user`、`user-posts`、`sub-comments`。
- 不做批量自动互动。
