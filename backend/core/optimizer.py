from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy.spatial import KDTree

from core.constants import KNN_K, DIST_PENALTY_COEFF


@dataclass
class Candidate:
    id: int
    name: str
    lat: float
    lng: float
    price: float
    rating: float
    kdist: float


@dataclass
class TemplateResult:
    score: float = field(default=-float("inf"))
    assignments: Optional[list[Candidate]] = field(default=None)


def build_kdtree(filtered: list[dict]) -> tuple[KDTree, np.ndarray]:
    coords = np.array([[r["lat"], r["lng"]] for r in filtered])
    return KDTree(coords), coords


def _candidates_for_node(
    vlat: float,
    vlng: float,
    filtered: list[dict],
    tree: KDTree,
    k: int,
) -> list[Candidate]:
    raw_dists, raw_idxs = tree.query([vlat, vlng], k=k)

    if k == 1:
        raw_dists = [float(raw_dists)]
        raw_idxs = [int(raw_idxs)]
    else:
        raw_dists = raw_dists.tolist()
        raw_idxs = [int(i) for i in raw_idxs.tolist()]

    return [
        Candidate(
            id=filtered[i]["id"],
            name=filtered[i]["name"],
            lat=float(filtered[i]["lat"]),
            lng=float(filtered[i]["lng"]),
            price=float(filtered[i]["price"]),
            rating=float(filtered[i]["rating"]),
            kdist=float(d),
        )
        for d, i in zip(raw_dists, raw_idxs)
    ]


def _backtrack(
    node_idx: int,
    budget_left: float,
    used_ids: set,
    assignments: list[Candidate],
    candidates_per_node: list[list[Candidate]],
    best: TemplateResult,
) -> None:
    if node_idx == len(candidates_per_node):
        score = (
            sum(c.rating for c in assignments)
            - DIST_PENALTY_COEFF * sum(c.kdist for c in assignments)
        )
        if score > best.score:
            best.score = score
            best.assignments = assignments[:]
        return

    for cand in candidates_per_node[node_idx]:
        if cand.id in used_ids or cand.price > budget_left:
            continue
        used_ids.add(cand.id)
        assignments.append(cand)
        _backtrack(node_idx + 1, budget_left - cand.price, used_ids, assignments, candidates_per_node, best)
        assignments.pop()
        used_ids.remove(cand.id)


def solve_template(
    tpoints: list[tuple[float, float]],
    filtered: list[dict],
    tree: KDTree,
    user_lat: float,
    user_lng: float,
    lat_scale: float,
    lng_scale: float,
    total_budget: float,
) -> TemplateResult:
    k = min(KNN_K, len(filtered))

    candidates_per_node: list[list[Candidate]] = [
        _candidates_for_node(
            user_lat + pt[1] * lat_scale,
            user_lng + pt[0] * lng_scale,
            filtered,
            tree,
            k,
        )
        for pt in tpoints
    ]

    result = TemplateResult()
    _backtrack(0, total_budget, set(), [], candidates_per_node, result)
    return result


def optimize_path(candidates: list[Candidate]) -> list[Candidate]:
    n = len(candidates)
    if n <= 3:
        return candidates[:]

    path = list(range(n))

    def _d(i: int, j: int) -> float:
        p, q = candidates[i], candidates[j]
        return ((p.lat - q.lat) ** 2 + (p.lng - q.lng) ** 2) ** 0.5

    improved = True
    while improved:
        improved = False
        for i in range(n - 1):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue
                a, b = path[i], path[i + 1]
                c, d = path[j], path[(j + 1) % n]
                if _d(a, c) + _d(b, d) < _d(a, b) + _d(c, d) - 1e-10:
                    path[i + 1 : j + 1] = path[i + 1 : j + 1][::-1]
                    improved = True

    return [candidates[i] for i in path]
