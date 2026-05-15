"""Regression tests for the web cow-puzzle levels and solver examples."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from chatgame.games.cow_puzzle.parse import parse
from chatgame.games.cow_puzzle.solver import solve, verify


ROOT = Path(__file__).resolve().parents[2]
LEVELS_PATH = ROOT / "web" / "src" / "games" / "cowPuzzleLevels.json"
EXAMPLES_DIR = ROOT / "web" / "public" / "examples"


def _levels() -> list[dict]:
    return json.loads(LEVELS_PATH.read_text(encoding="utf-8"))["levels"]


def test_builtin_web_levels_are_solver_verified():
    for level in _levels():
        color_ids = np.array(level["grid"], dtype=int)
        expected = [tuple(point) for point in level["solution"]]

        assert verify(color_ids, expected) == []
        solution = solve(color_ids)
        assert solution is not None
        assert verify(color_ids, solution) == []


def test_example_images_remain_parseable_and_solvable():
    for level in _levels():
        image_path = EXAMPLES_DIR / f"cow-puzzle-{level['size']}.png"

        color_ids, _samples, _bbox = parse(str(image_path), n=level["size"])
        solution = solve(color_ids)

        assert solution is not None
        assert verify(color_ids, solution) == []
