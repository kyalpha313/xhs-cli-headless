# 能力状态总览

更新时间：2026-04-18

这份文档用于汇总 `xhs-cli-headless` 当前对外能力的实际状态，重点回答三件事：

- 哪些命令已经纳入默认 CLI 命令面并且可用
- 哪些命令仍然隐藏，仅供实验或定向验证
- 哪些命令已经确认在当前 public web API 下不可稳定使用

说明：

- 这里的“支持”强调的是当前 fork 的实际发布口径，不等同于上游仓库或源码里是否仍保留某个命令
- 这里的“已知失败”强调的是在当前真实会话里已经复现过失败，不建议作为 Agent 默认调用入口
- 真实验证细节可继续参考 `release_test_matrix.md`

## 默认支持

以下命令已经纳入默认 `xhs --help` 命令面，并且在本仓库当前发布口径下可视为优先支持能力。

### 认证与会话

| 命令 | 当前状态 | 备注 |
| --- | --- | --- |
| `xhs login` | 支持 | 默认走 headless 二维码登录 |
| `xhs login --qrcode-http` | 支持 | 与默认登录属于同一路径 |
| `xhs status` | 支持 | 检查当前登录态 |
| `xhs whoami` | 支持 | 获取当前账号信息 |
| `xhs auth doctor` | 支持 | 诊断主站 / creator 双域会话 |
| `xhs auth inspect` | 支持 | 检查已保存 cookies 字段 |
| `xhs auth import --file` | 支持 | 导入 cookies 文件 |
| `xhs auth import-fields --interactive` | 支持 | 交互式导入关键 cookie 字段 |
| `xhs logout` | 支持 | 清空本地登录态 |

### 只读发现与阅读

| 命令 | 当前状态 | 备注 |
| --- | --- | --- |
| `xhs search` | 支持 | 已真实验证 |
| `xhs search-user` | 支持 | 已真实验证 |
| `xhs topics` | 支持 | 已真实验证 |
| `xhs feed` | 支持 | 已真实验证 |
| `xhs hot` | 支持 | 已真实验证 |
| `xhs read` | 支持 | 已真实验证 |
| `xhs comments` | 支持 | 已真实验证 |
| `xhs my-notes` | 支持 | creator 列表已真实验证 |
| `xhs unread` | 支持 | 已真实验证 |

### 互动与社交

| 命令 | 当前状态 | 备注 |
| --- | --- | --- |
| `xhs like` / `xhs like --undo` | 支持 | 已真实验证 |
| `xhs favorite` / `xhs unfavorite` | 支持 | 单笔记收藏/取消收藏已真实验证 |
| `xhs board` | 支持 | 通过 HTML fallback 读取收藏专辑，已真实验证 |
| `xhs comment` | 支持 | 已真实验证 |
| `xhs reply` | 支持 | 已真实验证 |
| `xhs delete-comment` | 支持 | 已真实验证 |
| `xhs follow` / `xhs unfollow` | 支持 | 已真实验证 |

## 默认隐藏

以下命令仍保留在源码和 CLI 中，但默认不出现在 `xhs --help` 里。

### 隐藏但部分可用

| 命令 | 当前状态 | 备注 |
| --- | --- | --- |
| `xhs post` | 隐藏 | 已真实验证成功，可创建私密图文笔记，但仍与 `delete` 风险绑定，暂不公开 |
| `xhs login --browser` | 隐藏 | 本地/辅助路径保留，不作为服务器/Agent 默认登录方式 |
| `xhs login --qrcode` | 隐藏 | 浏览器辅助二维码路径保留，不作为默认入口 |

### 隐藏且已知失败

| 命令 | 当前状态 | 备注 |
| --- | --- | --- |
| `xhs delete` | 隐藏且失败 | creator 会话有效时仍失败；当前已明确映射为 `unsupported_operation` |
| `xhs sub-comments` | 隐藏且失败 | 已在真实带子评论笔记上复测，仍返回 `code -1` |
| `xhs user` | 隐藏且失败 | 当前 public web API 下持续失败 |
| `xhs user-posts` | 隐藏且失败 | 当前 public web API 下持续失败 |
| `xhs favorites` | 隐藏且失败 | 当前 public web API 下持续失败 |
| `xhs likes` | 隐藏且失败 | 当前 public web API 下持续失败 |
| `xhs notifications` | 隐藏且失败 | `mentions / likes / connections` 持续失败 |

## 已知失败与替代路线

### 收藏列表

- `xhs favorites` 当前坏掉
- `board/user` API 当前也坏掉
- 替代路线：使用 `xhs board <board_id_or_url>` 读取具体收藏专辑

### 用户页

- `xhs user`
- `xhs user-posts`

当前都未打通，不建议暴露为默认能力。

### 通知列表

- `xhs notifications`

当前 `you/mentions`、`you/likes`、`you/connections` 仍失败；`xhs unread` 可继续单独使用。

### Creator 删除

- `xhs post` 已真实成功
- `xhs delete` 当前未打通

这意味着 creator 写操作暂时不能当成完整闭环能力对外承诺。

## 当前建议

如果是 Agent 或自动化场景，建议优先使用：

- `login`
- `status`
- `whoami`
- `auth doctor`
- `search`
- `search-user`
- `topics`
- `feed`
- `hot`
- `read`
- `comments`
- `my-notes`
- `unread`
- `like`
- `favorite`
- `unfavorite`
- `board`
- `comment`
- `reply`
- `delete-comment`
- `follow`
- `unfollow`

当前不建议作为默认能力使用：

- `sub-comments`
- `user`
- `user-posts`
- `favorites`
- `likes`
- `notifications`
- `delete`

