# -*- coding: utf-8 -*-
import random

from fastapi import APIRouter, Request

from core.constants import SHAPE_MATRICES, SHAPE_ZH_NAMES, THEME_MAPPING, MIN_FILTERED
from core.geo import haversine_m, lat_lng_scales
from core.optimizer import build_kdtree, solve_template, optimize_path, TemplateResult
from core.renderer import build_map
from models.schemas import RouteRequest, RouteResponse, Assignment

router = APIRouter(prefix="/api/v1")


def _is_open_today(restaurant: dict, current_day: str) -> bool:
    if not current_day:
        return True
    opening_hours = restaurant.get("opening_hours", [])
    if not opening_hours:
        return True
    for day_str in opening_hours:
        if day_str.startswith(current_day):
            if "Closed" in day_str:
                return False
            return True
    return True


@router.post("/generate_route", response_model=RouteResponse)
def generate_route(req: RouteRequest, request: Request) -> RouteResponse:
    restaurants: list[dict] = request.app.state.restaurants
    tags = THEME_MAPPING.get(req.ui_theme, [])

    filtered = [
        r for r in restaurants
        if any(t in r.get("theme", []) for t in tags)
        and haversine_m(req.user_lat, req.user_lng, r["lat"], r["lng"]) <= req.search_radius_meters
        and _is_open_today(r, req.current_day)
    ]

    if len(filtered) < MIN_FILTERED:
        return RouteResponse(
            status="insufficient_restaurants",
            constellation_matched=None,
            matched_shape_name=None,
            total_price=0.0,
            map_html="",
        )

    lat_scale, lng_scale = lat_lng_scales(req.user_lat, req.search_radius_meters)
    tree, _ = build_kdtree(filtered)

    departure_minutes: int | None = None
    if req.current_time:
        try:
            h, m = req.current_time.split(":")
            departure_minutes = int(h) * 60 + int(m)
        except (ValueError, AttributeError):
            departure_minutes = None

    shape_names = list(SHAPE_MATRICES.keys())
    random.shuffle(shape_names)

    best: TemplateResult | None = None
    best_name: str | None = None

    for tname in shape_names:
        tpoints = SHAPE_MATRICES[tname]
        if len(tpoints) > len(filtered):
            continue

        result = solve_template(
            tpoints, filtered, tree,
            req.user_lat, req.user_lng,
            lat_scale, lng_scale,
            req.total_budget,
            departure_minutes,
        )

        if result.assignments is not None:
            best = result
            best_name = tname
            break

    if best is None or best.assignments is None:
        return RouteResponse(
            status="no_valid_route",
            constellation_matched=None,
            matched_shape_name=None,
            total_price=0.0,
            map_html="",
        )

    ordered = optimize_path(best.assignments)
    total_price = round(sum(c.price for c in ordered), 2)
    map_html = build_map(ordered, best_name)

    return RouteResponse(
        status="success",
        constellation_matched=best_name,
        matched_shape_name=SHAPE_ZH_NAMES.get(best_name, best_name),
        total_price=total_price,
        map_html=map_html,
        assignments=[Assignment(name=c.name, lat=c.lat, lng=c.lng) for c in ordered],
    )
