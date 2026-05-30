# -*- coding: utf-8 -*-
import folium
from branca.element import Element as BrancaElement

from core.constants import CLOSED_SHAPES, GLOW_LAYERS, MARKER_PALETTE, NEON_CYAN, SHAPE_ZH_NAMES
from core.optimizer import Candidate


def build_map(chosen: list[Candidate], shape_name: str) -> str:
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
