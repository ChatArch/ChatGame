<div align="center">
    <a href="https://pypi.python.org/pypi/chatgame">
        <img src="https://img.shields.io/pypi/v/chatgame.svg" alt="PyPI version" />
    </a>
    <a href="https://github.com/ChatArch/ChatGame/actions/workflows/ci.yml">
        <img src="https://github.com/ChatArch/ChatGame/actions/workflows/ci.yml/badge.svg" alt="Tests" />
    </a>
    <a href="https://arch.gh.wzhecnu.cn/ChatGame/">
        <img src="https://img.shields.io/badge/docs-mkdocs-blue.svg" alt="Documentation" />
    </a>
</div>

<div align="center">

[English](README.en.md) | [简体中文](README.md)
</div>

# ChatGame

ChatGame solves game puzzles from screenshots: it parses a board, prints solving steps, and provides an installed-mode Web UI.

## Quick Start

```bash
pip install chatgame
chatgame --version
chatgame --tree
chatgame --tree-brief
chatgame games
chatgame solve level24.png -o solved.png
chatgame web setup
chatgame web serve
```

## Current CLI

This is the registered `chatgame --tree-brief` surface. Run `chatgame --tree` to include parameter signatures.

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

Full command tree: https://arch.gh.wzhecnu.cn/ChatGame/en/cli-tree/

## Documentation

- Home: https://arch.gh.wzhecnu.cn/ChatGame/en/
- CLI tree: https://arch.gh.wzhecnu.cn/ChatGame/en/cli-tree/
- Chinese docs: https://arch.gh.wzhecnu.cn/ChatGame/

## Development Checks

```bash
pip install -e ".[dev,docs]"
python -m pytest -q
mkdocs build --strict
python -m build
```

See `DEVELOP.md` and `AGENTS.md` before extending the package.
