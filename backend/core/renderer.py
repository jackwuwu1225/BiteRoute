# -*- coding: utf-8 -*-
import folium
from branca.element import Element as BrancaElement

from core.constants import (
    CLOSED_SHAPES,
    GLOW_LAYERS,
    MARKER_PALETTE,
    NEON_CYAN,
    SHAPE_ZH_NAMES,
    YOUBIKE_COLOR_FEW,
    YOUBIKE_COLOR_MANY,
    YOUBIKE_COLOR_NONE,
    YOUBIKE_THRESHOLD_FEW,
    YOUBIKE_THRESHOLD_MANY,
)
from core.optimizer import Candidate
from core.youbike import RelayStar


def build_map(
    chosen: list[Candidate],
    shape_name: str,
    relay_stars: list[RelayStar] | None = None,
) -> str:
    center_lat = sum(c.lat for c in chosen) / len(chosen)
    center_lng = sum(c.lng for c in chosen) / len(chosen)

    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=15,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    m.get_root().header.add_child(BrancaElement('<meta charset="UTF-8">'))

    zh_name = SHAPE_ZH_NAMES.get(shape_name, shape_name)
    _inject_overlay(m, zh_name)
    # 接駁星畫在主星之下，避免遮住星座主視覺
    if relay_stars:
        _add_relay_stars(m, relay_stars)
    _add_markers(m, chosen)
    _add_glow_polyline(m, chosen, shape_name)

    return m.get_root().render()


def _inject_overlay(m: folium.Map, zh_name: str) -> None:
    overlay_html = (
        "<div style='"
        "position:fixed;top:12px;left:12px;z-index:9999;"
        "background:rgba(5,5,16,0.84);"
        "border:1px solid rgba(0,229,255,0.38);"
        "border-radius:10px;padding:7px 14px;"
        "font-family:system-ui,-apple-system,sans-serif;"
        "font-size:13px;color:#fff;pointer-events:none;"
        "backdrop-filter:blur(8px);'>"
        f"當前圖形：<b style='color:#00e5ff;'>{zh_name}</b>"
        "</div>"
    )
    m.get_root().html.add_child(BrancaElement(overlay_html))


def _add_markers(m: folium.Map, chosen: list[Candidate]) -> None:
    for idx, r in enumerate(chosen):
        color = MARKER_PALETTE[idx % len(MARKER_PALETTE)]
        stars = "★" * round(r.rating) + "☆" * (5 - round(r.rating))
        maps_url = f"https://www.google.com/maps/search/?api=1&query={r.lat},{r.lng}"

        popup_html = (
            "<div style='font-family:system-ui,sans-serif;min-width:190px;padding:8px 10px;'>"
            f"<b style='font-size:14px;display:block;margin-bottom:5px;'>{r.name}</b>"
            "<div style='margin-bottom:8px;'>"
            f"<span style='color:#facc15;font-size:13px;'>{stars}</span>"
            f"<span style='color:#888;font-size:12px;margin-left:5px;'>{r.rating}</span>"
            "</div>"
            f"<a href='{maps_url}' target='_blank' rel='noopener' "
            "style='display:inline-block;padding:5px 12px;"
            "background:#00e5ff;color:#05050f;font-size:11px;font-weight:600;"
            "border-radius:6px;text-decoration:none;'>Open in Google Maps</a>"
            "</div>"
        )

        folium.CircleMarker(
            location=[r.lat, r.lng],
            radius=12,
            color="rgba(255,255,255,0.55)",
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f"#{idx + 1} {r.name}",
        ).add_to(m)


def _add_glow_polyline(m: folium.Map, chosen: list[Candidate], shape_name: str) -> None:
    coords = [[c.lat, c.lng] for c in chosen]
    draw_coords = coords + [coords[0]] if shape_name in CLOSED_SHAPES else coords

    for weight, opacity in GLOW_LAYERS:
        folium.PolyLine(
            draw_coords,
            color=NEON_CYAN,
            weight=weight,
            opacity=opacity,
        ).add_to(m)


def _relay_style(star: RelayStar) -> tuple[str, float]:
    """依可借車數決定接駁星的顏色與亮度（fill_opacity）。"""
    if not star.in_service or star.bikes <= 0:
        return YOUBIKE_COLOR_NONE, 0.40
    if star.bikes >= YOUBIKE_THRESHOLD_MANY:
        return YOUBIKE_COLOR_MANY, 0.95
    if star.bikes >= YOUBIKE_THRESHOLD_FEW:
        return YOUBIKE_COLOR_FEW, 0.70
    return YOUBIKE_COLOR_NONE, 0.40


def _add_relay_stars(m: folium.Map, relay_stars: list[RelayStar]) -> None:
    """把 YouBike 站點畫成依附在主星旁、較暗淡的小「接駁星」。"""
    for star in relay_stars:
        color, opacity = _relay_style(star)
        status_txt = "營運中" if star.in_service else "停駛"

        popup_html = (
            "<div style='font-family:system-ui,sans-serif;min-width:170px;padding:8px 10px;'>"
            f"<b style='font-size:13px;display:block;margin-bottom:4px;'>🚲 {star.name}</b>"
            "<div style='font-size:12px;line-height:1.6;'>"
            f"可借車輛：<b style='color:{color};'>{star.bikes}</b> 台<br>"
            f"可還空位：<b>{star.docks}</b> 位<br>"
            f"狀態：{status_txt}"
            "</div>"
            f"<div style='font-size:10px;color:#888;margin-top:5px;'>資料時間 {star.update_time}</div>"
            "</div>"
        )

        # 外層淡光暈，營造星點質感
        folium.CircleMarker(
            location=[star.lat, star.lng],
            radius=9,
            color=color,
            weight=0,
            fill=True,
            fill_color=color,
            fill_opacity=opacity * 0.25,
        ).add_to(m)
        # 內層實心小點
        folium.CircleMarker(
            location=[star.lat, star.lng],
            radius=4,
            color="rgba(255,255,255,0.6)",
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=opacity,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"🚲 {star.name}（可借 {star.bikes}）",
        ).add_to(m)
