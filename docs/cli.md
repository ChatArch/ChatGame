# chatgame CLI 用法

## 安装

```bash
conda activate cow-puzzle
pip install -e ".[dev]"
```

---

## 命令总览

```
chatgame --version
chatgame --help

chatgame games
chatgame solve   <IMAGE>  [-g] [-n] [-o] [-v]

chatgame web setup   [-i | -I]
chatgame web serve   [--backend-only | --frontend-only] [--port] [--frontend-port]
chatgame web status  [--port] [--frontend-port]
```

---

## 求解类

### `chatgame games`
列出已支持的游戏。

```
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
# 最简用法（终端打印答案）
chatgame solve level24.png

# 同时保存标注图
chatgame solve level24.png -o solved.png

# 指定大小 + 调试输出
chatgame solve level24.png -n 10 -v

# 非默认游戏（未来扩展）
chatgame solve level.png -g other-game
```

---

## Web 服务类

### `chatgame web setup [-i|-I]`
逐项检查 Python 依赖、Node.js、前端 `node_modules`。

| 标志 | 说明 |
|------|------|
| `-i` | 交互模式：自动 `npm install` 安装缺失的前端依赖 |
| `-I` | 非交互：只检查，不安装（默认） |

```bash
chatgame web setup       # 检查，不安装
chatgame web setup -i    # 检查 + 自动安装缺失依赖
```

### `chatgame web serve`
并行启动后端（FastAPI / uvicorn）与前端（React / Vite），`Ctrl-C` 同时停止。

| 选项 | 默认 | 说明 |
|------|------|------|
| `--backend-only` | — | 仅启动后端 |
| `--frontend-only` | — | 仅启动前端 |
| `--port` | `8000` | 后端端口 |
| `--frontend-port` | `5173` | 前端端口 |

```bash
chatgame web serve                    # 同时启动
chatgame web serve --backend-only     # 仅后端
chatgame web serve --port 9000        # 自定义端口
```

### `chatgame web status`
探测各服务端口，打印 running / stopped。

```bash
$ chatgame web status
  后端   http://localhost:8000   running ✓
  前端   http://localhost:5173   stopped ✗
```

---

## 典型工作流

```bash
# 1. 首次环境初始化
chatgame web setup -i

# 2. 启动 Web 服务
chatgame web serve

# 3. 另一个终端确认服务状态
chatgame web status

# 4. 纯 CLI 求解（不需要 Web 服务）
chatgame solve screenshot.png -o result.png
```
