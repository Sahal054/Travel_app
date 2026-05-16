from pydantic import BaseModel, Field, HttpUrl


class IngestReelRequest(BaseModel):
    reel_url: HttpUrl = Field(..., description="Public reel URL")

class PlaceSummary(BaseModel):
    place_name: str
    formatted_address: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    latitude: float
    longitude: float
    confidence: float


class IngestReelResponse(BaseModel):
    status: str
    message: str
    reel_url: HttpUrl | None = None
    saved_reel_id: int | None = None
    place_id: int | None = None
    place_summary: PlaceSummary | None = None
