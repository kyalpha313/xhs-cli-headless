# xhs-search

你负责 `xhs` CLI 的搜索与发现类只读能力。

## 何时触发

- 搜索笔记
- 搜索用户
- 查话题
- 看推荐流
- 看热榜
- 为后续阅读或总结收集候选内容

## 支持命令

- `xhs search <query> --json`
- `xhs search-user <query> --json`
- `xhs topics <query> --json`
- `xhs feed --json`
- `xhs hot --json`

## 路由建议

| 用户意图 | 命令 |
| --- | --- |
| 搜索笔记 | `xhs search <query> --json` |
| 搜索用户 | `xhs search-user <query> --json` |
| 搜索话题 | `xhs topics <query> --json` |
| 看推荐 | `xhs feed --json` |
| 看热榜 | `xhs hot --json` |

如果命令返回未登录或登录过期，交给 `xhs-auth` 处理。
