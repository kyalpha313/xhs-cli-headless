# xhs-cli-headless

一个面向无 GUI / 远程服务器 / Agent 场景的小红书 CLI fork。

- Fork 仓库：[hostage007/xhs-cli-headless](https://github.com/hostage007/xhs-cli-headless)
- 上游项目：[jackwener/xiaohongshu-cli](https://github.com/jackwener/xiaohongshu-cli)
- CLI 命令：`xhs`

> 说明：这是基于上游项目维护的发布分支，重点强化了 headless 二维码登录、登录态诊断、结构化输出和发布前验证流程。README 已按本 fork 的真实支持范围重写，不再沿用上游的推广内容与发布口径。

## 目录

- [中文说明](#中文说明)
- [English](#english)

## 中文说明

### 项目定位

`xhs-cli-headless` 是一个以“服务器可用、Agent 可用、少人工介入”为目标的小红书 CLI fork。

这版发布重点是：

- 纯 HTTP 二维码登录
- 登录态导入 / 诊断 / 检查
- 核心只读链路稳定化
- 基础互动命令的可回滚验证
- 发布前 live validation 脚本

### 与上游的关系

- 本仓库是 [jackwener/xiaohongshu-cli](https://github.com/jackwener/xiaohongshu-cli) 的 fork。
- 本 fork 不再保留上游 README 里的 `More Tools` 推广内容。
- 本 fork 的 README、测试矩阵和发布说明，只描述当前 fork 已验证的行为，不默认继承上游全部能力承诺。

### 首版稳定范围

以下能力已收敛为本 fork 当前首版稳定范围：

- `xhs login --qrcode-http --print-link`
- `xhs status`
- `xhs whoami`
- `xhs auth doctor`
- `xhs auth inspect`
- `xhs auth import --file`
- `xhs search`
- `xhs search-user`
- `xhs topics`
- `xhs feed`
- `xhs hot`
- `xhs read`
- `xhs comments`
- `xhs my-notes`
- `xhs unread`
- `xhs like` / `xhs like --undo`
- `xhs favorite` / `xhs unfavorite`
- `xhs comment` / `xhs delete-comment`
- `xhs follow` / `xhs unfollow`

### 实验性 / 有限制

以下命令仍然保留，但不建议作为首版稳定能力宣传：

- `xhs login`
  - 浏览器 cookies 提取路径可能命中过期 session
  - 当前已改为提示用户回退到 `xhs login --qrcode-http --print-link`
- `xhs login --qrcode`
  - 浏览器辅助二维码路径保留，但本 fork 当前主推纯 HTTP 路线
- `xhs sub-comments`
  - 已补上 `xsec_token` 传播
  - 仍建议继续积累更多 live 样本
- `xhs reply`
  - 已补上 `-9043` 频控重试
  - 仍可能受平台节流影响
- `xhs post`
- `xhs delete`
  - creator 会话要求更严格，不纳入默认主验证流程

### 当前不支持 / 不建议宣传

以下命令在当前 public web API 下已确认不适合作为首版稳定能力：

- `xhs user`
- `xhs user-posts`
- `xhs favorites`
- `xhs likes`
- `xhs notifications`

### 安装

#### 方式 1：直接从本 fork 安装

```bash
uv tool install git+https://github.com/hostage007/xhs-cli-headless
```

或：

```bash
pipx install git+https://github.com/hostage007/xhs-cli-headless
```

#### 方式 2：源码运行

```bash
git clone https://github.com/hostage007/xhs-cli-headless.git
cd xhs-cli-headless
uv sync
```

### 快速开始

```bash
# 1) 推荐：无头二维码登录
xhs login --qrcode-http --print-link

# 2) 检查登录态
xhs status --yaml
xhs auth doctor --yaml
xhs auth inspect --yaml

# 3) 核心只读命令
xhs search "小红书" --yaml
xhs read 1 --yaml
xhs comments 1 --yaml
```

### 认证方式

当前支持的认证路径：

1. 已保存 cookies
2. 浏览器 cookies 提取
3. 浏览器辅助二维码登录
4. 纯 HTTP 二维码登录

其中本 fork 当前最推荐的是：

```bash
xhs login --qrcode-http --print-link
```

辅助命令：

```bash
xhs auth doctor
xhs auth inspect
xhs auth import --file cookies.json
```

### 常用命令

```bash
# Auth
xhs login --qrcode-http --print-link
xhs status
xhs whoami
xhs auth doctor
xhs auth inspect
xhs auth import --file cookies.json
xhs logout

# Search / Reading
xhs search "美食"
xhs search-user "用户关键词"
xhs topics "旅行"
xhs feed
xhs hot
xhs read 1
xhs comments 1

# Interactions
xhs like 1
xhs like 1 --undo
xhs favorite 1
xhs unfavorite 1
xhs comment 1 -c "好赞"
xhs delete-comment <note_id> <comment_id>
xhs follow <user_id>
xhs unfollow <user_id>

# Experimental
xhs sub-comments <note_id> <comment_id>
xhs reply <note_id> --comment-id <comment_id> -c "回复"
xhs post --title "标题" --body "正文" --images img.jpg
xhs delete <note_id>
```

### 结构化输出

所有命令都支持：

- `--yaml`
- `--json`

非 TTY 输出默认会偏向结构化格式，适合脚本和 Agent 使用。

统一 envelope 见 [SCHEMA.md](./SCHEMA.md)。

### 发布前验证

推荐发布前执行：

```bash
uv run pytest tests/test_client.py tests/test_cli.py tests/test_qr_login.py tests/test_cookies.py -q
uv run pytest -m smoke tests/test_smoke.py -q
uv run python scripts/live_release_validation.py > live_release_report.yaml
```

详细命令级验证矩阵见 [release_test_matrix.md](./release_test_matrix.md)。

发布说明草稿见 [RELEASE_NOTES.md](./RELEASE_NOTES.md)。

### 开发

```bash
uv sync
uv run pytest tests/ -v
uv run pytest -m smoke tests/test_smoke.py -q
```

## English

### What This Repo Is

`xhs-cli-headless` is a fork of the upstream Xiaohongshu CLI focused on:

- headless / server-friendly QR login
- session import / inspection / diagnostics
- structured output for automation and agent use
- release-oriented live validation

Fork repository:

- [hostage007/xhs-cli-headless](https://github.com/hostage007/xhs-cli-headless)

Upstream project:

- [jackwener/xiaohongshu-cli](https://github.com/jackwener/xiaohongshu-cli)

### Stable Scope In This Fork

Recommended as stable for the first release:

- `xhs login --qrcode-http --print-link`
- `xhs status`
- `xhs whoami`
- `xhs auth doctor`
- `xhs auth inspect`
- `xhs auth import --file`
- `xhs search`
- `xhs search-user`
- `xhs topics`
- `xhs feed`
- `xhs hot`
- `xhs read`
- `xhs comments`
- `xhs my-notes`
- `xhs unread`
- `xhs like` / `xhs like --undo`
- `xhs favorite` / `xhs unfavorite`
- `xhs comment` / `xhs delete-comment`
- `xhs follow` / `xhs unfollow`

### Experimental / Limited

- `xhs login` browser-cookie path
- `xhs login --qrcode`
- `xhs sub-comments`
- `xhs reply`
- `xhs post`
- `xhs delete`

### Unsupported In Current Public Web API

- `xhs user`
- `xhs user-posts`
- `xhs favorites`
- `xhs likes`
- `xhs notifications`

### Install

Install from this fork:

```bash
uv tool install git+https://github.com/hostage007/xhs-cli-headless
```

or:

```bash
pipx install git+https://github.com/hostage007/xhs-cli-headless
```

Run from source:

```bash
git clone https://github.com/hostage007/xhs-cli-headless.git
cd xhs-cli-headless
uv sync
```

### Recommended Auth Flow

```bash
xhs login --qrcode-http --print-link
xhs status --yaml
xhs auth doctor --yaml
xhs auth inspect --yaml
```

### Validation

```bash
uv run pytest tests/test_client.py tests/test_cli.py tests/test_qr_login.py tests/test_cookies.py -q
uv run pytest -m smoke tests/test_smoke.py -q
uv run python scripts/live_release_validation.py > live_release_report.yaml
```

For the detailed command-by-command release classification, see [release_test_matrix.md](./release_test_matrix.md).
## License

Apache-2.0
