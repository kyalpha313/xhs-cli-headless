# xhs-cli-headless

面向终端和 AI Agent 的小红书 CLI。

`xhs-cli-headless` 重点解决三件事：

- 在无 GUI / 远程服务器 / Agent 环境中完成登录和会话恢复
- 用稳定命令读取、搜索和整理小红书内容
- 把 CLI 与 Agent skill 一起发布，安装一个包即可同时获得程序和使用指南

当前版本：`0.8.8`

## 适合谁用

- 想在服务器或自动化脚本里使用小红书只读能力的人
- 需要让 AI Agent 调用小红书搜索、阅读、评论读取等能力的人
- 需要明确知道哪些能力稳定、哪些能力暂不承诺的人

## 安装

```bash
uv tool install git+https://github.com/kyalpha313/xhs-cli-headless
```

或：

```bash
pipx install git+https://github.com/kyalpha313/xhs-cli-headless
```

源码运行：

```bash
git clone https://github.com/kyalpha313/xhs-cli-headless.git
cd xhs-cli-headless
uv sync
uv run xhs --help
```

## 更新

`0.8.7` 起，可以用内置命令更新 CLI 和随包发布的 Agent skill：

```bash
xhs update --check --json
xhs update --dry-run
xhs update
```

如果你使用 GitHub 源安装：

```bash
xhs update --source github
```

`xhs update` 会优先识别 `uv tool`、`pipx`、`pip` 等常见安装方式。无法安全判断时，请先用 `--dry-run` 查看将执行的命令。

## 快速开始

```bash
# 1. 登录。默认是 headless 二维码登录，会在终端显示二维码和登录链接
xhs login

# 2. 检查登录态
xhs status --json
xhs auth doctor --json

# 3. 搜索和阅读
xhs search "AI agent" --json
xhs read <note_id_or_url> --json
xhs comments <note_id_or_url> --json

# 4. 读取收藏专辑 / board
xhs board <board_id_or_url> --json
```

## Agent 登录最佳实践

Agent 遇到“token 过期”“未登录”“Session expired”时，不要反复重试业务命令。推荐顺序是：

```bash
# 1. 先诊断
xhs auth doctor --json

# 2. 首次登录或会话过期，走二维码登录
xhs login

# 3. 如果用户已有 cookies 文件
xhs auth import --file cookies.json --json

# 4. 如果用户只能从浏览器复制字段
xhs auth import-fields --interactive

# 5. 恢复后验证
xhs status --json
```

例外：如果用户只是读取公开视频 / 公开笔记 URL，或给出 `xhslink.com` 短链接，先尝试 `xhs read`。公开内容可以走 HTML fallback，不应把登录失效当作硬阻塞；只有 fallback 也失败、或用户需要评论 / feed / 互动等登录能力时，再引导登录。

结构化错误会带 `details.steps`，Agent 可以直接按步骤引导用户完成恢复。

## 支持能力

### 认证与会话

| 命令 | 说明 |
| --- | --- |
| `xhs login` | 默认 headless 二维码登录 |
| `xhs login --qrcode-http` | 显式使用纯 HTTP 二维码登录 |
| `xhs status` | 检查当前登录态 |
| `xhs whoami` | 查看当前账号 |
| `xhs auth doctor` | 诊断主站和 creator 会话 |
| `xhs auth inspect` | 检查本地 cookie 字段，不打印敏感值 |
| `xhs auth import --file` | 导入 cookies 文件 |
| `xhs auth import-fields --interactive` | 交互式粘贴关键字段 |
| `xhs logout` | 清空本地登录态 |
| `xhs update` | 更新命令行和内置 Agent skill |

### 搜索与阅读

| 命令 | 说明 |
| --- | --- |
| `xhs search <query>` | 搜索笔记 |
| `xhs search-user <query>` | 搜索用户 |
| `xhs topics <query>` | 搜索话题 |
| `xhs feed` | 推荐流 |
| `xhs hot` | 热榜 |
| `xhs read <note_id_or_url>` | 读取笔记正文和正文图片 |
| `xhs comments <note_id_or_url>` | 读取评论 |
| `xhs board <board_id_or_url>` | 读取收藏专辑 / board |
| `xhs my-notes` | 查看当前账号发布的笔记 |
| `xhs unread` | 查看未读数量 |

### 互动

这些命令会修改账号状态，Agent 必须先向用户确认：

```bash
xhs like <note_id_or_url>
xhs like <note_id_or_url> --undo
xhs favorite <note_id_or_url>
xhs unfavorite <note_id_or_url>
xhs comment <note_id_or_url> -c "内容"
xhs reply <note_id_or_url> --comment-id <comment_id> -c "内容"
xhs delete-comment <note_id> <comment_id>
xhs follow <user_id>
xhs unfollow <user_id>
```

## 当前不默认承诺的能力

以下能力保留源码或历史记录，但不建议 Agent 默认调用：

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

替代路线：

- 收藏列表：优先使用 `xhs board <board_id_or_url>`
- 通知详情：当前只承诺 `xhs unread`
- 用户主页 / 用户发帖：当前不承诺稳定读取
- 删除笔记：当前不承诺稳定执行

## 短链接说明

`xhs read` 支持标准小红书笔记 URL；公开 URL 在没有登录态时也会尝试 HTML fallback，例如：

```bash
xhs read "https://www.xiaohongshu.com/explore/<note_id>?xsec_token=...&xsec_source=..."
xhs read "https://www.xiaohongshu.com/user/profile/<user_id>/<note_id>?xsec_token=...&xsec_source=..."
```

`xhslink.com` 短链接会先通过 HTTP 跳转展开，再交给 `xhs read`。CLI 只接受最终跳转到 `xiaohongshu.com` 或其子域的 URL；如果短链无法展开或跳到其他域名，会直接拒绝。

登录仍然有价值：有效登录态通常能获取更多 API 字段，也会影响评论、feed、互动、账号相关和受限内容。但公开视频 / 公开笔记读取不再被缺失登录态预先阻断。

## 内置 Agent Skill

`0.8.6` 起，本仓库内置 Agent 使用指南；`0.8.7` 起可通过 `xhs update` 一并更新 CLI 和这些 skill：

- `skills/SKILL.md`
- `skills/xhs-auth/SKILL.md`
- `skills/xhs-search/SKILL.md`
- `skills/xhs-read/SKILL.md`
- `skills/xhs-social/SKILL.md`
- `skills/xhs-ops/SKILL.md`
- `references/capability-boundary.md`
- `references/cli-command-map.md`
- `references/safety-rules.md`

它们描述 Agent 应如何选择命令、处理登录失效、确认写操作和规避不稳定能力。

## 结构化输出

所有命令都支持：

- `--json`
- `--yaml`

非 TTY 环境默认偏向结构化输出，适合脚本和 Agent 编排。

统一 envelope：

```json
{
  "ok": true,
  "schema_version": "1",
  "data": {}
}
```

错误 envelope：

```json
{
  "ok": false,
  "schema_version": "1",
  "error": {
    "code": "not_authenticated",
    "message": "...",
    "details": {
      "steps": []
    }
  }
}
```

## 开发与验证

```bash
uv sync
uv run pytest tests/ -q
uv run pytest -m smoke tests/test_smoke.py -q
```

辅助脚本：

```bash
python3 scripts/run_xhs.py --append-json-flag status
python3 scripts/smoke_check.py --json
```

## License

Apache-2.0
