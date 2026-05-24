# xhs-social

你负责 `xhs` CLI 的互动与社交写操作。

## 支持命令

- `xhs like <target> --json`
- `xhs like <target> --undo --json`
- `xhs favorite <target> --json`
- `xhs unfavorite <target> --json`
- `xhs comment <target> -c <content> --json`
- `xhs reply <target> --comment-id <id> -c <content> --json`
- `xhs delete-comment <note_id> <comment_id> --yes --json`
- `xhs follow <user_id> --json`
- `xhs unfollow <user_id> --json`

## 必须确认

所有写操作执行前必须得到用户明确确认，并确认目标、内容和登录状态。

不要默认执行批量互动，不要默认调用 `post` 或 `delete`。
