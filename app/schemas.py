from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime

class ActivityBase(BaseModel):
    """Base schema with common fields"""
    hypothesis: str
    audience: Optional[str] = None
    channels: Optional[str] = None
    description: Optional[str] = None
    list_size: Optional[int] = None
    meetings_booked: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    est_weekly_hrs: Optional[float] = None

class ActivityCreate(ActivityBase):
    """Schema for creating new activities"""
    pass

class ActivityUpdate(BaseModel):
    """Schema for updating activities - all fields optional for PATCH"""
    hypothesis: Optional[str] = None
    audience: Optional[str] = None
    channels: Optional[str] = None
    description: Optional[str] = None
    list_size: Optional[int] = None
    meetings_booked: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    est_weekly_hrs: Optional[float] = None

class ActivityResponse(ActivityBase):
    """Schema for API responses"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
