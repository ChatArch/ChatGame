"""牛牛谜题图像解析。

调用 ``chatgame.utils.image`` 完成通用的棋盘定位与格子采样，
在此之上做颜色聚类，输出每格的颜色 ID 矩阵。
"""

from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans

from chatgame.utils.image import (
    load_image,
    find_grid_bbox,
    sample_cells,
    estimate_grid_size_from_image,
)


# 牛牛系列截图的背景色（浅蓝）
_BG_COLOR: tuple[int, int, int] = (221, 248, 255)


def cluster_colors(samples: np.ndarray, n: int) -> np.ndarray:
    """对 N×N 采样颜色做 k-means 聚类，返回整数 ID 矩阵。

    ID 按颜色在矩阵中首次出现的顺序（左上→右下）分配，
    方便与棋盘可视化对照。

    Parameters
    ----------
    samples:
        shape ``(n, n, 3)`` uint8，每格中心 RGB。
    n:
        颜色数（= 棋盘边长）。

    Returns
    -------
    np.ndarray, shape ``(n, n)``, int
    """
    flat = samples.reshape(-1, 3).astype(float)
    km = KMeans(n_clusters=n, n_init=10, random_state=42)
    raw_labels = km.fit_predict(flat).reshape(n, n)

    # 重映射：首次出现顺序 → 稳定 ID
    mapping: dict[int, int] = {}
    next_id = 0
    for r in range(n):
        for c in range(n):
            old = int(raw_labels[r, c])
            if old not in mapping:
                mapping[old] = next_id
                next_id += 1
    return np.vectorize(mapping.__getitem__)(raw_labels)


def parse(
    image_path: str,
    n: int | None = None,
) -> tuple[np.ndarray, np.ndarray, tuple[int, int, int, int]]:
    """从截图中提取颜色 ID 矩阵。

    Parameters
    ----------
    image_path:
        游戏截图路径。
    n:
        棋盘边长。``None`` 时根据棋盘分隔线自动推断 6/8/10。

    Returns
    -------
    color_ids : np.ndarray, shape (n, n), int
        每格颜色 ID（0 ~ n-1）。
    samples : np.ndarray, shape (n, n, 3), uint8
        每格中心原始 RGB（供调试 / 标注）。
    bbox : (x0, y0, x1, y1)
        棋盘在原图中的像素包围盒。
    """
    arr = load_image(image_path)
    bbox = find_grid_bbox(arr, bg_color=_BG_COLOR)
    x0, y0, x1, y1 = bbox

    if n is None:
        n = estimate_grid_size_from_image(arr, bbox)

    samples = sample_cells(arr, x0, y0, x1, y1, n)
    color_ids = cluster_colors(samples, n)
    return color_ids, samples, bbox
