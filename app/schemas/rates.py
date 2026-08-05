from pydantic import BaseModel


class OTARate(BaseModel):
    provider: str
    logo_slug: str
    price_per_night_inr: int
    currency: str = "INR"
    rating: float | None = None
    review_count: int | None = None
    deep_link: str
    is_best_deal: bool = False
    badge: str | None = None
