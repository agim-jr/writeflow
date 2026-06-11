from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from app.models.user import SubscriptionTier


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    preferred_write_time: Optional[str] = None
    timezone: Optional[str] = None
    reminder_enabled: Optional[bool] = None


class UserProfile(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    is_qualified: bool
    qualification_date: Optional[datetime]
    subscription_tier: SubscriptionTier
    current_streak: int
    longest_streak: int
    total_words: int
    total_sessions: int
    newsletters_published: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserPublicProfile(BaseModel):
    id: int
    full_name: Optional[str]
    current_streak: int
    longest_streak: int
    total_words: int
    newsletters_published: int
    qualification_date: Optional[datetime]

    class Config:
        from_attributes = True


class UserStats(BaseModel):
    current_streak: int
    longest_streak: int
    total_words: int
    total_sessions: int
    newsletters_published: int
    last_write_date: Optional[datetime]
    preferred_write_time: Optional[str]
