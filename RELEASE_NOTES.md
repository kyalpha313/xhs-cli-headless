# v0.8.4

## 新功能

- 默认 `xhs login` 收敛为面向无 GUI / 远程服务器场景的 headless 二维码登录
- 新增认证工具链
  - `xhs auth doctor`
  - `xhs auth inspect`
  - `xhs auth import --file`
- 新增 `xhs auth import-fields`
  - 支持直接传入 `a1`、`web_session`、`webId` 等字段
  - 支持 `--interactive` 交互式粘贴浏览器 / F12 中复制的 cookie 字段
- 新增浏览器 / F12 登录恢复文档 `docs/browser-cookie-recovery.md`
  - 说明当扫码确认后触发额外验证码时，如何在用户自己的浏览器中完成验证，再把字段导回服务器 CLI

## Bug 修复

- 修复并验证纯 HTTP 二维码登录主路径
- 修正二维码登录状态提示
  - 原先在“已确认但尚未完成会话”阶段会显示“登录已成功”
  - 现在改为更准确的“已确认，正在完成登录”
- 改进二维码登录触发验证码后的错误提示
  - 明确引导用户使用 `xhs auth import --file` 或 `xhs auth import-fields --interactive`
- 改进验证码冷却日志文案
  - 明确说明冷却只是避免重试风暴，不代表验证码已经解决
- 收窄默认发布命令面，只保留已验证稳定的能力
