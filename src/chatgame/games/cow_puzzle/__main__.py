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


def run(image_path: str, n: int | None = None) -> None:
    sep = "=" * 56

    # ── Phase 1: 解析 ────────────────────────────────────────
    print(sep)
    print("Phase 1  图像解析")
    print(sep)
    t0 = time.perf_counter()
    color_ids, samples, bbox = parse(image_path, n=n)
    t1 = time.perf_counter()
    actual_n = color_ids.shape[0]
    x0, y0, x1, y1 = bbox
    print(f"棋盘区域: x=[{x0},{x1}]  y=[{y0},{y1}]  {actual_n}×{actual_n}")
    print(f"图像解析: {(t1 - t0) * 1000:.0f} ms\n")

    color_names = [
        _color_name(samples[color_ids == cid][0].tolist())
        for cid in range(actual_n)
    ]

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

    # ── Phase 2: 求解 ────────────────────────────────────────
    print(f"\n{sep}")
    print("Phase 2  CSP 求解")
    print(sep)
    t2 = time.perf_counter()
    solution = solve(color_ids)
    t3 = time.perf_counter()
    print(f"求解: {(t3 - t2) * 1000:.1f} ms")

    if solution is None:
        print("\n❌ 无解！请检查图像或指定正确的 N。")
        sys.exit(1)

    # ── Phase 3: 打印答案 ────────────────────────────────────
    print(f"\n{sep}")
    print("Phase 3  答案")
    print(sep)

    ordered = sorted(enumerate(solution), key=lambda x: (x[1][0], x[1][1]))
    print("\n解（按点击顺序，从上到下、从左到右）:")
    for click_num, (cid, (r, c)) in enumerate(ordered, 1):
        print(f"  第 {click_num} 步  行{r} 列{c}  颜色={color_names[cid]}({cid})")

    print("\n棋盘（[N]=第N步点击，数字=色块ID）:")
    _print_board(color_ids, solution, actual_n)

    errors = verify(color_ids, solution)
    print()
    if errors:
        print("⚠️  验证失败:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print("✓ 验证通过")
    print("  规则1 每色1头牛   ✓")
    print("  规则2 行列各唯一  ✓")
    print("  规则3 牛四周无牛  ✓")
    print(f"\n总耗时: {(t3 - t0) * 1000:.0f} ms")
    print(sep)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python -m chatgame.games.cow_puzzle <图片路径> [N]")
        sys.exit(1)
    image = sys.argv[1]
    size = int(sys.argv[2]) if len(sys.argv) > 2 else None
    run(image, n=size)
