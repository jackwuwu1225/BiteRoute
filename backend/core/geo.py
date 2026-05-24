import math


_EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2.0 * _EARTH_RADIUS_M * math.asin(math.sqrt(min(1.0, a)))


def lat_lng_scales(user_lat: float, radius_m: float) -> tuple[float, float]:
    lat_scale = radius_m / 111_320.0
    lng_scale = radius_m / (111_320.0 * math.cos(math.radians(user_lat)))
    return lat_scale, lng_scale
