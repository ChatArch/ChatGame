# 快速上手

## 1. 环境准备

要求：

- Python `>=3.10`
- Node.js / npm 只在前端开发态需要；安装态 `chatgame web serve` 不依赖它们

建议使用干净的 Python 虚拟环境，避免系统 `numpy/scipy/sklearn` 混装导致 ABI 冲突。

```bash
python3 -m venv .venv
. .venv/bin/activate
```

安装 chatgame：

```bash
git clone <repo-url> ChatGame && cd ChatGame
pip install -e ".[dev]" -i https://pypi.tuna.tsinghua.edu.cn/simple
```

确认安装：

```bash
chatgame --version
# chatgame, version 0.1.2
```

---

## 2. 纯 CLI 求解

准备一张游戏截图，一条命令得到答案：

```bash
chatgame solve level24.png
```

输出示例：

```
解（按点击顺序）:
  第 1 步  行0 列4  热粉
  第 2 步  行1 列7  粉
  ...

棋盘（[N]=第N步点击，数字=色块ID）:
     0   1   2   3   4   5   6   7
   +────────────────────────+
 0 │ 0  0  0  0 [1] 2  2  2 │
 ...

✓ 验证通过  (51 ms)
```

**常用选项：**

```bash
# 保存标注图（数字写在原图上）
chatgame solve level24.png -o solved.png

# 棋盘大小不能自动推断时手动指定
chatgame solve level24.png -n 10

# 打印颜色矩阵等调试信息
chatgame solve level24.png -v
```

---

## 3. 启动 Web UI

### 3.1 检查环境

```bash
chatgame web setup                        # 安装态检查（优先验证包内静态资源）
chatgame web setup -i --frontend-dir ./web  # 开发态检查 + 自动安装缺失前端依赖
```

输出示例：

```
── Python 环境
  ✓  chatgame 0.1.2
  ✓  fastapi 0.136.1
  ✓  uvicorn 0.47.0

── 前端依赖
  ✓  包内静态资源已就绪：.../site-packages/chatgame/web_static

✓ 环境就绪，可运行：chatgame web serve
```

说明：

- 安装态 `web setup` 只验证 Web 运行必需项，不要求 `scikit-learn/scipy`
- 如果你要开发前端或使用源码目录，再显式传 `--frontend-dir` / `-i`

### 3.2 启动服务

```bash
chatgame web serve
```

打开浏览器访问 **http://localhost:8000**，即可使用 Web 界面求解游戏。

```bash
# 仅启动后端 API（供调试）
chatgame web serve --backend-only

# 自定义端口
chatgame web serve --port 9000

# 开发态：显式使用源码目录启动 Vite dev server
chatgame web serve --dev --frontend-dir ./web
```

### 3.3 检查状态

```bash
chatgame web status
# Web/API http://localhost:8000   running ✓
```

---

## 4. 支持的游戏

```bash
chatgame games
```

| 游戏 ID | 游戏名称 | 说明 |
|---------|----------|------|
| `cow-puzzle` | 牛牛摆放谜题 | 色块区域约束，N-Queens 变体 |

---

## 下一步

- [CLI 完整参考](cli.md)
- [牛牛谜题玩法说明](games/cow-puzzle/rules.md)
- [游戏攻略](games/cow-puzzle/strategy.md)
