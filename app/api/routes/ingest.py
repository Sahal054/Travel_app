from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.db.session import get_db_session
from app.repositories.sqlalchemy_repositories import (
    SqlAlchemyPlaceRepository,
    SqlAlchemySavedReelRepository,
)
from app.schemas.ingest import IngestReelRequest, IngestReelResponse, PlaceSummary
from app.services.ingestion_service import IngestionService, IngestionValidationError

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post(
    "/reel",
    response_model=IngestReelResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_reel(
    payload: IngestReelRequest,
    db: AsyncSession = Depends(get_db_session),
) -> IngestReelResponse:
    service = IngestionService(
        place_repo=SqlAlchemyPlaceRepository(db),
        saved_reel_repo=SqlAlchemySavedReelRepository(db),
    )

    try:
        result = await service.ingest_reel(reel_url=str(payload.reel_url))
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Upstream API failure") from exc
    except (IngestionValidationError, ValidationError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error") from exc

    place_summary = PlaceSummary(
        place_name=result.verified_place.place_name,
        formatted_address=result.verified_place.formatted_address,
        city=result.verified_place.city,
        region=result.verified_place.region,
        country=result.verified_place.country,
        latitude=result.verified_place.latitude,
        longitude=result.verified_place.longitude,
        confidence=result.verified_place.score,
    )

    return IngestReelResponse(
        status="accepted",
        message="Ingestion completed",
        reel_url=payload.reel_url,
        saved_reel_id=result.saved_reel_id,
        place_id=result.place_id,
        place_summary=place_summary,
    )