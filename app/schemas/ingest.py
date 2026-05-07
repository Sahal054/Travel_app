from pydantic import BaseModel, Field, HttpUrl


class IngestReelRequest(BaseModel):
    reel_url: HttpUrl = Field(..., description="Public reel URL")


class IngestReelResponse(BaseModel):
    status: str
    message: str
    reel_url: HttpUrl | None = None
