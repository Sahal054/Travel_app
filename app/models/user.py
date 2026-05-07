from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin



class User( Base,TimestampMixin):
    __tablename__ = "users"

    id:Mapped[int] = mapped_column(primary_key= True)