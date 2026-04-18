# Release Validation Evidence

Updated: 2026-04-18

这份文档只保留“验证证据”，不再承担最终状态口径职责。

- 命令是否默认支持、是否隐藏、是否已知失败，请以 [capability-status.md](file:///Users/bytedance/Documents/Trae/xhs-cli-headless/docs/capability-status.md) 为准。
- 这里仅记录本仓库当前已经跑过的自动化测试、真实验证、失败复现与关键观察。

## 自动化证据

### 单元 / CLI / cookies / 登录子集

- 命令：
  - `uv run pytest tests/test_qr_login.py tests/test_cli.py tests/test_client.py tests/test_cookies.py -q`
- 结果：
  - `93 passed`

### Smoke 子集

- 命令：
  - `uv run pytest -m smoke tests/test_smoke.py -q`
- 结果：
  - `11 passed`

### 近期定向回归

- 命令：
  - `uv run pytest tests/test_cli.py -q`
  - `uv run pytest tests/test_client.py -q`
- 结果：
  - `49 passed`
  - `26 passed`

## 真实成功证据

### 认证与会话

- 已真实跑通：
  - `xhs login`
  - `xhs auth doctor --json`
  - `xhs auth inspect --yaml`
  - `xhs status --yaml`
  - `xhs whoami --yaml`
- 关键观察：
  - 当前 `auth doctor` 已支持 `main / creator` 双域校验
  - 当前真实会话下两域都可达到 `valid`

### 搜索 / 阅读 / 评论

- 已真实跑通：
  - `xhs search "小红书" --yaml`
  - `xhs search-user <keyword>`
  - `xhs topics <keyword>`
  - `xhs feed`
  - `xhs hot`
  - `xhs read <note_id_or_url> --yaml`
  - `xhs comments <note_id_or_url> --yaml`
- 关键观察：
  - `comments` 主链路可用
  - 评论链路里可以拿到真实 `root_comment_id`

### 社交与互动

- 已真实跑通：
  - `xhs like`
  - `xhs favorite`
  - `xhs unfavorite`
  - `xhs comment`
  - `xhs reply`
  - `xhs delete-comment`
  - `xhs follow`
  - `xhs unfollow`
- 关键观察：
  - `reply` 已在作者自己的笔记上完成真实写操作验证
  - `delete-comment` 已完成真实回滚验证

### 收藏专辑

- 已真实跑通：
  - `xhs board 'https://www.xiaohongshu.com/board/69e3597300000000160244ac?source=web_user_page' --json`
- 关键观察：
  - `board/user` API 本身仍失败
  - 但 HTML fallback 能解析真实 board 页面，拿到 `note_id` 和 `xsec_token`

### Creator

- 已真实跑通：
  - `xhs my-notes --json`
  - `xhs post --title ... --body ... --images ... --private --json`
- 关键观察：
  - `post` 已成功创建私密测试笔记，并返回真实 `note_id`
  - `post` 目前仍不宜单独视为完整闭环能力，因为 `delete` 未打通

## 真实失败复现证据

### 用户页相关

- 已真实复现失败：
  - `user`
  - `user-posts`
- 典型现象：
  - `code -1`
  - `HTTP 406`

### 收藏 / 点赞列表

- 已真实复现失败：
  - `favorites`
  - `likes`
  - `board/user` API
- 典型现象：
  - `code -1`
- 备注：
  - `board` 命令当前依赖 HTML fallback，而不是 `board/user` API

### 通知列表

- 已真实复现失败：
  - `notifications`
  - `you/mentions`
  - `you/likes`
  - `you/connections`
- 关键观察：
  - `unread` 仍可单独成功

### 子评论

- 已真实复现失败：
  - `sub-comments`
- 已尝试但仍失败的变量：
  - 不同 `xsec_token`
  - 不同 `xsec_source`
  - 不同 `top_comment_id`
  - 不同 `image_formats`
- 典型现象：
  - `code -1`

### Creator 删除

- 已真实复现失败：
  - `xhs delete 69e35d53000000001a029d52 --yes --json`
- 关键观察：
  - `auth doctor` 显示 `main` 与 `creator` 都是 `valid`
  - `get_creator_note_list(page=0)` 可正常读取，并确认测试私密笔记仍存在
  - 当前 `/api/galaxy/creator/note/delete` 及其若干候选变体都未成功
  - 新实现已把这类失败收敛为明确的 `unsupported_operation`

## 关键收敛结论

- `reply` 与 `sub-comments` 不能再视作同一风险组：
  - `reply` 已真实成功
  - `sub-comments` 真实失败
- `favorites` 与 `board` 也不能再视作同一路径：
  - `favorites` 列表 API 失败
  - `board` 通过 HTML fallback 真实可用
- `post` 与 `delete` 当前不能对外承诺为完整 creator 闭环：
  - `post` 成功
  - `delete` 失败

## 后续验证建议

- 若继续攻 `delete`：
  - 需要从创作者后台重新抓取真实删除请求
- 若继续攻 `sub-comments`：
  - 需要从真实评论页重新抓取当前二级评论请求
- 若继续攻 `user / notifications`：
  - 需要对照真实浏览器请求补充上下文，而不是继续只猜 endpoint
