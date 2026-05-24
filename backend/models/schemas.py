from pydantic import BaseModel, Field
from typing import Optional


class RouteRequest(BaseModel):
    ui_theme: str = Field(..., examples=["dessert_run", "local_foodie", "drunken_voyage"])
    search_radius_meters: float = Field(..., gt=0)
    total_budget: float = Field(..., gt=0)
    user_lat: float = Field(..., ge=-90, le=90)
    user_lng: float = Field(..., ge=-180, le=180)


class RouteResponse(BaseModel):
    status: str
    constellation_matched: Optional[str]
    matched_shape_name: Optional[str]
    total_price: float
    map_html: str
