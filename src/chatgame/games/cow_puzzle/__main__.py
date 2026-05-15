"""牛牛谜题端到端脚本。

用法：
    python -m chatgame.games.cow_puzzle <图片路径> [N]

N 为棋盘边长，省略时自动推断。
"""

from __future__ import annotations

import sys
import time

import numpy as np

from chatgame.games.cow_puzzle.parse import parse
from chatgame.games.cow_puzzle.solver import solve, verify


# ── 颜色名称（按 RGB 最近邻匹配） ────────────────────────────────────────────
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


def _print_board(
    color_ids: np.ndarray,
    solution: list[tuple[int, int]],
    n: int,
) -> None:
    """打印棋盘：放牛格显示点击顺序 [N]，其余显示色块 ID。"""
    ordered = sorted(enumerate(solution), key=lambda x: (x[1][0], x[1][1]))
    click_at: dict[tuple[int, int], int] = {
        (r, c): num for num, (_, (r, c)) in enumerate(ordered, 1)
    }
    print("     " + "   ".join(str(c) for c in range(n)))
    print("   +" + "───" * n + "+")
    for r in range(n):
        cells = []
        for c in range(n):
            if (r, c) in click_at:
                cells.append(f"[{click_at[(r, c)]}]")
            else:
                cells.append(f" {int(color_ids[r, c])} ")
        print(f" {r} │{''.join(cells)}│")
    print("   +" + "───" * n + "+")


def run(
    image_path: str,
    n: int | None = None,
    output: str | None = None,
    verbose: bool = False,
) -> None:
    sep = "=" * 56
    t0 = time.perf_counter()

    # ── 解析 ─────────────────────────────────────────────────
    color_ids, samples, bbox = parse(image_path, n=n)
    t1 = time.perf_counter()
    actual_n = color_ids.shape[0]
    x0, y0, x1, y1 = bbox

    color_names = [
        _color_name(samples[color_ids == cid][0].tolist())
        for cid in range(actual_n)
    ]

    if verbose:
        print(sep)
        print(f"棋盘区域: x=[{x0},{x1}]  y=[{y0},{y1}]  {actual_n}×{actual_n}")
        print(f"图像解析: {(t1 - t0) * 1000:.0f} ms\n")
        print("颜色 ID 映射:")
        for cid in range(actual_n):
            cnt = int((color_ids == cid).sum())
            rgb = samples[color_ids == cid][0].tolist()
            print(f"  {cid} = {color_names[cid]:<4}  {cnt:2d} 格  RGB≈{rgb}")
        print("\n颜色 ID 矩阵:")
        print("    " + "  ".join(str(c) for c in range(actual_n)))
        for r in range(actual_n):
            row = "  ".join(str(int(color_ids[r, c])) for c in range(actual_n))
            print(f"  {r}   {row}")
        print()

    # ── 求解 ─────────────────────────────────────────────────
    solution = solve(color_ids)
    t2 = time.perf_counter()

    if solution is None:
        print("❌ 无解！请检查图像或指定正确的 -n 值。")
        sys.exit(1)

    # ── 打印答案 ─────────────────────────────────────────────
    ordered = sorted(enumerate(solution), key=lambda x: (x[1][0], x[1][1]))
    print("解（按点击顺序）:")
    for click_num, (cid, (r, c)) in enumerate(ordered, 1):
        print(f"  第 {click_num} 步  行{r} 列{c}  {color_names[cid]}")

    print()
    _print_board(color_ids, solution, actual_n)

    errors = verify(color_ids, solution)
    print()
    if errors:
        print("⚠️  验证失败:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print(f"✓ 验证通过  ({(t2 - t0) * 1000:.0f} ms)")

    # ── 标注图（可选） ───────────────────────────────────────
    if output:
        _annotate(image_path, solution, bbox, actual_n, output)
        print(f"标注图已保存：{output}")


def _annotate(
    image_path: str,
    solution: list[tuple[int, int]],
    bbox: tuple[int, int, int, int],
    n: int,
    output_path: str,
) -> None:
    """在原图上叠加点击顺序编号，保存结果图。"""
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
            fill=(220, 50, 50),
            outline=(255, 255, 255),
            width=2,
        )
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                                      size=int(radius * 1.2))
        except OSError:
            font = ImageFont.load_default()
        text = str(click_num)
        bbox_t = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox_t[2] - bbox_t[0], bbox_t[3] - bbox_t[1]
        draw.text((cx - tw // 2, cy - th // 2), text, fill="white", font=font)

    img.save(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python -m chatgame.games.cow_puzzle <图片路径> [N]")
        sys.exit(1)
    image = sys.argv[1]
    size = int(sys.argv[2]) if len(sys.argv) > 2 else None
    run(image, n=size)
