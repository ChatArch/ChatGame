"""chatgame FastAPI 后端。

端点：
  POST /solve              上传截图，返回解坐标 + 标注图（base64）+ 颜色矩阵
  GET  /games              已支持游戏列表
  GET  /games/{id}/docs    游戏规则 / 攻略 Markdown
"""

from __future__ import annotations

import base64
import io
import os
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image

from chatgame.web.paths import has_static_assets, package_static_dir

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

@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/games")
@app.get("/api/games")
def list_games():
    return {"games": list(_GAMES.values())}


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
    image: UploadFile = File(...),
    game: str = Form("cow-puzzle"),
    n: int | None = Form(None),
):
    if game not in _GAMES:
        raise HTTPException(400, f"未知游戏 {game!r}")
    if n is not None and n <= 0:
        raise HTTPException(400, "棋盘边长必须为正整数")

    # 读取图像
    image.file.seek(0)
    raw = image.file.read()
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
        from chatgame.games.cow_puzzle.solver import find_solutions, verify

        try:
            color_ids, samples, bbox = parse(tmp_path, n=n)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        actual_n = color_ids.shape[0]

        solutions = find_solutions(color_ids, limit=2)
        elapsed = round((time.perf_counter() - t0) * 1000)

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
