from pydantic import BaseModel


class WaypointInput(BaseModel):
    lat: float
    lng: float
    name: str


class OptimizeRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    waypoints: list[WaypointInput]


class OptimizedRoute(BaseModel):
    optimized_order: list[int]
    ordered_waypoints: list[WaypointInput]
    encoded_polyline: str
    native_maps_url: str
