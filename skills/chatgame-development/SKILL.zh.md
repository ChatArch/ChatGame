---
name: chatgame-development
description: 维护 ChatGame 的开发规范。适用于新增游戏、整理网页资源、同步安装态静态资源与文档，以及避免把研发资料误打进安装包。
version: 0.1.0
---

# ChatGame 开发规范

这个 skill 用于维护 `ChatGame` 的项目内开发约定，重点覆盖：

- 网页资产与包内资源怎么放
- 哪些文档需要随安装发布，哪些不该进入安装包
- 新增游戏时的最小接入流程
- Web 开发态、安装态与发布态之间如何保持一致

## 目录职责

### 1. 前端源码

- 放在 `web/`
- 这里是 React / Vite 的开发态源码
- 只在前端开发时直接读取
- 修改后如果要让 `chatgame web serve` 生效，必须重新构建到 `src/chatgame/web_static/`

### 2. 安装态静态资源

- 放在 `src/chatgame/web_static/`
- 这是 Python 包真正随 `pip install .` / `pip install -e .` 提供给 `chatgame web serve` 的网页资源
- `chatgame web serve` 不直接读取 `web/src/`
- 所有网页可见改动，最终都必须体现在这里

### 3. 包内网页文档

- 放在 `src/chatgame/docs/games/<game-id>/`
- 这里只放网页运行时/API 直接需要的用户文档
- 当前约定只放：
  - `rules.md`
  - `strategy.md`
- `chatgame.api` 的 `/api/games/{id}/docs` 只应依赖这里的包内文档

### 4. 研发/算法文档

- 放在 `docs/games/<game-id>/`
- 适用于：
  - `algorithm.md`
  - `generation.md`
  - 其他研发过程说明、生成策略、验证细节
- 这些文档默认不作为网页运行时依赖
- 不要为了“安装态能读到文档”把研发文档直接复制进 `src/chatgame/docs/`

## 资源同步规则

### 网页改动

1. 修改 `web/` 下前端源码
2. 本地开发可先用 `npm run dev` 验证交互
3. 准备交付前，必须重新构建到 `src/chatgame/web_static/`
4. 再用 `chatgame web serve` 验证安装态网页是否与预期一致

原则：

- `localhost:5173` 只代表开发态
- `chatgame web serve` 代表安装态
- 任何“网页已经修好”的结论，都必须以安装态验证为准

### 文档改动

1. 如果网页上的“玩法说明 / 攻略”要显示：
   - 改 `src/chatgame/docs/games/<game-id>/rules.md`
   - 改 `src/chatgame/docs/games/<game-id>/strategy.md`
2. 如果是研发说明：
   - 改 `docs/games/<game-id>/algorithm.md`
   - 改 `docs/games/<game-id>/generation.md`
3. 不要把研发文档混进包内网页文档目录

## 安装态一致性规则

目标：以下两种方式都必须可用

- `pip install .`
- `pip install -e .`

每次涉及网页资源或包内文档时，至少验证：

1. `python -m pip install .`
2. `chatgame web serve`
3. 打开页面，确认网页可加载
4. 检查 `/api/games/<game-id>/docs` 返回非空正文

如果这次修改的是开发态调试链路，再额外验证：

1. `python -m pip install -e .`
2. `chatgame web serve --reload`

## 新增游戏最小流程

以新增 `<game-id>` 为例，按下面顺序推进。

### 1. 注册游戏

- 在 `src/chatgame/api.py` 的游戏注册表中加入新条目
- 至少提供：
  - `id`
  - `name`
  - `description`
  - 必要默认配置

### 2. 准备网页文档

- 新建 `src/chatgame/docs/games/<game-id>/rules.md`
- 新建 `src/chatgame/docs/games/<game-id>/strategy.md`

要求：

- `rules.md` 面向第一次玩的用户
- `strategy.md` 面向通关或求解技巧
- 文案必须能直接给网页展示，不依赖额外上下文

### 3. 准备研发文档

如有需要，再新增：

- `docs/games/<game-id>/algorithm.md`
- `docs/games/<game-id>/generation.md`

这类文档服务开发与维护，不强制进入安装包网页链路。

### 4. 接入前端

- 游戏列表页补卡片
- 对应详情页接入规则/攻略展示
- 如有游玩或求解页面，确保路由与入口完整

### 5. 接入后端/求解

- 如果支持求解，补齐解析/求解实现
- 保持 CLI、API、网页三侧入口一致
- 避免把纯前端交互逻辑误塞进 Python 后端，反之亦然

### 6. 验证与发布

- 跑相关测试
- 重建 `src/chatgame/web_static/`
- 验证 `pip install .`
- 验证 `chatgame web serve`
- 再考虑版本号、`CHANGELOG.md` 与 tag

## 常见错误

- 只改了 `web/src/`，没重建 `src/chatgame/web_static/`
- 在 `localhost:5173` 看起来正常，就误以为安装态也正常
- 把 `algorithm.md`、`generation.md` 复制进包内文档目录
- 只验证源码仓库运行，没验证 `pip install .`
- 只验证 `pip install -e .`，没验证普通安装

## 交付前检查清单

- 网页源码改动是否已重建到 `src/chatgame/web_static/`
- 包内网页文档是否只包含运行时需要的文档
- `chatgame web serve` 是否能显示正确页面
- `/api/games/<game-id>/docs` 是否返回非空
- `pip install .` 与 `pip install -e .` 是否至少验证过一轮
