# chatgame CLI 用法

## 安装

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install chatgame
```

---

## 命令总览

```text
chatgame --version
chatgame --help

chatgame games
chatgame solve <IMAGE> [-g] [-n] [-o] [-v]

chatgame web setup
chatgame web serve [--host] [--port]
```

---

## 求解类

### `chatgame games`

列出已支持的游戏。

```text
$ chatgame games
已支持游戏：
  cow-puzzle       牛牛摆放谜题
```

### `chatgame solve <IMAGE>`

从游戏截图解析并求解，打印点击顺序。

| 选项 | 默认 | 说明 |
|------|------|------|
| `-g / --game` | `cow-puzzle` | 游戏类型 |
| `-n / --size` | 自动推断 | 棋盘边长 N |
| `-o / --output` | — | 标注结果图保存路径 |
| `-v / --verbose` | 关 | 打印颜色矩阵等调试信息 |

```bash
chatgame solve level24.png
chatgame solve level24.png -o solved.png
chatgame solve level24.png -n 10 -v
```

---

## Web 类

### `chatgame web setup`

检查安装态 Web 运行环境：

- `chatgame` 包本身
- `fastapi`
- `uvicorn`
- 包内静态资源 `chatgame/web_static`

```bash
chatgame web setup
```

### `chatgame web serve`

启动安装态 Web 服务，默认直接服务包内静态资源。

| 选项 | 默认 | 说明 |
|------|------|------|
| `--host` | `127.0.0.1` | 服务监听地址；局域网/IP 访问可设为 `0.0.0.0` |
| `--port` | `8000` | Web/API 端口 |

```bash
chatgame web serve
chatgame web serve --port 9000
chatgame web serve --host 0.0.0.0 --port 8000
```

---

## 典型工作流

```bash
# 1. 检查安装态环境
chatgame web setup

# 2. 启动 Web UI
chatgame web serve

# 3. 纯 CLI 求解
chatgame solve screenshot.png -o result.png
```
