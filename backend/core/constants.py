# all of the shape needs to be replaced.
SHAPE_MATRICES: dict[str, list[tuple[float, float]]] = {
    "triangle": [(-0.8, -0.5), (0.0,  0.8), (0.8, -0.5), (-0.8, -0.5)],
    "square":   [(-0.5,  0.5), (0.5,  0.5), (0.5, -0.5), (-0.5, -0.5), (-0.5, 0.5)],
    "line":     [(-0.7,  0.0), (0.0,  0.0), (0.7,  0.0)],
    "v_shape":  [(-0.6,  0.6), (0.0, -0.6), (0.6,  0.6)],
    "diamond":  [(0.0,   0.8), (0.5,  0.0), (0.0, -0.8), (-0.5,  0.0), (0.0,  0.8)],
}

SHAPE_ZH_NAMES: dict[str, str] = {
    "triangle": "三角",
    "square":   "正方",
    "line":     "直線",
    "v_shape":  "V形",
    "diamond":  "菱形",
}

THEME_MAPPING: dict[str, list[str]] = {
    "dessert_run":   ["dessert", "cafe"],
    "local_foodie":  ["local", "midnight"],
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

KNN_K             = 5
MIN_FILTERED      = 3
DIST_PENALTY_COEFF = 200.0
