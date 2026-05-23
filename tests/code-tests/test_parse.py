"""单元测试：图像解析流程。"""

import numpy as np
import pytest

from conftest import IMG_8x8, IMG_10x10, IMG_10x10_32660, IMG_10x10_32660_CROP
from chatgame.games.cow_puzzle.parse import parse, cluster_colors
from chatgame.utils.image import (
    estimate_grid_size_from_image,
    find_grid_bbox,
    sample_cells,
    load_image,
)


# ── utils/image ───────────────────────────────────────────────────────────────

class TestFindGridBbox:
    def test_8x8_bbox_is_square(self):
        arr = load_image(str(IMG_8x8))
        x0, y0, x1, y1 = find_grid_bbox(arr)
        w, h = x1 - x0, y1 - y0
        # 棋盘应近似正方形（误差 < 15%）
        assert abs(w - h) / max(w, h) < 0.15

    def test_8x8_bbox_not_degenerate(self):
        arr = load_image(str(IMG_8x8))
        x0, y0, x1, y1 = find_grid_bbox(arr)
        assert x1 - x0 > 100
        assert y1 - y0 > 100

    def test_10x10_bbox_is_square(self):
        arr = load_image(str(IMG_10x10))
        x0, y0, x1, y1 = find_grid_bbox(arr)
        w, h = x1 - x0, y1 - y0
        assert abs(w - h) / max(w, h) < 0.15

    def test_auto_grid_size_counts_visual_cell_bands(self):
        cases = [
            (IMG_8x8, 8),
            (IMG_10x10_32660, 10),
            (IMG_10x10_32660_CROP, 10),
        ]

        for image_path, expected_n in cases:
            arr = load_image(str(image_path))
            bbox = find_grid_bbox(arr)
            assert estimate_grid_size_from_image(arr, bbox) == expected_n


class TestSampleCells:
    def test_output_shape(self):
        arr = load_image(str(IMG_8x8))
        x0, y0, x1, y1 = find_grid_bbox(arr)
        samples = sample_cells(arr, x0, y0, x1, y1, n=8)
        assert samples.shape == (8, 8, 3)
        assert samples.dtype == np.uint8

    def test_values_in_valid_range(self):
        arr = load_image(str(IMG_8x8))
        x0, y0, x1, y1 = find_grid_bbox(arr)
        samples = sample_cells(arr, x0, y0, x1, y1, n=8)
        assert samples.min() >= 0
        assert samples.max() <= 255


# ── cow_puzzle/parse ──────────────────────────────────────────────────────────

class TestClusterColors:
    def test_output_shape_and_range(self):
        arr = load_image(str(IMG_8x8))
        x0, y0, x1, y1 = find_grid_bbox(arr)
        samples = sample_cells(arr, x0, y0, x1, y1, n=8)
        ids = cluster_colors(samples, n=8)
        assert ids.shape == (8, 8)
        assert ids.min() == 0
        assert ids.max() == 7

    def test_each_color_appears_at_least_once(self):
        arr = load_image(str(IMG_8x8))
        x0, y0, x1, y1 = find_grid_bbox(arr)
        samples = sample_cells(arr, x0, y0, x1, y1, n=8)
        ids = cluster_colors(samples, n=8)
        for cid in range(8):
            assert (ids == cid).any(), f"颜色 {cid} 未出现"


class TestParse:
    def test_8x8_output_types(self):
        color_ids, samples, bbox = parse(str(IMG_8x8), n=8)
        assert color_ids.shape == (8, 8)
        assert samples.shape == (8, 8, 3)
        assert len(bbox) == 4

    def test_8x8_color_count(self):
        color_ids, _, _ = parse(str(IMG_8x8), n=8)
        assert set(color_ids.flatten()) == set(range(8))

    def test_10x10_color_count(self):
        color_ids, _, _ = parse(str(IMG_10x10), n=10)
        assert set(color_ids.flatten()) == set(range(10))

    def test_10x10_crop_matches_full_screenshot(self):
        full_ids, _, full_bbox = parse(str(IMG_10x10_32660), n=10)
        crop_ids, _, crop_bbox = parse(str(IMG_10x10_32660_CROP), n=10)

        assert full_bbox[1] < full_bbox[3]
        assert crop_bbox[1] < crop_bbox[3]
        assert np.array_equal(crop_ids, full_ids)

    def test_auto_detects_10x10_crop_size(self):
        color_ids, _, _ = parse(str(IMG_10x10_32660_CROP), n=None)

        assert color_ids.shape == (10, 10)

    def test_8x8_ids_are_sequential_from_top_left(self):
        """ID 按首次出现顺序分配，矩阵左上角必为 0。"""
        color_ids, _, _ = parse(str(IMG_8x8), n=8)
        assert color_ids[0, 0] == 0
