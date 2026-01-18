"""
In-memory storage for GTM activities
This will be replaced with PostgreSQL database later
"""
from datetime import datetime
from typing import List, Optional, Dict
from dataclasses import dataclass, field, asdict

@dataclass
class GTMActivity:
    """GTM Activity data model"""
    id: int
    hypothesis: str
    audience: Optional[str] = None
    channels: Optional[str] = None
    description: Optional[str] = None
    list_size: Optional[int] = None
    meetings_booked: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    est_weekly_hrs: Optional[float] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class InMemoryStorage:
    """Simple in-memory storage for activities"""

    def __init__(self):
        self.activities: Dict[int, GTMActivity] = {}
        self.next_id = 1

    def create(self, hypothesis: str, audience: str = None, channels: str = None, **kwargs) -> GTMActivity:
        """Create a new activity"""
        activity = GTMActivity(
            id=self.next_id,
            hypothesis=hypothesis,
            audience=audience,
            channels=channels,
            **kwargs
        )
        self.activities[self.next_id] = activity
        self.next_id += 1
        return activity

    def get(self, activity_id: int) -> Optional[GTMActivity]:
        """Get an activity by ID"""
        return self.activities.get(activity_id)

    def list_all(self, limit: int = 10, filter_text: str = None) -> List[GTMActivity]:
        """List all activities with optional filter"""
        activities = list(self.activities.values())

        # Filter if text provided
        if filter_text:
            filter_lower = filter_text.lower()
            activities = [
                a for a in activities
                if (a.hypothesis and filter_lower in a.hypothesis.lower()) or
                   (a.audience and filter_lower in a.audience.lower()) or
                   (a.channels and filter_lower in a.channels.lower())
            ]

        # Sort by ID descending (newest first)
        activities.sort(key=lambda x: x.id, reverse=True)

        return activities[:limit]

    def update(self, activity_id: int, **kwargs) -> Optional[GTMActivity]:
        """Update an activity"""
        activity = self.activities.get(activity_id)
        if not activity:
            return None

        # Update fields
        for key, value in kwargs.items():
            if hasattr(activity, key) and value is not None:
                setattr(activity, key, value)

        activity.updated_at = datetime.utcnow().isoformat()
        return activity

    def delete(self, activity_id: int) -> bool:
        """Delete an activity"""
        if activity_id in self.activities:
            del self.activities[activity_id]
            return True
        return False


# Global storage instance
storage = InMemoryStorage()
