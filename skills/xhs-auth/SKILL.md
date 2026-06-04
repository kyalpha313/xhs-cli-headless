# xhs-auth

你负责 `xhs` CLI 的认证、登录、会话恢复和退出登录。

## 何时触发

- 用户要登录小红书
- 用户要检查当前账号
- 命令返回未登录、登录过期、token 过期、会话失效
- 用户要导入 cookies 或手动恢复会话
- 用户要退出登录

## 支持命令

- `xhs login`
- `xhs login --qrcode-http`
- `xhs status --json`
- `xhs whoami --json`
- `xhs auth doctor --json`
- `xhs auth inspect --json`
- `xhs auth import --file <file> --json`
- `xhs auth import-fields --interactive`
- `xhs logout --json`

## 默认流程

例外：用户只是读取公开视频 / 公开笔记 URL、`xhslink.com` 短链或 board 时，不要因为未登录直接要求 `xhs login`。先交给 `xhs-read` 路径尝试公开 HTML fallback；fallback 失败或用户需要评论、feed、互动、账号相关能力时，再进入下面流程。

遇到认证问题时：

1. 先运行 `xhs auth doctor --json`。
2. 如果没有可用登录态，引导用户运行 `xhs login`。
3. 如果用户已有 cookies 文件，使用 `xhs auth import --file <file>`。
4. 如果用户只能复制浏览器字段，使用 `xhs auth import-fields --interactive`。
5. 恢复后运行 `xhs status --json` 验证。

不要在会话失效时反复重试业务命令。

## 输出要求

告诉用户三件事：

- 当前是否已登录
- 当前账号是谁
- 如果不可用，下一步最短恢复路径是什么
