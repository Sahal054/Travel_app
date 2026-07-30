from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RouteCache(Base):
    __tablename__ = "route_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    encoded_polyline: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_route_cache_route_hash", "route_hash", unique=True),
    )
