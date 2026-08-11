# CLI 树

`chatgame --tree` 从真实注册的 Click command surface 生成，用来核对当前包对外暴露的命令、参数和 Web 子命令。更新 CLI 注册后，应同步测试、本文档和 README 中的命令示例。

## 顶层命令

```text
chatgame # chatgame — 游戏谜题求解工具。
├── --help # Show this message and exit.
├── --version # Show the version and exit.
├── --tree # Print the registered command tree.
├── games # 列出已支持的游戏。
├── solve IMAGE [--game GAME] [--size SIZE] [--output OUTPUT] [--verbose] # 从游戏截图解析并求解谜题。
└── web # Web 服务管理（后端 + 前端）。
    ├── web serve [--host HOST] [--port PORT] [--reload] # 启动 Web 服务。
    └── web setup # 检查 Web 运行环境。
```

## 命令边界

| 命令 | 状态 | 说明 |
|---|---|---|
| `chatgame games` | 已实现 | 列出当前支持的游戏。 |
| `chatgame solve IMAGE` | 已实现 | 解析截图并输出求解步骤，可保存标注图。 |
| `chatgame web setup` | 已实现 | 检查安装态 Web 运行依赖和包内静态资源。 |
| `chatgame web serve` | 已实现 | 启动 FastAPI/静态资源 Web UI。 |

## 更新规则

- 不手写虚构命令；`--tree` 输出必须来自真实 Click 注册树。
- 新增或删除命令时，先更新 CLI 注册，再更新测试和本文档。
- scaffold/template `hello` 不属于 ChatGame 业务接口；若出现，应删除公开命令面。
