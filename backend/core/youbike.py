# -*- coding: utf-8 -*-
"""
YouBike「接駁星」資料模組。

透過 TDX 運輸資料流通服務平台取得台南 YouBike 站點與即時車況，
為每個星座節點（餐廳）配對最近的一座接駁站。

設計重點：
  * 認證金鑰一律從環境變數讀取（TDX_CLIENT_ID / TDX_CLIENT_SECRET），絕不寫進程式碼。
  * 站點靜態資料長快取、即時車況短快取（60 秒），兼顧新鮮度與 API 負載。
  * 任何環節失敗（無金鑰 / 連線錯誤 / 無資料）都回傳空清單並記錄警告，
    絕不讓核心的星座路線生成功能崩潰（優雅降級）。
"""
import json
import logging
import os
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass

from core.constants import (
    YOUBIKE_AVAIL_TTL,
    YOUBIKE_CITY,
    YOUBIKE_RELAY_RADIUS_M,
    YOUBIKE_STATION_TTL,
)
from core.geo import haversine_m

logger = logging.getLogger("biteroute.youbike")

AUTH_URL = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
API_BASE = "https://tdx.transportdata.tw/api/basic"

# 模組層級快取：{ "value": ..., "exp": 過期的 epoch 秒數 }
_token_cache: dict = {"value": None, "exp": 0.0}
_stations_cache: dict = {"value": None, "exp": 0.0}
_avail_cache: dict = {"value": None, "exp": 0.0}


@dataclass
class RelayStar:
    """一座接駁站（YouBike 站點 + 即時車況）。"""
    station_uid: str
    name: str
    lat: float
    lng: float
    bikes: int            # 可借車輛數 (AvailableRentBikes)
    docks: int            # 可還空位數 (AvailableReturnBikes)
    capacity: int         # 總車位 (BikesCapacity)
    in_service: bool      # ServiceStatus == 1
    update_time: str      # 資料時間 (UpdateTime)


def _now() -> float:
    return time.time()


def _get_token() -> str | None:
    """取得 access token（含快取）。失敗回傳 None。"""
    if _token_cache["value"] and _token_cache["exp"] > _now():
        return _token_cache["value"]

    client_id = os.environ.get("TDX_CLIENT_ID")
    client_secret = os.environ.get("TDX_CLIENT_SECRET")
    if not client_id or not client_secret:
        logger.warning("未設定 TDX_CLIENT_ID / TDX_CLIENT_SECRET，停用 YouBike 接駁星功能。")
        return None

    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }).encode()
    req = urllib.request.Request(AUTH_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.load(resp)
    except Exception as exc:  # noqa: BLE001 - 任何錯誤都降級
        logger.warning("TDX 取得 token 失敗：%s", exc)
        return None

    token = payload.get("access_token")
    expires_in = float(payload.get("expires_in", 86400))
    if not token:
        logger.warning("TDX token 回應缺少 access_token。")
        return None

    # 提早 60 秒過期，避免邊界情況
    _token_cache.update(value=token, exp=_now() + max(0.0, expires_in - 60))
    return token


def _api_get(path: str, token: str) -> list | None:
    """呼叫 TDX API，回傳 list；失敗回傳 None。"""
    req = urllib.request.Request(f"{API_BASE}{path}", method="GET")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.load(resp)
    except Exception as exc:  # noqa: BLE001
        logger.warning("TDX API 請求失敗 %s：%s", path, exc)
        return None


def _fetch_stations() -> list[dict]:
    """站點靜態資料（長快取）。失敗回傳空清單。"""
    if _stations_cache["value"] is not None and _stations_cache["exp"] > _now():
        return _stations_cache["value"]

    token = _get_token()
    if token is None:
        return []

    data = _api_get(f"/v2/Bike/Station/City/{YOUBIKE_CITY}?$format=JSON", token)
    if data is None:
        return []

    _stations_cache.update(value=data, exp=_now() + YOUBIKE_STATION_TTL)
    return data


def _fetch_availability() -> dict[str, dict]:
    """即時車況（短快取），以 StationUID 為鍵。失敗回傳空 dict。"""
    if _avail_cache["value"] is not None and _avail_cache["exp"] > _now():
        return _avail_cache["value"]

    token = _get_token()
    if token is None:
        return {}

    data = _api_get(f"/v2/Bike/Availability/City/{YOUBIKE_CITY}?$format=JSON", token)
    if data is None:
        return {}

    indexed = {row["StationUID"]: row for row in data if "StationUID" in row}
    _avail_cache.update(value=indexed, exp=_now() + YOUBIKE_AVAIL_TTL)
    return indexed


def _merge() -> list[RelayStar]:
    """合併站點靜態資料與即時車況，產出 RelayStar 清單。"""
    stations = _fetch_stations()
    if not stations:
        return []
    avail = _fetch_availability()

    merged: list[RelayStar] = []
    for s in stations:
        uid = s.get("StationUID")
        pos = s.get("StationPosition", {})
        lat = pos.get("PositionLat")
        lng = pos.get("PositionLon")
        if uid is None or lat is None or lng is None:
            continue

        a = avail.get(uid, {})
        merged.append(RelayStar(
            station_uid=uid,
            name=s.get("StationName", {}).get("Zh_tw", "YouBike"),
            lat=float(lat),
            lng=float(lng),
            bikes=int(a.get("AvailableRentBikes", 0)),
            docks=int(a.get("AvailableReturnBikes", 0)),
            capacity=int(s.get("BikesCapacity", 0)),
            in_service=(a.get("ServiceStatus", 0) == 1),
            update_time=a.get("UpdateTime", s.get("UpdateTime", "")),
        ))
    return merged


def get_relay_stars(
    nodes: list[tuple[float, float]],
    radius_m: float = YOUBIKE_RELAY_RADIUS_M,
) -> list[RelayStar]:
    """
    為每個星座節點找出最近的一座接駁站。

    nodes: [(lat, lng), ...] 各餐廳節點座標
    回傳：去重後的 RelayStar 清單（多個節點共用同一站時只回傳一次）。
    任何失敗都回傳空清單（不拋例外）。
    """
    if not nodes:
        return []

    all_stars = _merge()
    if not all_stars:
        return []

    chosen: dict[str, RelayStar] = {}
    for nlat, nlng in nodes:
        best: RelayStar | None = None
        best_dist = float("inf")
        for star in all_stars:
            d = haversine_m(nlat, nlng, star.lat, star.lng)
            if d <= radius_m and d < best_dist:
                best, best_dist = star, d
        if best is not None:
            chosen[best.station_uid] = best

    return list(chosen.values())
