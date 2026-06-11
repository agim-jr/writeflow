"""Pydantic schemas for AI coach endpoints."""
from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class PersonalityType(str, Enum):
    """Supported personality types for coaching messages."""
    DIRECT_CHALLENGING = "direct_challenging"
    GENTLE_ENCOURAGING = "gentle_encouraging"
    ANALYTICAL_FACTUAL = "analytical_factual"
    PLAYFUL_CASUAL = "playful_casual"
    COACH_MENTOR = "coach_mentor"


class RiskLevel(str, Enum):
    """Risk levels for streak loss."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CoachNudge(BaseModel):
    """Schema for coaching nudge response."""
    message: str = Field(..., description="The personalized coaching message")
    personality_type: PersonalityType = Field(..., description="Personality type used")
    risk_level: RiskLevel = Field(..., description="Current streak risk level")
    current_streak: int = Field(..., description="User's current streak")
    days_since_last_write: int = Field(..., description="Days since last write")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When nudge was generated")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Your 42-day streak is strong. Keep pushing.",
                "personality_type": "direct_challenging",
                "risk_level": "low",
                "current_streak": 42,
                "days_since_last_write": 0,
                "timestamp": "2026-05-22T10:30:00Z"
            }
        }


class CoachInsight(BaseModel):
    """Schema for AI coaching insights."""
    insight_type: Literal["streak_milestone", "writing_pattern", "motivation_boost", "risk_alert"]
    title: str = Field(..., description="Insight title")
    message: str = Field(..., description="Detailed insight message")
    priority: Literal["low", "medium", "high"] = Field(default="medium")
    actionable: bool = Field(default=True, description="Whether this insight has actionable steps")
    action_text: Optional[str] = Field(None, description="Suggested action if actionable")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "insight_type": "streak_milestone",
                "title": "Week Streak Achieved!",
                "message": "You've maintained consistency for 7 days. This is when habits start to solidify.",
                "priority": "medium",
                "actionable": True,
                "action_text": "Set a goal for the next 7 days to strengthen this habit.",
                "timestamp": "2026-05-22T10:30:00Z"
            }
        }


class NudgeRequest(BaseModel):
    """Optional request body for customizing nudges."""
    preferred_personality: Optional[PersonalityType] = Field(
        None,
        description="Override user's default personality preference"
    )
    force_generation: bool = Field(
        False,
        description="Force new message generation even if recently sent"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "preferred_personality": "gentle_encouraging",
                "force_generation": False
            }
        }


class PersonalityPreferenceUpdate(BaseModel):
    """Schema for updating user's personality preference."""
    personality_type: PersonalityType = Field(..., description="New personality preference")

    class Config:
        json_schema_extra = {
            "example": {
                "personality_type": "direct_challenging"
            }
        }


class InsightHistory(BaseModel):
    """Schema for historical insights response."""
    insights: list[CoachInsight] = Field(..., description="List of past insights")
    total_count: int = Field(..., description="Total number of insights")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(10, description="Number of items per page")

    class Config:
        json_schema_extra = {
            "example": {
                "insights": [
                    {
                        "insight_type": "streak_milestone",
                        "title": "Week Streak!",
                        "message": "7 days strong!",
                        "priority": "medium",
                        "actionable": True,
                        "action_text": "Keep going!",
                        "timestamp": "2026-05-22T10:30:00Z"
                    }
                ],
                "total_count": 15,
                "page": 1,
                "page_size": 10
            }
        }
