from sqlalchemy import Column, Integer, String, Text, Float, Date, DateTime
from sqlalchemy.sql import func
from app.database import Base

class GTMActivity(Base):
    """
    SQLAlchemy model for GTM activities.
    """
    __tablename__ = "gtm_activities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hypothesis = Column(String, nullable=False)
    audience = Column(String, nullable=True)
    channels = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    list_size = Column(Integer, nullable=True)
    meetings_booked = Column(Integer, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    est_weekly_hrs = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<GTMActivity(id={self.id}, hypothesis='{self.hypothesis}')>"
