from enum import Enum as PyEnum

from sqlalchemy import Boolean, Enum, Float, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.models.base import Base, TimestampMixin


class ReelStatus(str, PyEnum):
    queued = "queued"
    processing = "processing"
    processed = "processed"
    failed = "failed"

class SavedReel(Base, TimestampMixin):
    __tablename__ = "saved_reels"
    __table_args__ = (
        UniqueConstraint("platform", "reel_url", name="uq_saved_reels_platform_reel_url"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    reel_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[ReelStatus] = mapped_column(
        Enum(ReelStatus, name="reel_status"),
        nullable=False,
        default=ReelStatus.queued,
    )
    title: Mapped[str | None] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)
    raw_metadata: Mapped[dict | None] = mapped_column(JSONB)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024))

    ai_confidence: Mapped[float | None] = mapped_column(Float)
    ai_reasoning: Mapped[str | None] = mapped_column(Text)
    ai_model_used: Mapped[str | None] = mapped_column(String(64))
    is_verified_truth: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
    )
    media_storage_path: Mapped[str | None] = mapped_column(String(1024))

    place_id: Mapped[int | None] = mapped_column(ForeignKey("places.id", ondelete="SET NULL"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    place = relationship("Place")
    user = relationship("User")
    