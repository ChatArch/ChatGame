# 前端测试规范

ChatGame Web 的基础可用性必须由自动化测试兜底，不能只依赖人工点击或 `vite build`。

## 测试分层

- 单元测试：覆盖纯逻辑，例如 cow-puzzle 规则、关卡数据和 API wrapper 错误转换。
- 组件测试：使用 Vitest、jsdom、Testing Library，在真实 DOM 中验证 React 页面交互。
- E2E 测试：使用 Playwright Chromium，启动真实 `chatgame` FastAPI 服务，访问打包后的静态前端。
- 安装态 smoke：构建 wheel 并 `pip install` 后，验证 `chatgame web serve` 的页面、API 和静态资源。

## 本地命令

在提交前从仓库根目录运行：

```bash
PYTHONPATH=src python -m pytest -q
python -m build
python -m mkdocs build --strict
```

在 `web/` 目录运行：

```bash
npm ci
npm run lint
npm run test
npm run build:static
npx playwright install chromium
npm run test:e2e
```

说明：

- Python 兼容门禁按 `3.10` 执行；不要求使用特定环境管理器。
- `npm ci` 必须能基于 `web/package-lock.json` 复现依赖。
- `npm run test:e2e` 会先构建 `src/chatgame/web_static`，再启动 `uvicorn chatgame.api:app`。

## 组件测试要求

组件测试位于 `web/src/**/*.test.{js,jsx,mjs}`。

必须遵守：

- 用用户可见的 role/text/label 查询元素，避免测试 CSS module 的哈希类名。
- API 请求通过 `web/src/test/mockFetch.js` mock，不依赖真实后端或外网。
- 交互测试必须验证状态变化，例如按钮 enabled/disabled、预览图出现、棋盘格 `aria-pressed`、求解结果或错误提示。
- API 错误、超时、无解、多解、唯一解都要有 UI 断言，不能只断言页面能渲染。

## E2E 要求

E2E 测试位于 `web/e2e/`。

当前基础用例覆盖：

- `/`、`/play`、`/solve`、`/contribute` 导航。
- `/play/cow-puzzle?tab=start` 的 6/8/10 尺寸、点击影响效果、演示解逐步落子和通关提示。
- `/solve/cow-puzzle?tab=solver` 的 10x10 示例求解和标注图展示。
- 上传固定图片求解，确保最终出现结果或明确错误，不得卡在加载态。
- docs/API 返回异常内容时回退到内置说明。

每个 E2E 用例都要收集 browser console error 和 page error。失败时 Playwright 会保留：

- `web/test-results/`
- `web/playwright-report/`

CI 会在失败时上传这些 artifact。

## CI 门禁

`.github/workflows/ci.yml` 在 PR 和 `main` push 上运行：

- `backend`：Python 3.10，安装 `.[dev]`，运行 `pytest`。
- `frontend`：Node 22，`npm ci`，运行 lint、Vitest、静态构建。
- `e2e`：Python 3.10 + Node 22，安装 Playwright Chromium，运行真实浏览器测试。
- `package`：构建静态前端和 Python wheel，检查 wheel 内 JS/CSS、favicon、示例图。
- `install-smoke`：安装 wheel 后启动 `chatgame web serve`，probe 页面、API、示例图。
- `docs`：Python 3.10，运行 `mkdocs build --strict`。

## 回归测试规则

以下改动必须补测试：

- 页面曾经打不开、空白、一直加载。
- 按钮点击无反应或点击后卡死。
- 上传、示例图、求解结果、错误提示行为变化。
- 安装态静态资源、路由 fallback、`chatgame web serve` 行为变化。
- API 错误/超时/无解/多解语义变化。

修复前端 bug 时，优先补组件测试；涉及真实路由、静态资源或浏览器 runtime 的问题，同时补 E2E。
