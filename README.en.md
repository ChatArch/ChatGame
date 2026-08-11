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
chatgame games
chatgame solve level24.png -o solved.png
chatgame web setup
chatgame web serve
```

## Current CLI

```text
chatgame # chatgame — 游戏谜题求解工具。
├── games
├── solve IMAGE [--game GAME] [--size SIZE] [--output OUTPUT] [--verbose]
└── web
    ├── web serve [--host HOST] [--port PORT] [--reload]
    └── web setup
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
