import folium
from branca.element import Element as BrancaElement

from core.constants import GLOW_LAYERS, MARKER_PALETTE, NEON_CYAN, SHAPE_ZH_NAMES
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
    _add_glow_polyline(m, chosen)

    return m._repr_html_()


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

        popup_html = (
            "<div style='font-family:system-ui,sans-serif;min-width:160px;padding:6px;'>"
            f"<b style='font-size:13px;'>{r.name}</b><br>"
            f"<span style='color:#888;font-size:11px;'>站點 #{idx + 1}</span><br>"
            f"<span style='color:#facc15;'>{stars}</span> "
            f"<span style='color:#888;font-size:11px;'>{r.rating}</span><br>"
            f"<span style='color:#00e5ff;'>&#36; {int(r.price)}</span>"
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
            popup=folium.Popup(popup_html, max_width=230),
            tooltip=f"#{idx + 1} {r.name}",
        ).add_to(m)


def _add_glow_polyline(m: folium.Map, chosen: list[Candidate]) -> None:
    route_coords = [[c.lat, c.lng] for c in chosen]
    route_coords.append(route_coords[0])

    for weight, opacity in GLOW_LAYERS:
        folium.PolyLine(
            route_coords,
            color=NEON_CYAN,
            weight=weight,
            opacity=opacity,
        ).add_to(m)
