# xhs-cli-headless

一个面向无 GUI / 远程服务器 / Agent 场景的小红书 CLI fork。

- Fork 仓库：[kyalpha313/xhs-cli-headless](https://github.com/kyalpha313/xhs-cli-headless)
- 上游项目：[jackwener/xiaohongshu-cli](https://github.com/jackwener/xiaohongshu-cli)
- CLI 命令：`xhs`

> 说明：这是基于上游项目维护的发布分支，重点强化了 headless 二维码登录、登录态诊断、结构化输出和发布前验证流程。README 已按本 fork 的真实支持范围重写，不再沿用上游的推广内容与发布口径。

## 中文说明

### 项目定位

`xhs-cli-headless` 是一个以“服务器可用、Agent 可用、少人工介入”为目标的小红书 CLI fork。

### 与上游的关系

- 本仓库是 [jackwener/xiaohongshu-cli](https://github.com/jackwener/xiaohongshu-cli) 的 fork。
- 本 fork 的 README、测试矩阵和发布说明，只描述当前 fork 已验证的行为，不默认继承上游全部能力承诺。
- 原项目需要浏览器实现登陆动作，不适合服务器部署与Agent交互，本项目完善了命令行模式下的登陆功能，包括纯 HTTP 二维码登录，登录态导入 / 诊断 / 检查等。

### 首版稳定范围

以下能力已收敛为本 fork 当前首版稳定范围：

- `xhs login` 默认 headless 二维码登录（即--qrcode-http，含终端二维码 + 登录链接）
- `xhs status` 检查登录态
- `xhs whoami` 获取当前用户 ID
- `xhs auth doctor` 诊断当前登录态是否完整、是否可用
- `xhs auth inspect` 检查本地已保存 cookies 的字段情况（不输出敏感值）
- `xhs auth import --file` 导入 cookies
- `xhs search` 搜索笔记
- `xhs search-user` 搜索用户
- `xhs topics` 获取话题
- `xhs feed` 获取动态
- `xhs hot` 获取热门笔记
- `xhs read` 读取笔记
- `xhs comments` 获取评论
- `xhs my-notes` 获取自己的笔记
- `xhs unread` 获取未读笔记
- `xhs like` / `xhs like --undo` 点赞/取消点赞笔记
- `xhs favorite` / `xhs unfavorite` 收藏/取消收藏笔记
- `xhs comment` / `xhs delete-comment` 评论/删除评论
- `xhs follow` / `xhs unfollow` 关注/取消关注用户

### 当前未纳入发布命令面

以下能力当前不纳入本 release 的默认命令面：

- `xhs login --browser` 浏览器方式登录
- `xhs login --qrcode` 浏览器辅助二维码登录
- `xhs sub-comments` 获取子评论
- `xhs reply` 回复评论
- `xhs post` 发布笔记
- `xhs delete` 删除笔记
- `xhs user` 获取用户信息
- `xhs user-posts` 获取用户笔记
- `xhs favorites` 获取收藏笔记
- `xhs likes` 获取点赞笔记
- `xhs notifications` 获取通知

说明：

- 上述能力中，一部分是兼容/实验路径，另一部分已确认在当前 public web API 下不可稳定使用
- 它们当前不在 `xhs --help` 的默认命令列表中，也不应作为 Agent 的默认调用入口

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
xhs comment <note_id_or_url> -c "好赞"
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
