"""Milestones API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.writing_session import WritingSession
from pydantic import BaseModel, Field

router = APIRouter()


# Pydantic schemas
class Milestone(BaseModel):
    """Schema for a milestone achievement."""
    id: str
    title: str
    description: str
    icon: str
    achieved_at: Optional[datetime] = None
    is_achieved: bool
    progress: Optional[int] = None  # 0-100 percentage
    target: Optional[int] = None
    category: str  # "streak", "words", "sessions", "consistency"

    class Config:
        json_schema_extra = {
            "example": {
                "id": "streak_7",
                "title": "Week Warrior",
                "description": "Write for 7 days in a row",
                "icon": "🔥",
                "achieved_at": "2026-05-22T10:30:00Z",
                "is_achieved": True,
                "progress": 100,
                "target": 7,
                "category": "streak"
            }
        }


class MilestoneResponse(BaseModel):
    """Response containing user's milestones."""
    total_milestones: int
    achieved_count: int
    in_progress_count: int
    milestones: List[Milestone]


# Milestone definitions
MILESTONE_DEFINITIONS = [
    # Streak milestones
    {"id": "streak_3", "title": "Getting Started", "description": "Write for 3 days in a row", "icon": "🌱", "target": 3, "category": "streak"},
    {"id": "streak_7", "title": "Week Warrior", "description": "Write for 7 days in a row", "icon": "🔥", "target": 7, "category": "streak"},
    {"id": "streak_14", "title": "Two Week Wonder", "description": "Write for 14 days in a row", "icon": "⚡", "target": 14, "category": "streak"},
    {"id": "streak_30", "title": "Monthly Master", "description": "Write for 30 days in a row", "icon": "🏆", "target": 30, "category": "streak"},
    {"id": "streak_60", "title": "Consistency King", "description": "Write for 60 days in a row", "icon": "👑", "target": 60, "category": "streak"},
    {"id": "streak_100", "title": "Centurion", "description": "Write for 100 days in a row", "icon": "💯", "target": 100, "category": "streak"},

    # Word count milestones
    {"id": "words_1000", "title": "First Thousand", "description": "Write 1,000 total words", "icon": "📝", "target": 1000, "category": "words"},
    {"id": "words_10000", "title": "Ten Thousand Strong", "description": "Write 10,000 total words", "icon": "📚", "target": 10000, "category": "words"},
    {"id": "words_50000", "title": "Novelist", "description": "Write 50,000 total words", "icon": "📖", "target": 50000, "category": "words"},
    {"id": "words_100000", "title": "Author", "description": "Write 100,000 total words", "icon": "✍️", "target": 100000, "category": "words"},

    # Session milestones
    {"id": "sessions_10", "title": "Dedicated Writer", "description": "Complete 10 writing sessions", "icon": "⭐", "target": 10, "category": "sessions"},
    {"id": "sessions_50", "title": "Committed Creator", "description": "Complete 50 writing sessions", "icon": "🌟", "target": 50, "category": "sessions"},
    {"id": "sessions_100", "title": "Century Club", "description": "Complete 100 writing sessions", "icon": "💫", "target": 100, "category": "sessions"},
]


@router.get("/", response_model=MilestoneResponse)
async def get_user_milestones(
    db: Session = Depends(get_db),  # ✅ Fixed order - db first
    current_user: User = Depends(get_current_user)
):
    """
    Get all milestones for the current user with achievement status.

    Returns:
    - All available milestones
    - Which ones are achieved
    - Progress on in-progress milestones
    """

    # Get user stats
    total_sessions = db.query(func.count(WritingSession.id)).filter(
        WritingSession.user_id == current_user.id
    ).scalar() or 0

    total_words = db.query(func.sum(WritingSession.word_count)).filter(
        WritingSession.user_id == current_user.id
    ).scalar() or 0

    current_streak = current_user.current_streak or 0

    # Check each milestone
    milestones = []
    achieved_count = 0

    for milestone_def in MILESTONE_DEFINITIONS:
        is_achieved = False
        progress = 0
        achieved_at = None

        # Calculate progress based on category
        if milestone_def["category"] == "streak":
            current_value = current_streak
        elif milestone_def["category"] == "words":
            current_value = total_words
        elif milestone_def["category"] == "sessions":
            current_value = total_sessions
        else:
            current_value = 0

        target = milestone_def["target"]

        if current_value >= target:
            is_achieved = True
            progress = 100
            achieved_count += 1
            achieved_at = None
        else:
            progress = min(int((current_value / target) * 100), 99)

        milestone = Milestone(
            id=milestone_def["id"],
            title=milestone_def["title"],
            description=milestone_def["description"],
            icon=milestone_def["icon"],
            achieved_at=achieved_at,
            is_achieved=is_achieved,
            progress=progress,
            target=target,
            category=milestone_def["category"]
        )

        milestones.append(milestone)

    in_progress_count = len(milestones) - achieved_count

    return MilestoneResponse(
        total_milestones=len(milestones),
        achieved_count=achieved_count,
        in_progress_count=in_progress_count,
        milestones=milestones
    )


@router.get("/recent")
async def get_recent_milestones(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recently achieved milestones."""

    # Get all milestones
    response = await get_user_milestones(db, current_user)

    # Filter to only achieved milestones
    achieved = [m for m in response.milestones if m.is_achieved]

    # Sort by target (higher = more recent achievement)
    achieved.sort(key=lambda x: x.target or 0, reverse=True)

    return {
        "recent_milestones": achieved[:limit],
        "count": len(achieved)
    }


@router.get("/next")
async def get_next_milestone(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the next milestone the user is closest to achieving."""

    response = await get_user_milestones(db, current_user)

    # Filter to unachieved milestones
    unachieved = [m for m in response.milestones if not m.is_achieved]

    if not unachieved:
        return {
            "message": "You've achieved all milestones! 🎉",
            "next_milestone": None
        }

    # Sort by progress (highest progress = closest)
    unachieved.sort(key=lambda x: x.progress or 0, reverse=True)

    return {
        "next_milestone": unachieved[0],
        "total_remaining": len(unachieved)
    }
