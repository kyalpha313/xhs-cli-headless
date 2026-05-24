# CLI Command Map

这份文档定义自然语言意图如何映射到稳定 `xhs` 命令。

## 认证与会话

| 用户意图 | 推荐命令 |
| --- | --- |
| 检查是否已登录 | `xhs status --json` |
| 查看当前账号 | `xhs whoami --json` |
| 登录排障 | `xhs auth doctor --json` |
| 查看本地 cookie 字段状态 | `xhs auth inspect --json` |
| 首次登录或重新登录 | `xhs login` |
| 导入 cookies 文件 | `xhs auth import --file <file> --json` |
| 交互式导入字段 | `xhs auth import-fields --interactive` |
| 退出登录 | `xhs logout --json` |

## 搜索与发现

| 用户意图 | 推荐命令 |
| --- | --- |
| 搜索笔记 | `xhs search <query> --json` |
| 搜索用户 | `xhs search-user <query> --json` |
| 搜索话题 | `xhs topics <query> --json` |
| 看推荐流 | `xhs feed --json` |
| 看热榜 | `xhs hot --json` |

## 阅读与查看

| 用户意图 | 推荐命令 |
| --- | --- |
| 读取笔记详情 | `xhs read <note_id_or_url> --json` |
| 查看评论 | `xhs comments <note_id_or_url> --json` |
| 查看收藏专辑/board | `xhs board <board_id_or_url> --json` |
| 查看我的笔记 | `xhs my-notes --json` |
| 查看未读数量 | `xhs unread --json` |

## 互动与社交

| 用户意图 | 推荐命令 |
| --- | --- |
| 点赞 | `xhs like <target> --json` |
| 取消点赞 | `xhs like <target> --undo --json` |
| 收藏 | `xhs favorite <target> --json` |
| 取消收藏 | `xhs unfavorite <target> --json` |
| 发表评论 | `xhs comment <target> -c <content> --json` |
| 回复评论 | `xhs reply <target> --comment-id <id> -c <content> --json` |
| 删除评论 | `xhs delete-comment <note_id> <comment_id> --yes --json` |
| 关注用户 | `xhs follow <user_id> --json` |
| 取消关注 | `xhs unfollow <user_id> --json` |

## 组合工作流

- 搜索后总结：`search -> read -> comments -> summarize`
- 评论区观点整理：`read -> comments -> summarize`
- board 内容整理：`board -> summarize`
- 登录恢复：`auth doctor -> login` 或 `auth import`
