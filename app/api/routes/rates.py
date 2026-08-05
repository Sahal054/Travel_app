import logging
from typing import Annotated

from fastapi import APIRouter, Query

from app.schemas.rates import OTARate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/rates", tags=["rates"])

# Base multipliers by budget level
_LEVEL_MULT = {"backpacker": 0.4, "standard": 1.0, "luxury": 2.8}

def _make_rates(hotel_name: str, base_price: int, destination: str) -> list[OTARate]:
    """Return mock OTA rate data. In production, replace with real affiliate API calls."""
    providers = [
        dict(provider="Agoda",       logo_slug="agoda",     mult=1.00, badge="Best Price"),
        dict(provider="Booking.com", logo_slug="booking",   mult=1.07, badge=None),
        dict(provider="Expedia",     logo_slug="expedia",   mult=1.12, badge=None),
        dict(provider="MakeMyTrip",  logo_slug="makemytrip",mult=0.97, badge="Member Deal"),
        dict(provider="Goibibo",     logo_slug="goibibo",   mult=0.99, badge=None),
    ]
    rates = []
    best_idx = min(range(len(providers)), key=lambda i: providers[i]["mult"])
    for i, p in enumerate(providers):
        price = round(base_price * p["mult"] / 100) * 100
        dest_slug = destination.lower().replace(" ", "-")
        hotel_slug = hotel_name.lower().replace(" ", "-")
        deep_link = f"https://www.{p['logo_slug']}.com/search?q={hotel_slug}&destination={dest_slug}"
        rates.append(OTARate(
            provider=p["provider"],
            logo_slug=p["logo_slug"],
            price_per_night_inr=price,
            rating=round(3.8 + i * 0.15, 1),
            review_count=120 + i * 43,
            deep_link=deep_link,
            is_best_deal=(i == best_idx),
            badge=p["badge"],
        ))
    return rates


@router.get("/compare", response_model=list[OTARate])
async def compare_rates(
    hotel_name: Annotated[str, Query(min_length=1)],
    destination: Annotated[str, Query(min_length=1)],
    budget_level: Annotated[str, Query()] = "standard",
    base_price: Annotated[int, Query(gt=0)] = 3500,
) -> list[OTARate]:
    mult = _LEVEL_MULT.get(budget_level, 1.0)
    adjusted_base = int(base_price * mult)
    return _make_rates(hotel_name, adjusted_base, destination)
