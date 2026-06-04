# xhs-read

你负责 `xhs` CLI 的阅读与查看能力。

## 何时触发

- 打开单条笔记
- 查看正文和图片
- 查看评论
- 查看 board / 收藏专辑
- 查看我的笔记
- 查看未读数量

## 支持命令

- `xhs read <note_id_or_url> --json`
- `xhs comments <note_id_or_url> --json`
- `xhs board <board_id_or_url> --json`
- `xhs my-notes --json`
- `xhs unread --json`

## 注意事项

- `read` 优先读取笔记详情；有登录态和 `xsec_token` 时可走 API，失败时可回退 HTML。
- 公开 `xiaohongshu.com` URL 和 `xhslink.com` 短链不要先卡登录。即使 `xhs status` 是 `not_authenticated`，也先尝试 `xhs read <url> --json`。
- `comments` 通常需要有效 `xsec_token` 和登录态。
- `board` 是收藏列表的稳定替代路线，可通过公开 HTML fallback 读取。
- `xhslink.com` 短链接会由 CLI 自动展开；如果展开失败或最终 URL 不是 `xiaohongshu.com`，再提示用户提供标准小红书 URL。

## 输出要求

笔记详情优先提取标题、正文、作者、图片数量、图片列表和关键互动信息。不要把相关推荐封面、头像误当作正文图片。
