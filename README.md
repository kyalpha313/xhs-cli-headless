# xhs-cli-headless

一个面向无 GUI / 远程服务器 / Agent 场景的小红书 CLI fork。

- Fork 仓库：[kyalpha313/xhs-cli-headless](https://github.com/kyalpha313/xhs-cli-headless)
- 上游项目：[jackwener/xiaohongshu-cli](https://github.com/jackwener/xiaohongshu-cli)
- CLI 命令：`xhs`

> 说明：这是基于上游项目维护的发布分支，重点强化了 headless 二维码登录、登录态诊断、结构化输出和发布前验证流程。README 已按本 fork 的真实支持范围重写，不再沿用上游的推广内容与发布口径。

当前支持、隐藏和已知失败能力的总览，见 [capability-status.md](file:///Users/bytedance/Documents/Trae/xhs-cli-headless/docs/capability-status.md)。
本次 `0.8.5` 版本默认开放了 `xhs board` 和 `xhs reply`。

## 中文说明

### 项目定位

`xhs-cli-headless` 是一个以“服务器可用、Agent 可用、少人工介入”为目标的小红书 CLI fork。

### 与上游的关系

- 本仓库是 [jackwener/xiaohongshu-cli](https://github.com/jackwener/xiaohongshu-cli) 的 fork。
- 本 fork 的 README、测试矩阵和发布说明，只描述当前 fork 已验证的行为，不默认继承上游全部能力承诺。
- 原项目需要浏览器实现登陆动作，不适合服务器部署与Agent交互，本项目完善了命令行模式下的登陆功能，包括纯 HTTP 二维码登录，登录态导入 / 诊断 / 检查等。

### 当前能力口径

README 这里只保留摘要，完整状态请以 [capability-status.md](file:///Users/bytedance/Documents/Trae/xhs-cli-headless/docs/capability-status.md) 为准。

- 默认支持能力：认证、搜索、阅读、评论、回复、删评论、关注、单笔记收藏，以及基于 HTML fallback 的 `xhs board`
- 默认隐藏能力：`xhs post`、`xhs login --browser`、`xhs login --qrcode`
- 已知失败能力：`xhs delete`、`xhs sub-comments`、`xhs user`、`xhs user-posts`、`xhs favorites`、`xhs likes`、`xhs notifications`
- 当前关键结论：`xhs post` 已真实成功，`xhs delete` 当前仍失败；`xhs board` 已真实可用并作为收藏专辑替代路线公开

### 安装

#### 方式 1：直接从本 fork 安装

```bash
uv tool install git+https://github.com/kyalpha313/xhs-cli-headless
```

或：

```bash
pipx install git+https://github.com/kyalpha313/xhs-cli-headless
```

PyPI 发布后，也可以改为：

```bash
uv tool install xhs-cli-headless
pipx install xhs-cli-headless
```

计划使用的 PyPI 包名为 `xhs-cli-headless`。

#### 方式 2：源码运行

```bash
git clone https://github.com/kyalpha313/xhs-cli-headless.git
cd xhs-cli-headless
uv sync
```

### 快速开始

```bash
# 1) 推荐：直接登录（默认就是 headless 二维码 + 终端二维码 + 登录链接）
xhs login

# 2) 检查登录态
xhs status --yaml
xhs auth doctor --yaml
xhs auth inspect --yaml

# 3) 核心只读命令
xhs search "小红书" --yaml
xhs read <note_id_or_url> --yaml
xhs comments <note_id_or_url> --yaml

# 4) 新增默认能力
xhs board <board_id_or_url> --yaml
xhs reply <note_id_or_url> --comment-id <comment_id> -c "收到"
```

### 认证方式

当前对外推荐的认证方式：

- 默认推荐：`xhs login`
  - 默认 headless 二维码登录，包含终端二维码和登录链接
- 显式指定纯 HTTP 二维码：`xhs login --qrcode-http`
  - 与默认 `xhs login` 属于同一路径
- 导入已有登录态：`xhs auth import --file cookies.json`
  - 适合从其他环境迁移已验证 cookies
- 从浏览器/F12 粘贴关键字段：`xhs auth import-fields --interactive`
  - 适合在用户本机浏览器完成登录后，把关键 cookies 字段带回服务器

说明：

- `xhs status`、`xhs whoami`、`xhs read` 等命令默认只使用本地已保存登录态
- 若当前没有有效登录态，请先执行 `xhs login` 或 `xhs auth import --file cookies.json`
- 如果 `xhs login` 在扫码确认后触发额外验证码，请参考 [browser-cookie-recovery.md](file:///Users/bytedance/Documents/Trae/xhs-cli-headless/docs/browser-cookie-recovery.md)

辅助命令：

```bash
xhs auth doctor
xhs auth inspect
xhs auth import --file cookies.json
```

### 常用命令

默认 `xhs --help` 里出现的命令，都是当前版本优先支持的入口。
隐藏命令和已知失败能力，请优先查看 [capability-status.md](file:///Users/bytedance/Documents/Trae/xhs-cli-headless/docs/capability-status.md)。

```bash
# Auth
xhs login
xhs login --qrcode-http
xhs status
xhs whoami
xhs auth doctor
xhs auth inspect
xhs auth import --file cookies.json
xhs auth import-fields --interactive
xhs logout

# Search / Reading
xhs search "美食"
xhs search-user "用户关键词"
xhs topics "旅行"
xhs feed
xhs hot
xhs read <note_id_or_url>
xhs comments <note_id_or_url>

# Interactions
xhs like <note_id_or_url>
xhs like <note_id_or_url> --undo
xhs favorite <note_id_or_url>
xhs unfavorite <note_id_or_url>
xhs board <board_id_or_url>
xhs comment <note_id_or_url> -c "好赞"
xhs reply <note_id_or_url> --comment-id <comment_id> -c "收到"
xhs delete-comment <note_id> <comment_id>
xhs follow <user_id>
xhs unfollow <user_id>
```

### 登录恢复

如果 `xhs login` 在扫码确认后仍被平台要求额外验证码：

- 优先在你自己的浏览器里完成验证
- 然后使用 `xhs auth import-fields --interactive`
- 详细步骤见 [browser-cookie-recovery.md](file:///Users/bytedance/Documents/Trae/xhs-cli-headless/docs/browser-cookie-recovery.md)

### 结构化输出

所有命令都支持：

- `--yaml`
- `--json`

非 TTY 输出默认会偏向结构化格式，适合脚本和 Agent 使用。

统一 envelope 见 [SCHEMA.md](./SCHEMA.md)。

```bash
uv sync
uv run pytest tests/ -v
uv run pytest -m smoke tests/test_smoke.py -q
```

## License

Apache-2.0
