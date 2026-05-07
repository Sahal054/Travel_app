from sqlalchemy import ARRAY, Index, Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geography

from app.models.base import Base, TimestampMixin


class Place(Base, TimestampMixin):
    __tablename__ = "places"

    id: Mapped[int] = mapped_column(primary_key=True)
    google_place_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    place_name: Mapped[str] = mapped_column(String(255), nullable=False)
    formatted_address: Mapped[str | None] = mapped_column(String(512))
    city: Mapped[str | None] = mapped_column(String(128))
    region: Mapped[str | None] = mapped_column(String(128))
    # 0 = Free, 1 = Inexpensive, 2 = Moderate, 3 = Expensive, 4 = Very Expensive
    price_level: Mapped[int | None] = mapped_column(Integer)
    rating: Mapped[float | None] = mapped_column(Float)
    # E.g., ["cafe", "point_of_interest", "establishment"]
    place_types: Mapped[list[str] | None] = mapped_column(ARRAY(String))

    country: Mapped[str | None] = mapped_column(String(128))
    location: Mapped[object] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_places_location", "location", postgresql_using="gist"),
    )

    