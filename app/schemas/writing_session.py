from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class WritingSessionCreate(BaseModel):
    content: Optional[str] = None
    word_count: int = Field(..., ge=0)
    duration_minutes: Optional[int] = Field(None, ge=0)


class WritingSessionUpdate(BaseModel):
    content: Optional[str] = None
    word_count: Optional[int] = Field(None, ge=0)
    ended_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=0)


class WritingSessionPublish(BaseModel):
    newsletter_title: str = Field(..., min_length=1)


class WritingSessionResponse(BaseModel):
    id: int
    user_id: int
    word_count: int
    started_at: datetime
    ended_at: Optional[datetime]
    duration_minutes: Optional[int]
    session_date: datetime
    is_counted_for_streak: bool
    is_published: bool
    published_at: Optional[datetime]
    newsletter_title: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class WritingSessionStats(BaseModel):
    total_sessions: int
    total_words: int
    average_session_duration: Optional[float]
    sessions_this_week: int
    words_this_week: int
    most_productive_time: Optional[str]
    most_productive_day: Optional[str]
