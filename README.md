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

ChatGame 是游戏谜题截图求解工具：从截图解析棋盘，输出求解步骤，并提供安装态 Web UI。

## 快速开始

```bash
pip install chatgame
chatgame --version
chatgame --tree
chatgame games
chatgame solve level24.png -o solved.png
chatgame web setup
chatgame web serve
```

## 当前 CLI

```text
chatgame # chatgame — 游戏谜题求解工具。
├── games
├── solve IMAGE [--game GAME] [--size SIZE] [--output OUTPUT] [--verbose]
└── web
    ├── web serve [--host HOST] [--port PORT] [--reload]
    └── web setup
```

完整命令树见： https://arch.gh.wzhecnu.cn/ChatGame/cli-tree/

## 文档

- 文档首页： https://arch.gh.wzhecnu.cn/ChatGame/
- CLI 树： https://arch.gh.wzhecnu.cn/ChatGame/cli-tree/
- 英文文档： https://arch.gh.wzhecnu.cn/ChatGame/en/

## 开发验证

```bash
pip install -e ".[dev,docs]"
python -m pytest -q
mkdocs build --strict
python -m build
```

扩展前先阅读 `DEVELOP.md` 和 `AGENTS.md`。
