from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class RouteMode(str, Enum):
    quickest = "quickest"
    scenic = "scenic"


class TripPlanRequest(BaseModel):
    origin_lat: float = Field(..., ge=-90, le=90)
    origin_lng: float = Field(..., ge=-180, le=180)
    dest_lat: float = Field(..., ge=-90, le=90)
    dest_lng: float = Field(..., ge=-180, le=180)
    route_mode: RouteMode = RouteMode.scenic


class InjectedWaypoint(BaseModel):
    name: str
    lat: float
    lng: float
    poi_type: str


class TripPlanResponse(BaseModel):
    route_status: str
    injected_waypoints_count: int
    injected_poi_names: List[str]
    native_maps_url: str
    waypoints: List[InjectedWaypoint]
    cache_hit: bool
