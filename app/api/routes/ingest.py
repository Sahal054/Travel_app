from fastapi import APIRouter, status

from app.schemas.ingest import IngestReelRequest, IngestReelResponse

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/reel", response_model=IngestReelResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_reel(payload: IngestReelRequest) -> IngestReelResponse:
    return IngestReelResponse(
        status="queued",
        message="Ingestion stub. Service wiring will be added next.",
        reel_url=payload.reel_url,
    )
