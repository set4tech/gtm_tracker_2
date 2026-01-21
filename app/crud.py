from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import GTMActivity
from app.schemas import ActivityCreate, ActivityUpdate

def get_activities(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    hypothesis: Optional[str] = None,
    audience: Optional[str] = None,
    channels: Optional[str] = None
) -> List[GTMActivity]:
    """
    Get list of activities with optional filters.
    """
    query = db.query(GTMActivity)

    # Apply filters if provided
    if hypothesis:
        query = query.filter(GTMActivity.hypothesis.ilike(f"%{hypothesis}%"))
    if audience:
        query = query.filter(GTMActivity.audience.ilike(f"%{audience}%"))
    if channels:
        query = query.filter(GTMActivity.channels.ilike(f"%{channels}%"))

    return query.offset(skip).limit(limit).all()

def get_activity(db: Session, activity_id: int) -> Optional[GTMActivity]:
    """
    Get a single activity by ID.
    """
    return db.query(GTMActivity).filter(GTMActivity.id == activity_id).first()

def create_activity(db: Session, activity: ActivityCreate) -> GTMActivity:
    """
    Create a new activity.
    """
    db_activity = GTMActivity(**activity.model_dump())
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity

def update_activity(
    db: Session,
    activity_id: int,
    activity: ActivityUpdate,
    partial: bool = False
) -> Optional[GTMActivity]:
    """
    Update an existing activity.
    If partial=True, only update provided fields (PATCH).
    If partial=False, update all fields (PUT).
    """
    db_activity = get_activity(db, activity_id)
    if not db_activity:
        return None

    update_data = activity.model_dump(exclude_unset=partial)

    for field, value in update_data.items():
        setattr(db_activity, field, value)

    db.commit()
    db.refresh(db_activity)
    return db_activity

def delete_activity(db: Session, activity_id: int) -> bool:
    """
    Delete an activity by ID.
    Returns True if deleted, False if not found.
    """
    db_activity = get_activity(db, activity_id)
    if not db_activity:
        return False

    db.delete(db_activity)
    db.commit()
    return True

def count_activities(db: Session) -> int:
    """
    Count total number of activities in database.
    """
    return db.query(GTMActivity).count()
