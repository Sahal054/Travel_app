import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.db.session import get_db_session
from app.models.itinerary import Itinerary
from app.schemas.itinerary import ItineraryRequest, ItineraryResponse
from app.services.itinerary_service import ItineraryService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/trips", tags=["trips"])


@router.post("/itinerary", response_model=ItineraryResponse)
async def create_itinerary(
    body: ItineraryRequest,
    db: AsyncSession = Depends(get_db_session),
    user_id: int | None = Depends(get_current_user_id),
) -> ItineraryResponse:
    try:
        service = ItineraryService()
        result = await service.generate(
            destination=body.destination,
            budget=body.budget,
            duration_days=body.duration_days,
        )
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.error("Itinerary generation failed", extra={"error": str(exc)})
        raise HTTPException(status_code=500, detail="Failed to generate itinerary")

    row = Itinerary(
        user_id=user_id,
        destination=body.destination,
        budget_level=body.budget,
        duration_days=body.duration_days,
        plan=result.model_dump(),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    result.itinerary_id = row.id
    return result
