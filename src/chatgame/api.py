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
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel
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
        "badge": "已支持",
    }
}

def _resolve_docs_dir() -> Path:
    # 尝试从安装包内置资源（chatgame/docs/games）获取
    pkg_dir = Path(__file__).resolve().parent / "docs" / "games"
    if pkg_dir.exists():
        return pkg_dir
    # 回退：开发环境源码外层目录（../../docs/games）
    dev_dir = Path(__file__).resolve().parents[2] / "docs" / "games"
    return dev_dir

_DOCS_DIR = _resolve_docs_dir()

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
    games = list(_GAMES.values())
    games.extend(_list_pending_contribution_games())
    return {"games": games}


@app.get("/games/{game_id}/docs")
@app.get("/api/games/{game_id}/docs")
def game_docs(game_id: str):
    if game_id not in _GAMES:
        raise HTTPException(404, f"游戏 {game_id!r} 不存在")
    doc_dir = _DOCS_DIR / game_id
    rules = (doc_dir / "rules.md").read_text(encoding="utf-8") if (doc_dir / "rules.md").exists() else ""
    strategy = (doc_dir / "strategy.md").read_text(encoding="utf-8") if (doc_dir / "strategy.md").exists() else ""
    return {"rules": rules, "strategy": strategy}


# ── 受限交互式游戏接入向导原型 ────────────────────────────────────────────────

_ALLOWED_TARGETS = {
    "rules_only": "只生成规则说明",
    "playable": "做可玩版本",
    "solver": "做自动求解",
    "play_and_solve": "可玩 + 自动求解",
}
_ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}
_MAX_UPLOAD_BYTES = 5 * 1024 * 1024
_GITHUB_PROGRESS_URL = "https://github.com/ChatArch/ChatGame"
_REVIEW_STATUSES = {"review_pending", "prd_approved"}


class ContributionAnswer(BaseModel):
    question_id: str
    value: str | list[str]


class ContributionAnswersPayload(BaseModel):
    answers: list[ContributionAnswer]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _contributions_root() -> Path:
    env_dir = os.getenv("CHATGAME_CONTRIBUTIONS_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return (Path.cwd() / ".chatgame" / "contributions").resolve()


def _list_pending_contribution_games() -> list[dict]:
    root = _contributions_root()
    if not root.exists():
        return []

    games: list[dict] = []
    for state_path in sorted(root.glob("contrib_*/state.json")):
        try:
            job = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if job.get("status") not in _REVIEW_STATUSES:
            continue
        source = job.get("input", {})
        name = source.get("name") or "待评审游戏"
        target = source.get("target", "play_and_solve")
        games.append({
            "id": job.get("job_id", state_path.parent.name),
            "name": name,
            "description": f"接入申请已提交，等待维护者 review · {_ALLOWED_TARGETS.get(target, '待评审')}",
            "status": "pending_review",
            "badge": "待评审",
            "progress_url": _GITHUB_PROGRESS_URL,
        })
    return games


def _job_dir(job_id: str) -> Path:
    if not re.fullmatch(r"contrib_[0-9a-zA-Z_\-]+", job_id):
        raise HTTPException(404, "接入任务不存在")
    return _contributions_root() / job_id


def _read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_event(job_dir: Path, event: str, payload: dict | None = None) -> None:
    record = {"time": _now_iso(), "event": event, "payload": payload or {}}
    with (job_dir / "events.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _question(question_id: str, question: str, options: list[tuple[str, str]]) -> dict:
    return {
        "id": question_id,
        "type": "single_choice",
        "question": question,
        "options": [{"value": value, "label": label} for value, label in options],
    }


def _answer_map(answers: list[dict]) -> dict[str, str | list[str]]:
    return {item["question_id"]: item["value"] for item in answers}


def _infer_board(name: str, rules: str) -> dict:
    text = f"{name}\n{rules}".lower()
    size_match = re.search(r"(\d+)\s*[x×*]\s*(\d+)", text)
    if size_match:
        return {"type": "grid", "rows": int(size_match.group(1)), "cols": int(size_match.group(2))}
    if "数独" in text or "sudoku" in text:
        return {"type": "grid", "rows": 9, "cols": 9}
    if "棋盘" in text or "格" in text or "grid" in text:
        return {"type": "grid", "rows": None, "cols": None}
    return {"type": "unknown", "rows": None, "cols": None}


def _analyze_contribution(name: str, rules: str, target: str, answers: list[dict]) -> dict:
    answer_by_id = _answer_map(answers)
    text = f"{name}\n{rules}"
    lower = text.lower()
    questions: list[dict] = []
    missing: list[str] = []
    risk_flags: list[str] = []
    board = _infer_board(name, rules)

    if any(token in lower for token in ["ignore previous", "忽略之前", "执行命令", "system prompt"]):
        risk_flags.append("possible_prompt_injection")

    understood_rules: list[str] = []
    if "数独" in lower or "sudoku" in lower:
        understood_rules.extend(["每行不重复", "每列不重复", "每个宫格不重复"])
    if any(token in rules for token in ["行", "row"]):
        understood_rules.append("存在行约束")
    if any(token in rules for token in ["列", "column"]):
        understood_rules.append("存在列约束")
    if any(token in rules for token in ["相邻", "adjacent"]):
        understood_rules.append("存在相邻限制")
    if any(token in rules for token in ["区域", "颜色", "region", "color"]):
        understood_rules.append("存在区域/颜色约束")
    if not understood_rules:
        understood_rules.append("已收到规则描述，但规则类型仍需补充确认")

    if len(rules.strip()) < 24 and "rule_detail" not in answer_by_id:
        missing.append("规则描述过短，需要补充核心玩法和胜利条件")
        questions.append({
            "id": "rule_detail",
            "type": "short_text",
            "question": "请用 1-3 句话补充核心玩法、限制条件和胜利条件。",
            "max_length": 500,
        })

    if board["type"] == "unknown" and "board_shape" not in answer_by_id:
        missing.append("棋盘或局面结构不明确")
        questions.append(_question("board_shape", "这个游戏的主要局面结构是什么？", [
            ("grid", "网格/棋盘"),
            ("cards", "卡牌/牌堆"),
            ("graph", "节点/连线"),
            ("other", "其他结构"),
        ]))

    if target in {"solver", "play_and_solve"} and "solver_output" not in answer_by_id:
        missing.append("自动求解结果展示方式未确认")
        questions.append(_question("solver_output", "自动求解结果第一版怎么展示？", [
            ("full_solution", "展示完整答案"),
            ("next_hint", "只给下一步提示"),
            ("both", "完整答案 + 下一步提示"),
        ]))

    if "screenshot_parse" not in answer_by_id:
        missing.append("截图识别是否进入第一版范围未确认")
        questions.append(_question("screenshot_parse", "第一版是否需要支持截图识别？", [
            ("v1", "第一版支持"),
            ("later", "第二版再做"),
            ("no", "不需要"),
        ]))

    if "scope_version" not in answer_by_id:
        missing.append("第一版范围需要确认")
        questions.append(_question("scope_version", "第一版接入范围建议定到哪里？", [
            ("prd_only", "只生成 PRD 草稿"),
            ("spec_next", "PRD 后再生成 GameSpec"),
            ("manual_review", "PRD 确认后人工评审再实现"),
        ]))

    sufficient = not questions and not risk_flags
    confidence = 0.35
    confidence += 0.2 if len(rules.strip()) >= 24 else 0
    confidence += 0.15 if board["type"] != "unknown" else 0
    confidence += min(len(answer_by_id) * 0.08, 0.24)
    confidence -= 0.18 if risk_flags else 0
    confidence = max(0.1, min(round(confidence, 2), 0.95))

    return {
        "summary": f"这是一个{_ALLOWED_TARGETS.get(target, '游戏接入')}任务，当前已识别出 {board['type']} 类型局面。",
        "confidence": confidence,
        "sufficient": sufficient,
        "game_type": "logic_puzzle" if board["type"] == "grid" else "unknown",
        "board": board,
        "understood_rules": list(dict.fromkeys(understood_rules)),
        "missing_information": missing,
        "questions": questions[:4],
        "risk_flags": risk_flags,
        "safety_note": "当前原型只生成 PRD，不执行代码、不修改仓库、不创建 PR。",
    }


def _render_prd(job: dict) -> str:
    source = job["input"]
    understanding = job["understanding"]
    answers = _answer_map(job.get("answers", []))
    target_label = _ALLOWED_TARGETS.get(source.get("target"), source.get("target", "未指定"))
    rules = "\n".join(f"- {rule}" for rule in understanding.get("understood_rules", []))
    answers_md = "\n".join(f"- {key}: {value}" for key, value in answers.items()) or "- 暂无补充答案"
    rows = understanding.get("board", {}).get("rows") or "待确认"
    cols = understanding.get("board", {}).get("cols") or "待确认"

    return f"""# {source['name']} 接入 PRD

## 目标

为 chatgame 接入 `{source['name']}` 的第一版需求草稿，目标类型：{target_label}。

## 当前理解

- 游戏类型：{understanding.get('game_type', 'unknown')}
- 局面结构：{understanding.get('board', {}).get('type', 'unknown')}
- 棋盘规模：{rows} x {cols}
- 理解置信度：{understanding.get('confidence')}

## 已理解规则

{rules}

## 用户补充

{answers_md}

## 第一版范围

- 先沉淀 PRD 和结构化理解，不直接生成代码。
- 需要用户确认 PRD 后，才允许进入 GameSpec 或实现计划阶段。
- 截图识别、自动求解和可玩版本是否进入第一版，以用户补充答案为准。

## 安全约束

- 上传图片和规则描述只作为待分析数据。
- 不执行用户内容中的任何命令或提示词指令。
- 当前阶段不修改仓库、不运行 shell、不创建 PR。
- 后续进入实现阶段前必须再次人工确认。

## 验收标准

- 用户可以看到模型对游戏规则的结构化理解。
- 信息不足时，系统通过有限选项要求用户补充。
- 用户确认后生成本 PRD 草稿。
- 用户点击提交审核后，任务状态变为 `review_pending`，维护者 review 后再决定是否进入实现阶段。
"""


def _load_job(job_id: str) -> dict:
    job_dir = _job_dir(job_id)
    if not job_dir.exists():
        raise HTTPException(404, "接入任务不存在")
    job = _read_json(job_dir / "state.json")
    if not job:
        raise HTTPException(404, "接入任务不存在")
    prd_path = job_dir / "PRD.md"
    if prd_path.exists():
        job["prd"] = prd_path.read_text(encoding="utf-8")
    return job


def _save_job(job: dict) -> dict:
    job["updated_at"] = _now_iso()
    job_dir = _job_dir(job["job_id"])
    _write_json(job_dir / "state.json", job)
    _write_json(job_dir / "model-understanding.json", job["understanding"])
    _write_json(job_dir / "answers.json", job.get("answers", []))
    return _load_job(job["job_id"])


@app.post("/contributions")
@app.post("/api/contributions")
async def create_contribution(
    name: str = Form(...),
    rules: str = Form(...),
    target: str = Form("play_and_solve"),
    image: UploadFile = File(...),
):
    if target not in _ALLOWED_TARGETS:
        raise HTTPException(400, "未知接入目标")
    if image.content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, "只支持 PNG / JPG / WebP 图片")

    raw = image.file.read(_MAX_UPLOAD_BYTES + 1)
    if len(raw) > _MAX_UPLOAD_BYTES:
        raise HTTPException(400, "图片不能超过 5MB")
    try:
        with Image.open(io.BytesIO(raw)) as img:
            image_size = img.size
    except Exception as exc:
        raise HTTPException(400, f"无法读取图片: {exc}") from exc

    job_id = f"contrib_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    job_dir = _job_dir(job_id)
    uploads_dir = job_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(image.filename or "screenshot.png").suffix.lower() or ".png"
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        suffix = ".png"
    image_path = uploads_dir / f"screenshot{suffix}"
    image_path.write_bytes(raw)

    input_data = {
        "name": name.strip(),
        "rules": rules.strip(),
        "target": target,
        "image": {"path": str(image_path), "filename": image.filename, "size": image_size},
    }
    understanding = _analyze_contribution(input_data["name"], input_data["rules"], target, [])
    status = "understanding_ready" if understanding["sufficient"] else "needs_clarification"
    job = {
        "job_id": job_id,
        "status": status,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "input": input_data,
        "understanding": understanding,
        "answers": [],
    }
    _write_json(job_dir / "input.json", input_data)
    _write_json(job_dir / "state.json", job)
    _write_json(job_dir / "model-understanding.json", understanding)
    _write_json(job_dir / "answers.json", [])
    _append_event(job_dir, "created", {"status": status})
    return _load_job(job_id)


@app.get("/contributions/{job_id}")
@app.get("/api/contributions/{job_id}")
def get_contribution(job_id: str):
    return _load_job(job_id)


@app.post("/contributions/{job_id}/answers")
@app.post("/api/contributions/{job_id}/answers")
def answer_contribution_questions(job_id: str, payload: ContributionAnswersPayload):
    job = _load_job(job_id)
    merged = _answer_map(job.get("answers", []))
    for answer in payload.answers:
        merged[answer.question_id] = answer.value
    job["answers"] = [
        {"question_id": question_id, "value": value}
        for question_id, value in sorted(merged.items())
    ]
    job["understanding"] = _analyze_contribution(
        job["input"]["name"],
        job["input"]["rules"],
        job["input"]["target"],
        job["answers"],
    )
    job["status"] = "understanding_ready" if job["understanding"]["sufficient"] else "needs_clarification"
    _append_event(_job_dir(job_id), "answers_submitted", {"status": job["status"]})
    return _save_job(job)


@app.post("/contributions/{job_id}/reanalyze")
@app.post("/api/contributions/{job_id}/reanalyze")
def reanalyze_contribution(job_id: str):
    job = _load_job(job_id)
    job["understanding"] = _analyze_contribution(
        job["input"]["name"],
        job["input"]["rules"],
        job["input"]["target"],
        job.get("answers", []),
    )
    job["status"] = "understanding_ready" if job["understanding"]["sufficient"] else "needs_clarification"
    _append_event(_job_dir(job_id), "reanalyzed", {"status": job["status"]})
    return _save_job(job)


@app.post("/contributions/{job_id}/generate-prd")
@app.post("/api/contributions/{job_id}/generate-prd")
def generate_contribution_prd(job_id: str):
    job = _load_job(job_id)
    if job["status"] not in {"understanding_ready", "prd_ready"}:
        raise HTTPException(409, "请先补充并确认模型理解，再生成 PRD")
    prd = _render_prd(job)
    (_job_dir(job_id) / "PRD.md").write_text(prd, encoding="utf-8")
    job["status"] = "prd_ready"
    _append_event(_job_dir(job_id), "prd_generated", {})
    return _save_job(job)


@app.post("/contributions/{job_id}/approve-prd")
@app.post("/api/contributions/{job_id}/approve-prd")
def approve_contribution_prd(job_id: str):
    job = _load_job(job_id)
    if not (_job_dir(job_id) / "PRD.md").exists():
        raise HTTPException(409, "请先生成 PRD")
    job["status"] = "review_pending"
    job["review"] = {
        "status": "pending",
        "message": "接入申请已提交，维护者 review 后会决定是否进入实现阶段。",
        "progress_url": _GITHUB_PROGRESS_URL,
    }
    _append_event(_job_dir(job_id), "submitted_for_review", job["review"])
    return _save_job(job)


@app.get("/contributions/{job_id}/artifacts/PRD.md")
@app.get("/api/contributions/{job_id}/artifacts/PRD.md")
def get_contribution_prd(job_id: str):
    prd_path = _job_dir(job_id) / "PRD.md"
    if not prd_path.exists():
        raise HTTPException(404, "PRD 尚未生成")
    return PlainTextResponse(prd_path.read_text(encoding="utf-8"))


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
