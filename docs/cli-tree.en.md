# CLI Tree

ChatGame uses the shared `chatstyle.add_tree_option()` integration to generate its command trees from the real registered Click command surface:

- `chatgame --tree` includes parameter signatures for interface review.
- `chatgame --tree-brief` preserves the same nodes and descriptions without parameter signatures.

When CLI registration changes, update tests, this page, and README examples together.

## Full Command Tree

```text
chatgame
├── --help  # Show this message and exit.
├── --version  # Show the version and exit.
├── --tree  # Print the registered CLI tree and exit.
├── --tree-brief  # Print the registered CLI tree without parameter signatures and exit.
├── games  # 列出已支持的游戏；只读文本输出。
├── solve <IMAGE> [--game GAME] [--size SIZE] [--output OUTPUT] [--verbose]  # 解析截图并输出求解步骤；--output 写入标注图。
└── web  # 管理安装态 Web 服务（后端 + 前端）。
    ├── serve [--host HOST] [--port PORT] [--reload]  # 启动长驻 Web 服务；监听指定地址和端口。
    └── setup  # 检查 Web 运行环境；只读状态输出。
```

## Brief Command Tree

```text
chatgame
├── --help  # Show this message and exit.
├── --version  # Show the version and exit.
├── --tree  # Print the registered CLI tree and exit.
├── --tree-brief  # Print the registered CLI tree without parameter signatures and exit.
├── games  # 列出已支持的游戏；只读文本输出。
├── solve  # 解析截图并输出求解步骤；--output 写入标注图。
└── web  # 管理安装态 Web 服务（后端 + 前端）。
    ├── serve  # 启动长驻 Web 服务；监听指定地址和端口。
    └── setup  # 检查 Web 运行环境；只读状态输出。
```

## Command Boundaries

| Command | Required inputs | Outputs | Side effects | Boundary |
|---|---|---|---|---|
| `chatgame games` | None | Text list of supported games | Read-only | Does not read or print credentials |
| `chatgame solve IMAGE` | Local image path | Text solving steps; optional annotated image | Reads the image; writes only when `--output` is set | No credentials; caller selects the output path |
| `chatgame web setup` | None | Installed dependency and static-asset status | Read-only checks | Does not read or print credentials |
| `chatgame web serve` | None; optional host/port | HTTP Web UI and API | Starts a long-running network listener | `--host 0.0.0.0` exposes the service to the LAN |

## Update Rules

- Do not implement a package-local tree renderer; ChatStyle generates both trees from the real Click registry.
- When adding or removing commands, update CLI registration first, then tests and this page.
- Scaffold/template `hello` is not a ChatGame business interface; if it appears, remove it from the public command surface.
