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
chatgame web build   [--frontend-dir] [--dist-dir] [--clean]
chatgame web serve   [--backend-only | --frontend-only] [--port] [--frontend-port] [--dev] [--frontend-dir] [--assets-dir]
chatgame web status  [--port] [--frontend-port] [--dev]
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

说明：

- 对最终用户，运行已打包好的 Web UI 不需要 Node.js
- `web setup` 主要服务于前端开发和本地构建

| 标志 | 说明 |
|------|------|
| `-i` | 交互模式：自动 `npm install` 安装缺失的前端依赖 |
| `-I` | 非交互：只检查，不安装（默认） |

```bash
chatgame web setup       # 检查，不安装
chatgame web setup -i    # 检查 + 自动安装缺失依赖
```

### `chatgame web build`
构建前端静态资源。默认从当前目录推断前端源码目录，并输出到当前目录下的 `./.chatgame/web-dist/`。

| 选项 | 默认 | 说明 |
|------|------|------|
| `--frontend-dir` | 自动推断 | 前端源码目录 |
| `--dist-dir` | `./.chatgame/web-dist/` | 构建输出目录 |
| `--clean` | — | 构建前清空输出目录 |

```bash
# 在仓库根目录执行，输出到当前目录 .chatgame/web-dist/
chatgame web build

# 显式指定前端源码目录与输出目录
chatgame web build --frontend-dir ./web --dist-dir ./dist
```

### `chatgame web serve`
默认启动后端并服务已构建好的静态资源；加 `--dev` 后进入开发模式，同时启动 FastAPI 与 Vite。

| 选项 | 默认 | 说明 |
|------|------|------|
| `--backend-only` | — | 仅启动后端 |
| `--frontend-only` | — | 仅启动前端 |
| `--port` | `8000` | 后端端口 |
| `--frontend-port` | `5173` | 前端端口 |
| `--dev` | — | 开发模式：启动 Vite dev server |
| `--frontend-dir` | 自动推断 | 前端源码目录（开发模式） |
| `--assets-dir` | 包内静态资源 | 已构建静态资源目录 |

```bash
# 安装态：优先服务包内静态资源
chatgame web serve

# 服务指定目录中的静态资源
chatgame web serve --assets-dir ./.chatgame/web-dist

# 开发态：显式启动 Vite
chatgame web serve --dev --frontend-dir ./web
```

### `chatgame web status`
探测服务端口。默认检查后端提供的 Web/API 端口；加 `--dev` 后同时检查 Vite 端口。

```bash
$ chatgame web status
  Web/API http://localhost:8000   running ✓
```

---

## 典型工作流

```bash
# 1. 开发前首次环境初始化
chatgame web setup -i

# 2. 安装态运行（优先包内静态资源）
chatgame web serve

# 3. 开发态运行（仓库内联调）
chatgame web serve --dev --frontend-dir ./web

# 4. 本地构建静态资源
chatgame web build --frontend-dir ./web

# 5. 另一个终端确认服务状态
chatgame web status --dev

# 6. 纯 CLI 求解（不需要 Web 服务）
chatgame solve screenshot.png -o result.png
```
