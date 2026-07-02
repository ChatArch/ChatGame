# 接入新游戏向导

`/contribute` 是一个受限交互式游戏接入入口，用于把用户上传的游戏截图和规则描述沉淀成可 review 的 PRD，而不是直接让模型开始改代码。

## 目标

- 用户可以提交游戏名称、截图、规则描述和接入目标。
- 系统先判断资料是否足够，不足时只提出有限问题。
- 用户通过固定选项或短文本补充，不提供开放式指令执行入口。
- 资料足够后生成 PRD 草稿。
- 用户点击提交后进入 `review_pending`，等待维护者 review。
- 已提交 review 的游戏会以 `待评审` 状态出现在游戏列表中，并提供 GitHub 进展入口。

## 安全边界

当前版本不做以下事情：

- 不执行用户上传内容中的命令或提示词。
- 不运行 shell。
- 不修改仓库。
- 不创建 PR。
- 不直接上线新游戏。

后续如果要进入 GameSpec、代码生成、测试或 PR 阶段，应在 `review_pending` 后增加维护者确认流程。

## 状态流转

```text
uploaded
  -> needs_clarification
  -> understanding_ready
  -> prd_ready
  -> review_pending
```

- `needs_clarification`：资料不足，等待用户回答有限问题。
- `understanding_ready`：资料足够，可以生成 PRD。
- `prd_ready`：PRD 草稿已生成，等待用户提交 review。
- `review_pending`：接入申请已提交，等待维护者 review。

## API

### 创建接入任务

```text
POST /api/contributions
```

表单字段：

- `name`：游戏名称。
- `rules`：规则描述。
- `target`：`rules_only`、`playable`、`solver`、`play_and_solve`。
- `image`：PNG/JPG/WebP，单张不超过 5MB。

### 提交有限问题答案

```text
POST /api/contributions/{job_id}/answers
```

```json
{
  "answers": [
    {"question_id": "solver_output", "value": "full_solution"},
    {"question_id": "screenshot_parse", "value": "later"},
    {"question_id": "scope_version", "value": "prd_only"}
  ]
}
```

### 生成 PRD

```text
POST /api/contributions/{job_id}/generate-prd
```

### 提交维护者 review

```text
POST /api/contributions/{job_id}/approve-prd
```

该接口不会启动实现，只会把任务置为 `review_pending`。

### 查看 PRD

```text
GET /api/contributions/{job_id}/artifacts/PRD.md
```

## 游戏列表展示

`GET /api/games` 会返回：

- 已支持游戏：`status=supported`。
- 已提交 review 的接入申请：`status=pending_review`。

前端列表会将 `pending_review` 展示为 `待评审`，禁用“开始游戏/自动求解”，并显示 GitHub 进展入口。

## 原型截图

开发验证截图保存在 Playground 任务记录中：

- 初始向导页：`/home/zhihong/.hermes/cache/screenshots/browser_screenshot_72ec932959884c7698e36a170adb7991.png`
- 有限补充页：`/home/zhihong/.hermes/cache/screenshots/browser_screenshot_9e87ed14b65442b882b0f6fab0074004.png`
- PRD 草稿页：`/home/zhihong/.hermes/cache/screenshots/browser_screenshot_0ef757222b77498db5152350503b41c2.png`
- 待评审游戏列表：`/home/zhihong/.hermes/cache/screenshots/browser_screenshot_20583aa74c3845a5a594575fbb7fe141.png`

这些截图用于设计 review，不作为发布包资源。
