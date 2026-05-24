import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy.spatial import KDTree

from core.constants import KNN_K, MAX_REVIEWS, MO_WEIGHTS, DWELL_MINUTES
from core.geo import haversine_m


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
            user_ratings_total=int(filtered[i].get("user_ratings_total", 0)),
            opening_hours=filtered[i].get("opening_hours", []),
        )
        for d, i in zip(raw_dists, raw_idxs)
    ]


def _parse_time(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _is_open(opening_hours: list, arrival_minutes: int) -> bool:
    if not opening_hours:
        return True
    for slot in opening_hours:
        open_str, close_str = slot.split("-")
        o = _parse_time(open_str)
        c = _parse_time(close_str)
        if o <= c:
            if o <= arrival_minutes <= c:
                return True
        else:
            # overnight wrap-around (e.g. 17:00-02:00)
            if arrival_minutes >= o or arrival_minutes <= c:
                return True
    return False


def _mo_score(
    assignments: list[Candidate],
    target_budget: float,
    lat_scale: float,
) -> float:
    w_budget, w_rating, w_reviews, w_shape = MO_WEIGHTS
    n = len(assignments)

    total_price = sum(c.price for c in assignments)
    u_budget = max(0.0, 1.0 - abs(total_price - target_budget) / max(1.0, target_budget))

    u_rating = sum(c.rating for c in assignments) / (5.0 * n)

    u_reviews = min(
        1.0,
        sum(math.log1p(c.user_ratings_total) for c in assignments)
        / (n * math.log1p(MAX_REVIEWS)),
    )

    max_kdist = lat_scale * math.sqrt(2.0)
    u_shape = max(0.0, 1.0 - (sum(c.kdist for c in assignments) / n) / max_kdist)

    return w_budget * u_budget + w_rating * u_rating + w_reviews * u_reviews + w_shape * u_shape


def _backtrack(
    node_idx: int,
    budget_left: float,
    target_budget: float,
    lat_scale: float,
    departure_seconds: Optional[float],
    cumulative_seconds: float,
    prev_lat: float,
    prev_lng: float,
    used_ids: set,
    assignments: list[Candidate],
    candidates_per_node: list[list[Candidate]],
    best: TemplateResult,
) -> None:
    if node_idx == len(candidates_per_node):
        score = _mo_score(assignments, target_budget, lat_scale)
        if score > best.score:
            best.score = score
            best.assignments = assignments[:]
        return

    dwell_sec = DWELL_MINUTES * 60.0

    for cand in candidates_per_node[node_idx]:
        if cand.id in used_ids or cand.price > budget_left:
            continue

        # Compute next cumulative time without mutating current scope
        next_cumulative_sec = cumulative_seconds
        if departure_seconds is not None:
            dist_m = haversine_m(prev_lat, prev_lng, cand.lat, cand.lng)
            walk_sec = dist_m / 1.1
            arrival_min = int((departure_seconds + cumulative_seconds + walk_sec) // 60) % 1440
            if not _is_open(cand.opening_hours, arrival_min):
                continue
            next_cumulative_sec += walk_sec + dwell_sec

        used_ids.add(cand.id)
        assignments.append(cand)
        _backtrack(
            node_idx + 1,
            budget_left - cand.price,
            target_budget,
            lat_scale,
            departure_seconds,
            next_cumulative_sec,
            cand.lat,
            cand.lng,
            used_ids,
            assignments,
            candidates_per_node,
            best,
        )
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
    departure_minutes: Optional[int] = None,
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

    departure_seconds = departure_minutes * 60.0 if departure_minutes is not None else None

    result = TemplateResult()
    _backtrack(
        0,
        total_budget,
        total_budget,
        lat_scale,
        departure_seconds,
        0.0,
        user_lat,
        user_lng,
        set(),
        [],
        candidates_per_node,
        result,
    )
    return result


def optimize_path(candidates: list[Candidate]) -> list[Candidate]:
    # Path order is hard-constrained to SHAPE_MATRICES drawing order.
    # Return as-is so the constellation shape is preserved on the map.
    return candidates
