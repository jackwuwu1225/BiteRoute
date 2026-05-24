from fastapi import APIRouter, Request

from core.constants import SHAPE_MATRICES, SHAPE_ZH_NAMES, THEME_MAPPING, MIN_FILTERED
from core.geo import haversine_m, lat_lng_scales
from core.optimizer import build_kdtree, solve_template, optimize_path, TemplateResult
from core.renderer import build_map
from models.schemas import RouteRequest, RouteResponse

router = APIRouter(prefix="/api/v1")


def _open_points(tpoints: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if len(tpoints) > 1 and tpoints[0] == tpoints[-1]:
        return list(tpoints[:-1])
    return list(tpoints)


@router.post("/generate_route", response_model=RouteResponse)
def generate_route(req: RouteRequest, request: Request) -> RouteResponse:
    restaurants: list[dict] = request.app.state.restaurants
    tags = THEME_MAPPING.get(req.ui_theme, [])

    filtered = [
        r for r in restaurants
        if any(t in r.get("theme", []) for t in tags)
        and haversine_m(req.user_lat, req.user_lng, r["lat"], r["lng"]) <= req.search_radius_meters
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

    best: TemplateResult | None = None
    best_name: str | None = None

    for tname, tpoints in SHAPE_MATRICES.items():
        open_pts = _open_points(tpoints)
        if len(open_pts) > len(filtered):
            continue

        result = solve_template(
            open_pts, filtered, tree,
            req.user_lat, req.user_lng,
            lat_scale, lng_scale,
            req.total_budget,
        )

        if result.assignments is not None and (best is None or result.score > best.score):
            best = result
            best_name = tname

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
    )
