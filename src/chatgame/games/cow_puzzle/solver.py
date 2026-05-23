"""牛牛谜题 CSP 求解器。

算法：回溯 + 前向检验（Forward Checking） + MRV 启发式排序。

约束：
- 每种颜色的牛必须在该颜色区域内
- 所有牛的行两两不同、列两两不同
- 任意两牛在 8 个方向上均不相邻（切比雪夫距离 > 1）
"""

from __future__ import annotations

from typing import Optional

import numpy as np


class SearchLimitExceeded(RuntimeError):
    """Raised when solution enumeration exceeds the configured search budget."""


# ── 内部辅助 ──────────────────────────────────────────────────────────────────

def _build_domains(color_ids: np.ndarray) -> list[list[tuple[int, int]]]:
    """为每种颜色建立候选格子列表（域）。"""
    n = color_ids.shape[0]
    domains: list[list[tuple[int, int]]] = [[] for _ in range(n)]
    for r in range(n):
        for c in range(n):
            domains[color_ids[r, c]].append((r, c))
    return domains


def _compatible(r1: int, c1: int, r2: int, c2: int) -> bool:
    """两头牛是否可共存（行列不同且 8 方向不相邻）。"""
    if r1 == r2 or c1 == c2:
        return False
    if abs(r1 - r2) <= 1 and abs(c1 - c2) <= 1:
        return False
    return True


def _forward_check(
    domains: list[list[tuple[int, int]]],
    color: int,
    r: int,
    c: int,
) -> tuple[bool, list[tuple[int, list[tuple[int, int]]]]]:
    """给颜色 color 分配 (r, c) 后，对未分配颜色做前向检验。

    Returns
    -------
    feasible : bool
        是否所有未分配颜色还有候选格。
    pruned : list of (color_id, removed_cells)
        被修剪的候选，用于回溯时恢复。
    """
    pruned: list[tuple[int, list[tuple[int, int]]]] = []
    for other, dom in enumerate(domains):
        if other == color:
            continue
        removed = [(rr, cc) for (rr, cc) in dom if not _compatible(r, c, rr, cc)]
        if removed:
            for pos in removed:
                dom.remove(pos)
            pruned.append((other, removed))
        if not dom:
            return False, pruned
    return True, pruned


def _restore(
    domains: list[list[tuple[int, int]]],
    pruned: list[tuple[int, list[tuple[int, int]]]],
) -> None:
    for color, removed in pruned:
        domains[color].extend(removed)


def _mrv_next(
    domains: list[list[tuple[int, int]]],
    assigned: set[int],
) -> int:
    """MRV：选候选数最少的未分配颜色。"""
    return min(
        (c for c in range(len(domains)) if c not in assigned),
        key=lambda c: len(domains[c]),
    )


def _backtrack(
    domains: list[list[tuple[int, int]]],
    assignment: list[Optional[tuple[int, int]]],
    assigned: set[int],
    used_rows: set[int],
    used_cols: set[int],
) -> bool:
    if len(assigned) == len(domains):
        return True

    color = _mrv_next(domains, assigned)

    for (r, c) in list(domains[color]):
        if r in used_rows or c in used_cols:
            continue
        if not all(
            _compatible(r, c, assignment[k][0], assignment[k][1])
            for k in assigned
        ):
            continue

        assignment[color] = (r, c)
        assigned.add(color)
        used_rows.add(r)
        used_cols.add(c)
        feasible, pruned = _forward_check(domains, color, r, c)

        if feasible and _backtrack(domains, assignment, assigned, used_rows, used_cols):
            return True

        _restore(domains, pruned)
        assignment[color] = None
        assigned.discard(color)
        used_rows.discard(r)
        used_cols.discard(c)

    return False


# ── 公开接口 ──────────────────────────────────────────────────────────────────

def solve(color_ids: np.ndarray) -> Optional[list[tuple[int, int]]]:
    """求解牛牛谜题。

    Parameters
    ----------
    color_ids : np.ndarray, shape (n, n)
        每格颜色 ID（0 ~ n-1）。

    Returns
    -------
    list of (row, col), length n
        第 i 项为颜色 i 的牛坐标；无解返回 ``None``。
    """
    n = color_ids.shape[0]
    domains = _build_domains(color_ids)
    assignment: list[Optional[tuple[int, int]]] = [None] * n
    if _backtrack(domains, assignment, set(), set(), set()):
        return assignment  # type: ignore[return-value]
    return None


def find_solutions(
    color_ids: np.ndarray,
    limit: int = 2,
    max_nodes: int | None = None,
) -> list[list[tuple[int, int]]]:
    """查找最多 ``limit`` 个解。

    ``limit=2`` 用于唯一性判断：找到第二个解即可停止，因为这已经证明
    该局面不是唯一解。返回 ``limit`` 个解表示“至少 limit 个解”，不表示
    精确只有这么多个解。``max_nodes`` 用于 API 侧防止异常输入触发过深搜索。
    """
    if limit < 1:
        return []

    n = color_ids.shape[0]
    domains = _build_domains(color_ids)
    for domain in domains:
        domain.sort()

    assignment: list[Optional[tuple[int, int]]] = [None] * n
    solutions: list[list[tuple[int, int]]] = []
    visited_nodes = 0

    def candidates_for(
        color: int,
        assigned: set[int],
        used_rows: set[int],
        used_cols: set[int],
    ) -> list[tuple[int, int]]:
        candidates: list[tuple[int, int]] = []
        for r, c in domains[color]:
            if r in used_rows or c in used_cols:
                continue
            if all(
                _compatible(r, c, assignment[k][0], assignment[k][1])
                for k in assigned
            ):
                candidates.append((r, c))
        return candidates

    def choose_color(
        assigned: set[int],
        used_rows: set[int],
        used_cols: set[int],
    ) -> tuple[int, list[tuple[int, int]]] | None:
        best_color: int | None = None
        best_candidates: list[tuple[int, int]] | None = None

        for color in range(n):
            if color in assigned:
                continue
            candidates = candidates_for(color, assigned, used_rows, used_cols)
            if not candidates:
                return None
            if best_candidates is None or len(candidates) < len(best_candidates):
                best_color = color
                best_candidates = candidates

        if best_color is None or best_candidates is None:
            return None
        return best_color, best_candidates

    def backtrack(
        assigned: set[int],
        used_rows: set[int],
        used_cols: set[int],
    ) -> None:
        nonlocal visited_nodes
        visited_nodes += 1
        if max_nodes is not None and visited_nodes > max_nodes:
            raise SearchLimitExceeded(f"search node limit exceeded: {max_nodes}")

        if len(solutions) >= limit:
            return
        if len(assigned) == n:
            solutions.append([pos for pos in assignment if pos is not None])
            return

        choice = choose_color(assigned, used_rows, used_cols)
        if choice is None:
            return
        color, candidates = choice

        for r, c in candidates:
            assignment[color] = (r, c)
            assigned.add(color)
            used_rows.add(r)
            used_cols.add(c)
            backtrack(assigned, used_rows, used_cols)
            used_cols.discard(c)
            used_rows.discard(r)
            assigned.discard(color)
            assignment[color] = None
            if len(solutions) >= limit:
                return

    backtrack(set(), set(), set())
    return solutions


def count_solutions(color_ids: np.ndarray, limit: int = 2) -> int:
    """计数最多 ``limit`` 个解，用于唯一解门禁。

    当 ``limit=2`` 时：
    - 返回 0 表示无解
    - 返回 1 表示唯一解
    - 返回 2 表示至少发现 2 个解，即非唯一解
    """
    return len(find_solutions(color_ids, limit=limit))


def verify(
    color_ids: np.ndarray,
    solution: list[tuple[int, int]],
) -> list[str]:
    """验证解的合法性。

    Returns
    -------
    list[str]
        错误描述列表；空列表表示合法。
    """
    n = color_ids.shape[0]
    errors: list[str] = []

    rows = [r for r, _ in solution]
    cols = [c for _, c in solution]

    if len(set(rows)) != n:
        errors.append(f"行重复: {sorted(rows)}")
    if len(set(cols)) != n:
        errors.append(f"列重复: {sorted(cols)}")

    for i, (r, c) in enumerate(solution):
        if color_ids[r, c] != i:
            errors.append(
                f"颜色 {i} 的牛放在了颜色 {color_ids[r, c]} 的格子 ({r},{c})"
            )
        for j, (r2, c2) in enumerate(solution):
            if i >= j:
                continue
            if abs(r - r2) <= 1 and abs(c - c2) <= 1:
                errors.append(
                    f"颜色 {i}({r},{c}) 与颜色 {j}({r2},{c2}) 相邻"
                )

    return errors
