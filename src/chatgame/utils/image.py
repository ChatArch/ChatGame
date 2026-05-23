"""通用图像棋盘工具。

提供与具体游戏无关的功能：
- 在截图中定位矩形棋盘的像素包围盒
- 自动估算棋盘格数
- 按 N×N 等分采样每格中心像素

设计约定
--------
- 背景色（游戏界面底色）通过 `bg_color` 和 `bg_thresh` 参数传入，
  默认值适用于"牛牛谜题"系列截图。
- 棋盘被假设为近似正方形，上边界和水平边界先确定，
  再用宽度限制下边界搜索范围，避免被底部 UI 干扰。
"""

from __future__ import annotations

import numpy as np
from PIL import Image


# ── 默认背景色（浅蓝色游戏底色） ──────────────────────────────────────────────
DEFAULT_BG: tuple[int, int, int] = (221, 248, 255)
DEFAULT_BG_THRESH: float = 20.0
DEFAULT_DENSITY: float = 0.30       # 棋盘行/列至少含此比例的非背景像素
DEFAULT_SQUARE_MARGIN: float = 1.15  # 搜索下边界时允许的高宽比上限
DEFAULT_SUPPORTED_SIZES: tuple[int, ...] = (6, 8, 10)


def load_image(path: str) -> np.ndarray:
    """加载图像并返回 uint8 RGB 数组，shape (H, W, 3)。"""
    return np.array(Image.open(path).convert("RGB"))


def find_grid_bbox(
    arr: np.ndarray,
    bg_color: tuple[int, int, int] = DEFAULT_BG,
    bg_thresh: float = DEFAULT_BG_THRESH,
    density: float = DEFAULT_DENSITY,
    top_skip_fraction: float = 1 / 3,
    square_margin: float = DEFAULT_SQUARE_MARGIN,
) -> tuple[int, int, int, int]:
    """在图像中定位棋盘区域，返回 ``(x0, y0, x1, y1)``。

    算法
    ----
    1. 对每行/列计算"非背景像素密度"。
    2. 上边界：跳过顶部 ``top_skip_fraction`` 后，向下找首条高密度行。
    3. 水平边界（x0, x1）：全列密度扫描。
    4. 下边界：在 ``y0 + width * square_margin`` 范围内从下向上搜索，
       防止被底部 UI 元素误判。

    Parameters
    ----------
    arr:
        RGB 图像数组，shape ``(H, W, 3)``。
    bg_color:
        背景色 RGB，用于判断"是否为背景"。
    bg_thresh:
        与背景色的欧氏距离阈值，超过则视为非背景。
    density:
        行/列非背景像素比例阈值，≥此值视为棋盘区域。
    top_skip_fraction:
        跳过顶部该比例的行（避免把 UI 头部误判为上边界）。
    square_margin:
        允许棋盘高/宽比最大值，用于限制下边界搜索范围。
    """
    H, W = arr.shape[:2]
    bg = np.array(bg_color, dtype=float)

    def row_density(y: int) -> float:
        dists = np.linalg.norm(arr[y].astype(float) - bg, axis=1)
        return float((dists > bg_thresh).mean())

    def col_density(x: int) -> float:
        dists = np.linalg.norm(arr[:, x].astype(float) - bg, axis=1)
        return float((dists > bg_thresh).mean())

    # 水平边界
    x0 = 0
    for x in range(W):
        if col_density(x) >= density:
            x0 = x
            break

    x1 = W - 1
    for x in range(W - 1, -1, -1):
        if col_density(x) >= density:
            x1 = x
            break

    # 优先选择高度接近棋盘宽度的连续高密度行段。这样裁剪图不会因为
    # 固定跳过顶部比例而错过棋盘上沿。
    grid_width = x1 - x0
    row_vals = np.array([row_density(y) for y in range(H)])
    row_runs: list[tuple[int, int]] = []
    start: int | None = None
    for y, value in enumerate(row_vals):
        if value >= density and start is None:
            start = y
        elif value < density and start is not None:
            row_runs.append((start, y - 1))
            start = None
    if start is not None:
        row_runs.append((start, H - 1))

    min_height = grid_width / square_margin
    candidates = [
        (abs((end - start) - grid_width), start, end)
        for start, end in row_runs
        if (end - start) >= min_height
    ]
    if candidates:
        _, y0, y1 = min(candidates)
        return x0, y0, x1, y1

    # 兼容兜底：若没有稳定行段，回到原来的顶部跳过 + 正方形限制策略。
    y0 = int(H * top_skip_fraction)
    for y in range(int(H * top_skip_fraction), H):
        if row_density(y) >= density:
            y0 = y
            break

    y_max = min(H - 1, y0 + int(grid_width * square_margin))
    y1 = y0 + grid_width
    for y in range(y_max, y0, -1):
        if row_density(y) >= density:
            y1 = y
            break

    return x0, y0, x1, y1


def sample_cells(
    arr: np.ndarray,
    x0: int, y0: int, x1: int, y1: int,
    n: int,
) -> np.ndarray:
    """在 N×N 格子各自中心采样 RGB。

    Parameters
    ----------
    arr:
        RGB 图像数组。
    x0, y0, x1, y1:
        棋盘像素包围盒。
    n:
        棋盘边长（格数）。

    Returns
    -------
    np.ndarray, shape ``(n, n, 3)``, dtype uint8
    """
    cell_w = (x1 - x0) / n
    cell_h = (y1 - y0) / n
    out = np.zeros((n, n, 3), dtype=np.uint8)
    for r in range(n):
        for c in range(n):
            cx = int(x0 + (c + 0.5) * cell_w)
            cy = int(y0 + (r + 0.5) * cell_h)
            out[r, c] = arr[cy, cx]
    return out


def estimate_grid_size(x0: int, x1: int, cell_px: int = 50) -> int:
    """根据棋盘宽度和预估格子像素大小推断 N。"""
    return round((x1 - x0) / cell_px)


def estimate_grid_size_from_image(
    arr: np.ndarray,
    bbox: tuple[int, int, int, int],
    supported_sizes: tuple[int, ...] = DEFAULT_SUPPORTED_SIZES,
) -> int:
    """从棋盘图像中的分隔线/分隔缝推断 N。

    旧实现按固定像素宽度估算格子数，高分辨率 8x8 和 10x10 棋盘宽度
    接近时会误判。这里改为直接数棋盘内的连续色块条带：官方截图是白色
    分隔缝，内置示例图是深色网格线，二者都作为分隔区域处理。
    """
    x0, y0, x1, y1 = bbox
    crop = arr[y0 : y1 + 1, x0 : x1 + 1].astype(int)
    if crop.size == 0:
        raise ValueError("无法自动识别棋盘尺寸：棋盘区域为空")

    max_channel = crop.max(axis=2)
    min_channel = crop.min(axis=2)
    channel_range = max_channel - min_channel

    light_separator = (min_channel > 225) & (channel_range < 45)
    dark_separator = max_channel < 70
    cell_mask = ~(light_separator | dark_separator)

    def count_runs(densities: np.ndarray) -> int | None:
        if densities.size == 0:
            return None

        window = max(3, int(densities.size * 0.003))
        if window % 2 == 0:
            window += 1
        smoothed = np.convolve(densities, np.ones(window) / window, mode="same")

        low, high = np.percentile(smoothed, [10, 90])
        if high - low < 0.08:
            return None
        threshold = (low + high) / 2
        min_run = max(3, int(densities.size * 0.02))

        runs = 0
        start: int | None = None
        for idx, is_cell_band in enumerate(smoothed > threshold):
            if is_cell_band and start is None:
                start = idx
            elif not is_cell_band and start is not None:
                if idx - start >= min_run:
                    runs += 1
                start = None
        if start is not None and densities.size - start >= min_run:
            runs += 1
        return runs

    col_count = count_runs(cell_mask.mean(axis=0))
    row_count = count_runs(cell_mask.mean(axis=1))
    counts = [count for count in (row_count, col_count) if count in supported_sizes]

    if row_count == col_count and row_count in supported_sizes:
        return int(row_count)
    if len(counts) == 1:
        return int(counts[0])

    supported = " / ".join(str(size) for size in supported_sizes)
    raise ValueError(
        f"无法自动识别棋盘尺寸，请选择 {supported} 或上传更清晰截图"
    )
