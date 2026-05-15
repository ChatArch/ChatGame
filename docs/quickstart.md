# 快速上手

## 1. 环境准备

推荐使用 conda 管理 Python 环境：

```bash
conda create -n cow-puzzle python=3.11 -c conda-forge -y
conda activate cow-puzzle
```

安装 chatgame：

```bash
git clone <repo-url> ChatGame && cd ChatGame
pip install -e ".[dev]" -i https://pypi.tuna.tsinghua.edu.cn/simple
```

确认安装：

```bash
chatgame --version
# chatgame, version 0.1.0
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
chatgame web setup        # 检查所有依赖
chatgame web setup -i     # 同时自动安装缺失的前端依赖（npm install）
```

输出示例：

```
── Python 环境
  ✓  chatgame 0.1.0
  ✓  fastapi 0.136.1
  ✓  uvicorn 0.47.0
  ...

── Node.js 环境
  ✓  node v24.14.1  (path)
  ✓  npm  11.11.0

── 前端依赖
  ✓  node_modules 已安装

✓ 环境就绪，可运行：chatgame web serve
```

### 3.2 启动服务

```bash
chatgame web serve
```

打开浏览器访问 **http://localhost:5173**，即可使用 Web 界面求解游戏。

```bash
# 仅启动后端 API（供调试）
chatgame web serve --backend-only

# 自定义端口
chatgame web serve --port 9000 --frontend-port 3000
```

### 3.3 检查状态

```bash
chatgame web status
# 后端   http://localhost:8000   running ✓
# 前端   http://localhost:5173   running ✓
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
