from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.milestone import MilestoneType


class MilestoneCreate(BaseModel):
    milestone_type: MilestoneType
    milestone_value: int
    title: str
    description: Optional[str] = None


class MilestoneResponse(BaseModel):
    id: int
    user_id: int
    milestone_type: MilestoneType
    milestone_value: int
    title: str
    description: Optional[str]
    achieved_at: datetime
    is_posted_to_feed: bool

    class Config:
        from_attributes = True


class MilestoneFeedItem(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str]
    milestone_type: MilestoneType
    milestone_value: int
    title: str
    description: Optional[str]
    achieved_at: datetime

    class Config:
        from_attributes = True
