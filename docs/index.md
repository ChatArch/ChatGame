# chatgame

**游戏谜题截图求解工具** — 拍一张游戏截图，自动解析并给出点击顺序。

当前支持游戏：**牛牛摆放谜题**（色块区域约束 · 行列唯一 · 无相邻，与 LinkedIn Queens 同类）

---

## 三行上手

```bash
# 安装
pip install -e ".[dev]"

# 求解截图（打印答案）
chatgame solve level24.png

# 同时保存标注图
chatgame solve level24.png -o solved.png
```

→ 详细步骤见 [快速上手](quickstart.md)

---

## 功能一览

| 功能 | 命令 |
|------|------|
| 截图求解，打印点击顺序 | `chatgame solve <图片>` |
| 保存标注图（数字叠加） | `chatgame solve <图片> -o <输出>` |
| 查看支持的游戏 | `chatgame games` |
| 环境检查 + 依赖安装 | `chatgame web setup -i` |
| 启动 Web UI | `chatgame web serve` |

---

## 本地预览文档

```bash
pip install -e ".[docs]"
mkdocs serve
```
