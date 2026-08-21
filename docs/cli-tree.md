# CLI 树

ChatGame 使用共享的 `chatstyle.add_tree_option()` 从真实注册的 Click command surface 生成命令树：

- `chatgame --tree` 显示参数签名，适合接口审查。
- `chatgame --tree-brief` 保留同一组节点和说明，但省略参数签名。

更新 CLI 注册后，应同步测试、本文档和 README 中的命令示例。

## 完整命令树

```text
chatgame
├── --help  # Show this message and exit.
├── --version  # Show the version and exit.
├── --tree  # Print the registered CLI tree and exit.
├── --tree-brief  # Print the registered CLI tree without parameter signatures and exit.
├── games  # 列出已支持的游戏；只读文本输出。
├── solve <IMAGE> [--game GAME] [--size SIZE] [--output OUTPUT] [--verbose]  # 解析截图并输出求解步骤；--output 写入标注图。
└── web  # 管理安装态 Web 服务（后端 + 前端）。
    ├── serve [--host HOST] [--port PORT] [--reload]  # 启动长驻 Web 服务；监听指定地址和端口。
    └── setup  # 检查 Web 运行环境；只读状态输出。
```

## 简要命令树

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

## 命令边界

| 命令 | 必需输入 | 输出 | 副作用 | 边界 |
|---|---|---|---|---|
| `chatgame games` | 无 | 支持游戏的文本列表 | 只读 | 不读取或输出凭据 |
| `chatgame solve IMAGE` | 本地图片路径 | 文本求解步骤；可选标注图 | 读取图片；仅在指定 `--output` 时写文件 | 不处理凭据；输出路径由调用者选择 |
| `chatgame web setup` | 无 | 安装态依赖和静态资源状态 | 只读检查 | 不读取或输出凭据 |
| `chatgame web serve` | 无；可选 host/port | HTTP Web UI 与 API | 启动长驻网络监听进程 | `--host 0.0.0.0` 会向局域网暴露服务 |

## 更新规则

- 不实现包内树渲染器；完整树和简要树都由 ChatStyle 从真实 Click 注册树生成。
- 新增或删除命令时，先更新 CLI 注册，再更新测试和本文档。
- scaffold/template `hello` 不属于 ChatGame 业务接口；若出现，应删除公开命令面。
