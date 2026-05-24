import re
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class RouteRequest(BaseModel):
    ui_theme: str = Field(..., examples=["dessert_run", "local_foodie", "drunken_voyage"])
    search_radius_meters: float = Field(..., gt=0)
    total_budget: float = Field(..., gt=0)
    user_lat: float = Field(..., ge=-90, le=90)
    user_lng: float = Field(..., ge=-180, le=180)
    departure_time: Optional[str] = Field(
        default=None,
        description="Departure time in HH:MM (24h). If omitted, no time-window filtering.",
        examples=["19:30"],
    )

    @field_validator("departure_time")
    @classmethod
    def validate_time_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r"^\d{2}:\d{2}$", v):
            raise ValueError("departure_time must be HH:MM")
        return v


class RouteResponse(BaseModel):
    status: str
    constellation_matched: Optional[str]
    matched_shape_name: Optional[str]
    total_price: float
    map_html: str
