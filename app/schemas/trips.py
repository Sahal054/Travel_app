from pydantic import BaseModel, Field
from typing import List


class TripPlanRequest(BaseModel):
    origin_lat: float = Field(..., ge=-90, le=90)
    origin_lng: float = Field(..., ge=-180, le=180)
    dest_lat: float = Field(..., ge=-90, le=90)
    dest_lng: float = Field(..., ge=-180, le=180)
    search_radius_meters: int = Field(default=2000, ge=100, le=50000)
    poi_type: str = Field(..., min_length=1, max_length=50)


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
