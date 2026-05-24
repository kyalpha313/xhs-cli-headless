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

- `read` 优先读取笔记详情；有 `xsec_token` 时可走 API，失败时可回退 HTML。
- `comments` 通常需要有效 `xsec_token` 和登录态。
- `board` 是收藏列表的稳定替代路线。
- 短链接如果无法被 CLI 自动展开，应提示用户提供标准小红书 URL 或使用浏览器能力展开。

## 输出要求

笔记详情优先提取标题、正文、作者、图片数量、图片列表和关键互动信息。不要把相关推荐封面、头像误当作正文图片。
