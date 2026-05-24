SHAPE_MATRICES: dict[str, list[tuple[float, float]]] = {
    # --- original geometric shapes (kept for demo) ---
    "triangle": [(-0.8, -0.5), (0.0,  0.8), (0.8, -0.5), (-0.8, -0.5)],
    "square":   [(-0.5,  0.5), (0.5,  0.5), (0.5, -0.5), (-0.5, -0.5), (-0.5, 0.5)],
    "v_shape":  [(-0.6,  0.6), (0.0, -0.6), (0.6,  0.6)],
    "diamond":  [(0.0,   0.8), (0.5,  0.0), (0.0, -0.8), (-0.5,  0.0), (0.0,  0.8)],

    # --- real constellation coordinates (lng_offset, lat_offset) ---
    # Orion: Betelgeuse, Bellatrix → Mintaka, Alnilam, Alnitak (belt) → Saiph, Rigel
    "orion": [
        (-0.30,  0.85),
        ( 0.30,  0.78),
        (-0.14,  0.12),
        ( 0.00,  0.08),
        ( 0.14,  0.04),
        (-0.22, -0.72),
        ( 0.35, -0.82),
    ],
    # Big Dipper: Dubhe, Merak, Phekda, Megrez (bowl) → Alioth, Mizar, Alkaid (handle)
    "big_dipper": [
        (-0.72,  0.62),
        (-0.72,  0.22),
        (-0.30,  0.18),
        (-0.28,  0.58),
        ( 0.08,  0.72),
        ( 0.45,  0.62),
        ( 0.82, -0.08),
    ],
    # Southern Cross: Acrux, Mimosa, Gacrux, Imai, Ginan
    "southern_cross": [
        ( 0.00, -0.85),
        ( 0.70,  0.05),
        ( 0.00,  0.82),
        (-0.65,  0.00),
        ( 0.12, -0.18),
    ],
    # Cassiopeia W-shape: Segin, Ruchbah, Gamma Cas, Schedar, Caph
    "cassiopeia": [
        (-0.82,  0.45),
        (-0.38,  0.72),
        ( 0.00, -0.20),
        ( 0.40,  0.70),
        ( 0.80,  0.28),
    ],
    # Scorpius: Graffias, Dschubba, Antares, Tau Sco, Shaula, Lesath, Girtab
    "scorpius": [
        (-0.55,  0.82),
        (-0.20,  0.88),
        (-0.10,  0.50),
        ( 0.10,  0.10),
        ( 0.28, -0.30),
        ( 0.55, -0.62),
        ( 0.70, -0.85),
    ],
}

SHAPE_ZH_NAMES: dict[str, str] = {
    "triangle":       "三角",
    "square":         "正方",
    "v_shape":        "V形",
    "diamond":        "菱形",
    "orion":          "獵戶座",
    "big_dipper":     "北斗七星",
    "southern_cross": "南十字座",
    "cassiopeia":     "仙后座",
    "scorpius":       "天蠍座",
}

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

KNN_K         = 5
MIN_FILTERED  = 3
MAX_REVIEWS   = 14137   # actual max in restaurant.json; used to normalise U_reviews
MO_WEIGHTS    = (0.25, 0.30, 0.20, 0.25)   # w_budget, w_rating, w_reviews, w_shape
DWELL_MINUTES = 45      # estimated dwell time per restaurant stop (minutes)
