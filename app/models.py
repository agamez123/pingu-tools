from sqlalchemy import Column, DateTime, Integer, String, func

from app.database import Base


class Url(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True)
    short_code = Column(String(10), unique=True, nullable=False, index=True)
    original_url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
