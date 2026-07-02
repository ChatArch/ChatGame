"""chatgame FastAPI 后端。

端点：
  POST /solve              上传截图，返回解坐标 + 标注图（base64）+ 颜色矩阵
  GET  /games              已支持游戏列表
  GET  /games/{id}/docs    游戏规则 / 攻略 Markdown
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
import re
import uuid
import time
from pathlib import Path

from fastapi import Body, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image

from chatgame.web.paths import has_static_assets, package_static_dir

logger = logging.getLogger("chatgame.api")
logger.setLevel(logging.INFO)

app = FastAPI(title="chatgame API", version="0.1.7")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 游戏注册表 ────────────────────────────────────────────────────────────────

_GAMES = {
    "cow-puzzle": {
        "id": "cow-puzzle",
        "name": "奶牛摆放谜题",
        "description": "色块区域约束 · 行列唯一 · 无相邻，N-Queens 变体",
        "supported_sizes": [6, 8, 10],
        "status": "supported",
        "source": "built_in",
    }
}

_CONTRIBUTIONS_ROOT = Path(__file__).resolve().parents[2] / ".chatgame" / "contributions"
_ALLOWED_IMAGE_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}
_ALLOWED_ANSWER_TYPES = {"single_choice", "multi_choice", "yes_no", "short_text", "number"}
_MAX_QUESTION_COUNT = 6
_MAX_TEXT_ANSWER_LENGTH = 500
_DEFAULT_OWNER_REVIEW_MESSAGE = (
    "需求已提交，当前进入维护者 review 阶段。"
    "后续由项目维护者审核范围和优先级，再决定是否启动真实开发。"
)

def _resolve_docs_dir() -> Path:
    # 尝试从安装包内置资源（chatgame/docs/games）获取
    pkg_dir = Path(__file__).resolve().parent / "docs" / "games"
    if pkg_dir.exists():
        return pkg_dir
    # 回退：开发环境源码外层目录（../../docs/games）
    dev_dir = Path(__file__).resolve().parents[2] / "docs" / "games"
    return dev_dir

_DOCS_DIR = _resolve_docs_dir()


def _now_ms() -> int:
    return int(time.time() * 1000)


def _job_dir(job_id: str) -> Path:
    if not re.fullmatch(r"contrib_[a-z0-9_\-]+", job_id):
        raise HTTPException(404, "接入申请不存在")
    return _CONTRIBUTIONS_ROOT / job_id


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return slug[:40] or "new-game"


def _read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_event(job_id: str, event: str, payload: dict | None = None) -> None:
    line = json.dumps(
        {"ts": _now_ms(), "event": event, "payload": payload or {}},
        ensure_ascii=False,
    )
    events_path = _job_dir(job_id) / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with events_path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def _save_job(job: dict) -> dict:
    job["updated_at"] = _now_ms()
    _write_json(_job_dir(job["id"]) / "job.json", job)
    return job


def _load_job(job_id: str) -> dict:
    job = _read_json(_job_dir(job_id) / "job.json")
    if not job:
        raise HTTPException(404, "接入申请不存在")
    return job


def _sanitize_text(value: str, limit: int = 4000) -> str:
    return (value or "").replace("\x00", "").strip()[:limit]


def _question(question_id: str, text: str, options: list[tuple[str, str]]) -> dict:
    return {
        "id": question_id,
        "type": "single_choice",
        "question": text,
        "options": [{"value": value, "label": label} for value, label in options[:5]],
    }


def _analyze_contribution(job: dict) -> dict:
    rules = job.get("rules", "")
    target_type = job.get("target_type", "playable_solver")
    text = f"{job.get('name', '')}\n{rules}".lower()
    understood_rules: list[str] = []
    questions: list[dict] = []
    risk_flags: list[str] = []

    if any(word in text for word in ["数独", "sudoku"]):
        game_type = "logic_puzzle"
        summary = "这是一个数独类逻辑游戏。"
        board = {"type": "grid", "rows": 9, "cols": 9}
        understood_rules.extend([
            "每行数字不重复",
            "每列数字不重复",
            "每个宫格数字不重复",
        ])
    elif any(word in text for word in ["棋盘", "网格", "grid", "行", "列"]):
        game_type = "grid_puzzle"
        summary = "这是一个网格类谜题，规则需要进一步收敛。"
        board = {"type": "grid", "rows": None, "cols": None}
        risk_flags.append("ambiguous_board")
        questions.append(
            _question(
                "board_shape",
                "第一版棋盘结构如何限定？",
                [("fixed_grid", "固定行列网格"), ("variable_grid", "不同关卡尺寸可变"), ("unknown", "还需要再补充")],
            )
        )
    else:
        game_type = "unknown"
        summary = "系统还不能稳定判断游戏类型，需要补充棋盘结构和胜利条件。"
        board = {"type": "unknown"}
        risk_flags.extend(["ambiguous_rules", "missing_win_condition"])
        questions.append(
            _question(
                "game_structure",
                "这个游戏第一版最接近哪种结构？",
                [("grid", "网格/棋盘谜题"), ("cards", "卡牌/牌面规则"), ("word", "文字/单词谜题"), ("other", "其他")],
            )
        )

    if not any(word in rules for word in ["目标", "胜利", "完成", "通关", "获胜"]):
        risk_flags.append("missing_win_condition")
        questions.append(
            _question(
                "win_condition",
                "用户完成游戏的判定方式是什么？",
                [("fill_all", "填满/完成全部格子"), ("reach_target", "达到指定目标"), ("no_conflict", "满足全部约束且无冲突")],
            )
        )

    # 去重并限制问题数量，避免模型式输出膨胀。
    deduped = []
    seen = set()
    for item in questions:
        if item["id"] not in seen:
            deduped.append(item)
            seen.add(item["id"])
    questions = deduped[:_MAX_QUESTION_COUNT]

    sufficient = game_type != "unknown" and not {"ambiguous_rules", "missing_win_condition"}.intersection(risk_flags)
    if job.get("answers"):
        sufficient = game_type != "unknown"
        risk_flags = [flag for flag in risk_flags if flag not in {"missing_win_condition", "ambiguous_board"}]
        questions = []

    return {
        "summary": summary,
        "confidence": 0.82 if sufficient else 0.58,
        "sufficient": sufficient,
        "game_type": game_type,
        "board": board,
        "understood_rules": understood_rules or ["需要根据补充说明继续整理规则"],
        "missing_information": [item["question"] for item in questions],
        "questions": questions,
        "risk_flags": risk_flags,
    }


def _validate_answers(job: dict, answers: list[dict]) -> list[dict]:
    questions = {item["id"]: item for item in job.get("understanding", {}).get("questions", [])}
    cleaned: list[dict] = []
    for item in answers[:_MAX_QUESTION_COUNT]:
        question_id = item.get("question_id")
        if question_id not in questions:
            raise HTTPException(400, f"未知问题: {question_id}")
        question = questions[question_id]
        if question.get("type") not in _ALLOWED_ANSWER_TYPES:
            raise HTTPException(400, "不支持的问题类型")
        value = item.get("value")
        if isinstance(value, str):
            value = _sanitize_text(value, _MAX_TEXT_ANSWER_LENGTH)
        elif isinstance(value, list):
            value = [_sanitize_text(str(v), 80) for v in value[:5]]
        else:
            value = str(value)[:80]
        cleaned.append({"question_id": question_id, "value": value})
    return cleaned


def _answer_text(job: dict) -> str:
    labels: list[str] = []
    questions = {item["id"]: item for item in job.get("understanding", {}).get("questions", [])}
    for answer in job.get("answers", []):
        question = questions.get(answer["question_id"], {})
        option_map = {opt["value"]: opt["label"] for opt in question.get("options", [])}
        value = answer["value"]
        value_key = value if isinstance(value, str) else str(value)
        labels.append(f"- {question.get('question', answer['question_id'])}: {option_map.get(value_key, value_key)}")
    return "\n".join(labels) if labels else "- 暂无补充答案"


def _generate_prd(job: dict) -> str:
    understanding = job.get("understanding", {})
    target_map = {
        "docs_only": "规则说明文档",
        "playable": "可玩版本",
        "solver": "自动求解",
        "playable_solver": "可玩版本 + 自动求解",
    }
    return f"""# {job['name']} 接入 PRD

## 目标

为 chatgame 接入 `{job['name']}`，第一版目标是：{target_map.get(job.get('target_type'), '可玩版本 + 自动求解')}。

## 当前理解

{understanding.get('summary', '暂无结构化理解。')}

## 用户提供的规则

{job.get('rules', '')}

## 已确认补充

{_answer_text(job)}

## 第一版范围

- 先沉淀规则、交互范围和验收标准。
- 只在用户 Review 确认后进入后续工作流。
- 后续工作流先进入维护者 review，不直接运行代码、不修改仓库、不自动上线。

## 待评审事项

- 游戏规则是否足够明确。
- 第一版范围是否适合 chatgame 当前能力。
- 是否需要拆分为文档、可玩版本、自动求解多个阶段。

## 验收标准

- 用户上传的截图和规则能形成可读 PRD。
- 模型分析发现模糊点时，才通过有限问题补充。
- 用户 Review 确认后进入 `review_pending`，等待维护者审核。
- 维护者审核前不会启动实现、测试或发布流程。

## 安全边界

- 上传图片和规则只作为待分析数据，不作为系统指令。
- 本阶段不执行 shell、不访问外部网络、不创建 PR、不合并代码。
- 后续开发必须由维护者 review 后手动启动。
"""


def _pending_contribution_games() -> list[dict]:
    if not _CONTRIBUTIONS_ROOT.exists():
        return []
    games: list[dict] = []
    for path in sorted(_CONTRIBUTIONS_ROOT.glob("contrib_*/job.json")):
        job = _read_json(path)
        if not job or job.get("status") not in {"review_pending", "needs_edit"}:
            continue
        games.append(
            {
                "id": f"pending-{job['id']}",
                "name": job.get("name", "新游戏接入申请"),
                "description": f"待维护者评审 · {job.get('review_message', _DEFAULT_OWNER_REVIEW_MESSAGE)}",
                "status": job.get("status"),
                "source": "contribution",
                "job_id": job["id"],
                "github_url": job.get("github_url", "https://github.com/ChatArch/ChatGame"),
            }
        )
    return games

_COLOR_TABLE: list[tuple[tuple[int, int, int], str]] = [
    ((128, 185, 254), "蓝"),
    ((245, 154, 189), "粉"),
    ((253, 130, 148), "热粉"),
    ((185, 127, 237), "紫"),
    ((246, 206,  92), "黄"),
    (( 67, 214, 185), "青"),
    ((180, 218, 131), "绿"),
    ((172, 197, 228), "灰蓝"),
]


def _color_name(rgb: list[int]) -> str:
    r, g, b = rgb
    return min(
        _COLOR_TABLE,
        key=lambda t: (r - t[0][0]) ** 2 + (g - t[0][1]) ** 2 + (b - t[0][2]) ** 2,
    )[1]


def _resolve_assets_dir() -> Path | None:
    if os.getenv("CHATGAME_DISABLE_WEB_UI") == "1":
        return None

    candidates: list[Path] = []
    env_dir = os.getenv("CHATGAME_WEB_ASSETS_DIR")
    if env_dir:
        candidates.append(Path(env_dir).expanduser().resolve())
    candidates.append(package_static_dir())

    for candidate in candidates:
        if has_static_assets(candidate):
            return candidate
    return None


_ASSETS_DIR = _resolve_assets_dir()


# ── 路由 ──────────────────────────────────────────────────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = uuid.uuid4().hex[:8]
    request.state.request_id = request_id
    t0 = time.perf_counter()
    logger.info(
        "request.start id=%s method=%s path=%s",
        request_id,
        request.method,
        request.url.path,
    )
    try:
        response = await call_next(request)
    except Exception:
        elapsed = round((time.perf_counter() - t0) * 1000)
        logger.exception(
            "request.error id=%s method=%s path=%s elapsed_ms=%s",
            request_id,
            request.method,
            request.url.path,
            elapsed,
        )
        raise

    elapsed = round((time.perf_counter() - t0) * 1000)
    logger.info(
        "request.finish id=%s method=%s path=%s status=%s elapsed_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/games")
@app.get("/api/games")
def list_games():
    games = list(_GAMES.values()) + _pending_contribution_games()
    return {"games": games}


@app.post("/contributions")
@app.post("/api/contributions")
async def create_contribution(
    image: UploadFile = File(...),
    name: str = Form(...),
    rules: str = Form(...),
    target_type: str = Form("playable_solver"),
):
    clean_name = _sanitize_text(name, 80)
    clean_rules = _sanitize_text(rules, 4000)
    if not clean_name or not clean_rules:
        raise HTTPException(400, "游戏名称和规则描述不能为空")
    if target_type not in {"docs_only", "playable", "solver", "playable_solver"}:
        raise HTTPException(400, "不支持的接入目标")
    if image.content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, "仅支持 PNG、JPG、WebP 图片")

    raw = await image.read()
    if not raw or len(raw) > 5 * 1024 * 1024:
        raise HTTPException(400, "图片不能为空，且不能超过 5MB")
    try:
        with Image.open(io.BytesIO(raw)) as img:
            cleaned = img.convert("RGB")
            image_width, image_height = cleaned.size
            if image_width < 20 or image_height < 20:
                raise ValueError("图片尺寸过小")
    except Exception as exc:
        raise HTTPException(400, f"无法读取图片: {exc}") from exc

    job_id = f"contrib_{int(time.time())}_{_slugify(clean_name)}_{uuid.uuid4().hex[:6]}"
    job_path = _job_dir(job_id)
    upload_dir = job_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    image_path = upload_dir / "screenshot.png"
    cleaned.save(image_path, format="PNG")

    job = {
        "id": job_id,
        "game_id": _slugify(clean_name),
        "name": clean_name,
        "rules": clean_rules,
        "target_type": target_type,
        "status": "analyzing",
        "created_at": _now_ms(),
        "updated_at": _now_ms(),
        "image": {
            "filename": image.filename or "screenshot.png",
            "content_type": image.content_type,
            "width": image_width,
            "height": image_height,
        },
        "answers": [],
        "github_url": "https://github.com/ChatArch/ChatGame",
    }
    job["understanding"] = _analyze_contribution(job)
    job["status"] = "understanding_ready" if job["understanding"]["sufficient"] else "needs_clarification"
    _save_job(job)
    _write_json(job_path / "input.json", {"name": clean_name, "rules": clean_rules, "target_type": target_type})
    _write_json(job_path / "model-understanding.json", job["understanding"])
    _append_event(job_id, "created", {"status": job["status"]})
    return job


@app.get("/contributions/{job_id}")
@app.get("/api/contributions/{job_id}")
def get_contribution(job_id: str):
    return _load_job(job_id)


@app.post("/contributions/{job_id}/answers")
@app.post("/api/contributions/{job_id}/answers")
def answer_contribution_questions(job_id: str, payload: dict = Body(...)):
    job = _load_job(job_id)
    answers = payload.get("answers")
    if not isinstance(answers, list):
        raise HTTPException(400, "answers 必须是数组")
    job["answers"] = _validate_answers(job, answers)
    job["understanding"] = _analyze_contribution(job)
    job["status"] = "understanding_ready" if job["understanding"]["sufficient"] else "needs_clarification"
    _write_json(_job_dir(job_id) / "answers.json", job["answers"])
    _write_json(_job_dir(job_id) / "model-understanding.json", job["understanding"])
    _save_job(job)
    _append_event(job_id, "answers_submitted", {"status": job["status"]})
    return job


@app.post("/contributions/{job_id}/reanalyze")
@app.post("/api/contributions/{job_id}/reanalyze")
def reanalyze_contribution(job_id: str):
    job = _load_job(job_id)
    job["understanding"] = _analyze_contribution(job)
    job["status"] = "understanding_ready" if job["understanding"]["sufficient"] else "needs_clarification"
    _write_json(_job_dir(job_id) / "model-understanding.json", job["understanding"])
    _save_job(job)
    _append_event(job_id, "reanalyzed", {"status": job["status"]})
    return job


@app.post("/contributions/{job_id}/generate-prd")
@app.post("/api/contributions/{job_id}/generate-prd")
def generate_contribution_prd(job_id: str):
    job = _load_job(job_id)
    if job.get("status") not in {"understanding_ready", "prd_ready", "needs_edit"}:
        raise HTTPException(400, "请先完成模型分析并处理模糊点")
    prd = _generate_prd(job)
    job["prd"] = prd
    job["status"] = "prd_ready"
    (_job_dir(job_id) / "PRD.md").write_text(prd, encoding="utf-8")
    _save_job(job)
    _append_event(job_id, "prd_generated", {"status": job["status"]})
    return job


@app.post("/contributions/{job_id}/edit-prd")
@app.post("/api/contributions/{job_id}/edit-prd")
def edit_contribution_prd(job_id: str, payload: dict = Body(...)):
    job = _load_job(job_id)
    if job.get("status") not in {"prd_ready", "review_pending", "needs_edit"}:
        raise HTTPException(400, "当前状态不能编辑 PRD")
    content = _sanitize_text(payload.get("content", ""), 12000)
    if not content:
        raise HTTPException(400, "PRD 内容不能为空")
    job["prd"] = content
    job["status"] = "prd_ready"
    (_job_dir(job_id) / "PRD.md").write_text(content, encoding="utf-8")
    _save_job(job)
    _append_event(job_id, "prd_edited", {"status": job["status"]})
    return job


@app.post("/contributions/{job_id}/submit-review")
@app.post("/api/contributions/{job_id}/submit-review")
def submit_contribution_review(job_id: str):
    job = _load_job(job_id)
    if job.get("status") != "prd_ready" or not job.get("prd"):
        raise HTTPException(400, "请先生成并确认 PRD")
    job["status"] = "review_pending"
    job["review_message"] = _DEFAULT_OWNER_REVIEW_MESSAGE
    _save_job(job)
    _append_event(job_id, "review_submitted", {"status": job["status"]})
    return {
        **job,
        "user_message": "已确认进入后续工作流。当前会先进入维护者 review，审核需求范围后再决定是否启动真实开发；你也可以在 GitHub 查看项目进展。",
    }


@app.get("/contributions/{job_id}/artifacts/PRD.md")
@app.get("/api/contributions/{job_id}/artifacts/PRD.md")
def contribution_prd(job_id: str):
    path = _job_dir(job_id) / "PRD.md"
    if not path.exists():
        raise HTTPException(404, "PRD 尚未生成")
    return {"content": path.read_text(encoding="utf-8")}


@app.get("/games/{game_id}/docs")
@app.get("/api/games/{game_id}/docs")
def game_docs(game_id: str):
    if game_id not in _GAMES:
        raise HTTPException(404, f"游戏 {game_id!r} 不存在")
    doc_dir = _DOCS_DIR / game_id
    rules = (doc_dir / "rules.md").read_text(encoding="utf-8") if (doc_dir / "rules.md").exists() else ""
    strategy = (doc_dir / "strategy.md").read_text(encoding="utf-8") if (doc_dir / "strategy.md").exists() else ""
    return {"rules": rules, "strategy": strategy}


@app.post("/solve")
@app.post("/api/solve")
async def solve_puzzle(
    request: Request,
    image: UploadFile = File(...),
    game: str = Form("cow-puzzle"),
    n: int | None = Form(None),
):
    request_id = getattr(request.state, "request_id", "-")
    stage_t0 = time.perf_counter()

    def log_stage(stage: str, **extra) -> None:
        elapsed = round((time.perf_counter() - stage_t0) * 1000)
        extra_text = " ".join(f"{key}={value}" for key, value in extra.items())
        logger.info(
            "solve.%s id=%s elapsed_ms=%s%s",
            stage,
            request_id,
            elapsed,
            f" {extra_text}" if extra_text else "",
        )

    if game not in _GAMES:
        raise HTTPException(400, f"未知游戏 {game!r}")
    if n is not None and n <= 0:
        raise HTTPException(400, "棋盘边长必须为正整数")

    # 读取图像
    log_stage("start", filename=image.filename, content_type=image.content_type, n=n)
    image.file.seek(0)
    raw = image.file.read()
    log_stage("read", bytes=len(raw))
    try:
        with Image.open(io.BytesIO(raw)) as img:
            image_width, image_height = img.size
    except Exception as e:
        raise HTTPException(400, f"无法读取图像: {e}") from e

    # 保存临时文件（parse 需要路径）
    import tempfile, os
    suffix = Path(image.filename or "img.png").suffix or ".png"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(raw)
        tmp_path = tmp.name

    try:
        t0 = time.perf_counter()
        from chatgame.games.cow_puzzle.parse import parse
        from chatgame.games.cow_puzzle.solver import (
            SearchLimitExceeded,
            find_solutions,
            verify,
        )

        try:
            color_ids, samples, bbox = parse(tmp_path, n=n)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        actual_n = color_ids.shape[0]
        log_stage("parsed", actual_n=actual_n, bbox=bbox)

        try:
            solutions = find_solutions(color_ids, limit=2, max_nodes=200_000)
        except SearchLimitExceeded as exc:
            log_stage("search_limit", max_nodes=200_000)
            raise HTTPException(
                422,
                "求解搜索超限，请确认截图是否清晰，或手动选择正确尺寸后重试",
            ) from exc
        elapsed = round((time.perf_counter() - t0) * 1000)
        log_stage("solved", solutions=len(solutions))

        if not solutions:
            raise HTTPException(422, "无解，请检查截图是否清晰，或确认当前关卡受支持")

        solution = solutions[0]
        errors = verify(color_ids, solution)
        if errors:
            raise HTTPException(422, f"解验证失败: {errors}")
        solution_status = "multiple" if len(solutions) > 1 else "unique"
        message = (
            "当前截图存在多个合法解，已先给出其中一个；建议确认关卡是否应为唯一解。"
            if solution_status == "multiple"
            else "已找到唯一解。"
        )

        # 颜色名称
        color_names = [
            _color_name(samples[color_ids == cid][0].tolist())
            for cid in range(actual_n)
        ]

        # 步骤列表（按行列顺序排）
        ordered = sorted(enumerate(solution), key=lambda x: (x[1][0], x[1][1]))
        steps = [
            {
                "step": click_num,
                "row": r,
                "col": c,
                "color_id": cid,
                "color_name": color_names[cid],
            }
            for click_num, (cid, (r, c)) in enumerate(ordered, 1)
        ]

        # 颜色矩阵
        grid = color_ids.tolist()

        # 标注图 → base64
        out_buf = io.BytesIO()
        _annotate_to_buf(tmp_path, solution, bbox, actual_n, out_buf)
        annotated_b64 = base64.b64encode(out_buf.getvalue()).decode()
        log_stage("annotated", output_bytes=len(out_buf.getvalue()))

        return {
            "n": actual_n,
            "solution_status": solution_status,
            "solution_count": len(solutions),
            "solution_count_limit": 2,
            "message": message,
            "steps": steps,
            "grid": grid,
            "grid_bbox": bbox,
            "image_width": image_width,
            "image_height": image_height,
            "annotated_image": annotated_b64,
            "elapsed_ms": elapsed,
        }
    finally:
        os.unlink(tmp_path)


def _annotate_to_buf(image_path, solution, bbox, n, buf):
    """标注图写入 BytesIO 而非文件。"""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    x0, y0, x1, y1 = bbox
    cell_w = (x1 - x0) / n
    cell_h = (y1 - y0) / n

    ordered = sorted(enumerate(solution), key=lambda x: (x[1][0], x[1][1]))
    for click_num, (_, (r, c)) in enumerate(ordered, 1):
        cx = int(x0 + (c + 0.5) * cell_w)
        cy = int(y0 + (r + 0.5) * cell_h)
        radius = int(min(cell_w, cell_h) * 0.35)
        draw.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            fill=(220, 50, 50), outline=(255, 255, 255), width=2,
        )
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                size=int(radius * 1.2),
            )
        except OSError:
            font = ImageFont.load_default()
        text = str(click_num)
        bbox_t = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox_t[2] - bbox_t[0], bbox_t[3] - bbox_t[1]
        draw.text((cx - tw // 2, cy - th // 2), text, fill="white", font=font)

    img.save(buf, format="PNG")


@app.get("/{full_path:path}", include_in_schema=False)
def serve_web_app(full_path: str):
    if _ASSETS_DIR is None:
        raise HTTPException(404, "Web 静态资源未就绪")

    relative = full_path.lstrip("/")
    if not relative:
        return FileResponse(_ASSETS_DIR / "index.html")

    target = (_ASSETS_DIR / relative).resolve()
    assets_root = _ASSETS_DIR.resolve()
    try:
        target.relative_to(assets_root)
    except ValueError as exc:
        raise HTTPException(404, "非法路径") from exc

    if target.is_file():
        return FileResponse(target)

    if "." not in Path(relative).name:
        return FileResponse(_ASSETS_DIR / "index.html")

    raise HTTPException(404, "资源不存在")
