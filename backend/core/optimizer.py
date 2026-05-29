# -*- coding: utf-8 -*-
import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy.spatial import KDTree

from core.constants import KNN_K, MAX_REVIEWS, MO_WEIGHTS

BEAM_WIDTH = 50


@dataclass
class Candidate:
    id: int
    name: str
    lat: float
    lng: float
    price: float
    rating: float
    kdist: float
    user_ratings_total: int = 0
    opening_hours: list = field(default_factory=list)


@dataclass
class TemplateResult:
    score: float = field(default=-float("inf"))
    assignments: Optional[list[Candidate]] = field(default=None)


def build_kdtree(filtered: list[dict]) -> tuple[KDTree, np.ndarray]:
    coords = np.array([[r["lat"], r["lng"]] for r in filtered])
    return KDTree(coords), coords


def _candidates_for_node(vlat: float, vlng: float, filtered: list[dict], tree: KDTree, k: int) -> list[Candidate]:
    raw_dists, raw_idxs = tree.query([vlat, vlng], k=k)
    if k == 1:
        raw_dists, raw_idxs = [float(raw_dists)], [int(raw_idxs)]
    else:
        raw_dists, raw_idxs = raw_dists.tolist(), [int(i) for i in raw_idxs.tolist()]

    return [
        Candidate(
            id=filtered[i]["id"], name=filtered[i]["name"], lat=float(filtered[i]["lat"]),
            lng=float(filtered[i]["lng"]), price=float(filtered[i]["price"]),
            rating=float(filtered[i]["rating"]), kdist=float(d),
            user_ratings_total=int(filtered[i].get("user_ratings_total", 0)),
            opening_hours=filtered[i].get("opening_hours", []),
        )
        for d, i in zip(raw_dists, raw_idxs)
    ]


def _rotate_points(points: list[tuple[float, float]], angle_rad: float) -> list[tuple[float, float]]:
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    return [(x * cos_a - y * sin_a, x * sin_a + y * cos_a) for x, y in points]


def _mo_score(assignments: list[Candidate], target_budget: float, lat_scale: float, total_nodes: int) -> float:
    w_budget, w_rating, w_reviews, w_shape = MO_WEIGHTS
    n = len(assignments)
    if n == 0:
        return -float("inf")

    total_price = sum(c.price for c in assignments)
    expected_budget = target_budget * (n / total_nodes)

    u_budget = max(0.0, 1.0 - abs(total_price - expected_budget) / max(1.0, expected_budget))
    u_rating = sum(c.rating for c in assignments) / (5.0 * n)
    u_reviews = min(1.0, sum(math.log1p(c.user_ratings_total) for c in assignments) / (n * math.log1p(MAX_REVIEWS)))

    avg_kdist = sum(c.kdist for c in assignments) / max(1, n)
    u_shape = lat_scale / (lat_scale + avg_kdist)

    return w_budget * u_budget + w_rating * u_rating + w_reviews * u_reviews + w_shape * u_shape


def solve_template(
    tpoints: list[tuple[float, float]], filtered: list[dict], tree: KDTree,
    user_lat: float, user_lng: float, lat_scale: float, lng_scale: float,
    total_budget: float, departure_minutes: Optional[int] = None,
) -> TemplateResult:
    k = min(KNN_K, len(filtered))
    total_nodes = len(tpoints)
    best = TemplateResult()

    for angle in [0, math.pi / 2, math.pi, 3 * math.pi / 2]:
        rotated = _rotate_points(tpoints, angle)

        candidates_per_node = [
            _candidates_for_node(user_lat + pt[1] * lat_scale, user_lng + pt[0] * lng_scale, filtered, tree, k)
            for pt in rotated
        ]

        beam: list[tuple[list[Candidate], float]] = [([], 0.0)]

        for candidates in candidates_per_node:
            next_beam = []
            for path, current_cost in beam:
                used_ids = {c.id for c in path}
                for cand in candidates:
                    if cand.id in used_ids:
                        continue
                    new_cost = current_cost + cand.price
                    if new_cost > total_budget:
                        continue
                    new_path = path + [cand]
                    score = _mo_score(new_path, total_budget, lat_scale, total_nodes)
                    next_beam.append((new_path, new_cost, score))

            next_beam.sort(key=lambda x: x[2], reverse=True)
            beam = [(p, c) for p, c, _ in next_beam[:BEAM_WIDTH]]

            if not beam:
                break
        else:
            if beam:
                best_path = beam[0][0]
                final_score = _mo_score(best_path, total_budget, lat_scale, total_nodes)
                if final_score > best.score:
                    best = TemplateResult(score=final_score, assignments=best_path)

    return best


def optimize_path(candidates: list[Candidate]) -> list[Candidate]:
    return candidates
