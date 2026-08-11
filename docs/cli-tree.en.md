# CLI Tree

`chatgame --tree` is generated from the real registered Click command surface. Use it to verify the public commands, arguments, and Web subcommands currently exposed by ChatGame. When CLI registration changes, update tests, this page, and README examples together.

## Top-Level Commands

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

## Command Boundaries

| Command | Status | Description |
|---|---|---|
| `chatgame games` | Implemented | List supported games. |
| `chatgame solve IMAGE` | Implemented | Parse a screenshot and output solving steps; can save an annotated image. |
| `chatgame web setup` | Implemented | Check installed-mode Web runtime dependencies and packaged static assets. |
| `chatgame web serve` | Implemented | Start the FastAPI/static-asset Web UI. |

## Update Rules

- Do not document invented commands; `--tree` output must come from the real Click registry.
- When adding or removing commands, update CLI registration first, then tests and this page.
- Scaffold/template `hello` is not a ChatGame business interface; if it appears, remove it from the public command surface.
