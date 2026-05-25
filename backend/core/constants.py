# -*- coding: utf-8 -*-
SHAPE_MATRICES: dict[str, list[tuple[float, float]]] = {
    "cassiopeia":      [(-0.90,  0.10), (-0.45,  0.75), ( 0.00,  0.15), ( 0.45,  0.75), ( 0.90,  0.10)],
    "aries":           [(-0.80,  0.80), ( 0.00,  0.20), ( 0.60, -0.50), ( 0.80, -0.80)],
    "triangulum":      [(-0.70, -0.40), ( 0.00,  0.75), ( 0.80, -0.25)],
    "cepheus":         [(-0.50, -0.55), (-0.50,  0.25), ( 0.00,  0.85), ( 0.50,  0.25), ( 0.50, -0.55)],
    "corvus":          [(-0.65, -0.50), (-0.30,  0.55), ( 0.30,  0.55), ( 0.65, -0.50)],
    "corona_borealis": [(-0.90,  0.00), (-0.73,  0.53), (-0.28,  0.86), ( 0.28,  0.86), ( 0.73,  0.53), ( 0.90,  0.00)],
    "scutum":          [( 0.00,  0.85), ( 0.60,  0.10), ( 0.00, -0.70), (-0.40,  0.25)],
    "norma":           [(-0.75,  0.65), (-0.75, -0.55), ( 0.75, -0.55)],
    "circinus":        [(-0.35,  0.75), ( 0.00, -0.65), ( 0.35,  0.75)],
}

SHAPE_ZH_NAMES: dict[str, str] = {
    "cassiopeia":      "仙后座",
    "aries":           "牡羊座",
    "triangulum":      "三角座",
    "cepheus":         "仙王座",
    "corvus":          "烏鴉座",
    "corona_borealis": "北冕座",
    "scutum":          "盾牌座",
    "norma":           "矩尺座",
    "circinus":        "圓規座",
}

CLOSED_SHAPES: list[str] = ["triangulum", "cepheus", "corvus", "scutum"]

THEME_MAPPING: dict[str, list[str]] = {
    "dessert_run":    ["dessert", "cafe"],
    "local_foodie":   ["local", "midnight"],
    "drunken_voyage": ["bar", "bistro"],
}

NEON_CYAN = "#00e5ff"

GLOW_LAYERS: list[tuple[int, float]] = [
    (16, 0.08),
    (10, 0.28),
    (5,  0.70),
    (2,  1.00),
]

MARKER_PALETTE: list[str] = [
    "#ffcc00",
    "#ff6b6b",
    "#a8ff78",
    "#78f1ff",
    "#ff78f1",
    "#f1ff78",
    "#78a8ff",
]

KNN_K         = 30
MIN_FILTERED  = 3
MAX_REVIEWS   = 14137
MO_WEIGHTS    = (0.20, 0.15, 0.15, 0.50)
DWELL_MINUTES = 45
