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
chatgame --tree-brief
chatgame games
chatgame solve level24.png -o solved.png
chatgame web setup
chatgame web serve
```

## 可选共享登录

ChatGame 默认不要求登录，截图上传和求解仍可匿名使用。只有在运维侧显式配置共享账号后，Web UI 才会显示登录入口；未配置时只显示“访客”，不会出现不可用的登录按钮。认证字段完全缺省时才会禁用登录；只填一部分账号字段或写入无效 TTL 会作为配置错误处理。

账号配置走 ChatEnv 的 `ChatGame` schema 或同名环境变量。密码字段必须是 PBKDF2 字符串，不要把真实账号或明文密码写入仓库：

```env
CHATGAME_AUTH_USERNAME='solver'
CHATGAME_AUTH_PASSWORD_PBKDF2='pbkdf2_sha256$600000$base64_salt$base64_digest'
CHATGAME_AUTH_USER_ID='solver-account'
CHATGAME_AUTH_DISPLAY_NAME='Puzzle Solver'
CHATGAME_AUTH_ORIGIN='http://localhost:8000'
CHATGAME_AUTH_TTL_SECONDS='86400'
```

会话和 CSRF 数据由 ChatLogin 管理，运行态文件位于 `~/.chatarch/chatgame`。

## 当前 CLI

以下为 `chatgame --tree-brief` 的注册命令面；`chatgame --tree` 会额外显示参数签名。

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
