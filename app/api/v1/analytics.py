from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.schemas.writing_session import WritingSessionCreate

import traceback
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/overview")
async def get_analytics_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive analytics overview."""
    try:
        logger.info(f"Getting analytics for user: {current_user.id}")
        performance_metrics = AnalyticsService.get_performance_metrics(db, current_user)

        return {
            "user": {
                "username": current_user.username,
                "email": current_user.email,
                "is_qualified": current_user.is_qualified or False,
                "total_words": current_user.total_words or 0,
                "current_streak": current_user.current_streak or 0,
                "longest_streak": current_user.longest_streak or 0,
                "total_sessions": current_user.total_sessions or 0
            },
            "performance": performance_metrics,
            "message": "Analytics overview retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error in analytics overview: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


# ✅ NEW: Daily Progress Endpoint
@router.get("/daily-progress")
async def get_daily_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get today's writing progress and sharing eligibility."""
    try:
        logger.info(f"Getting daily progress for user: {current_user.id}")

        # Check if we need to reset daily tracking
        today = date.today()

        # Reset if it's a new day
        if current_user.last_goal_check_date != today:
            logger.info(f"🔄 Resetting daily progress for user {current_user.id} (new day)")
            current_user.today_words = 0
            current_user.today_goal_met = False
            current_user.can_share_today = False
            current_user.last_goal_check_date = today
            db.commit()
            db.refresh(current_user)

        # Calculate progress
        daily_goal = current_user.daily_goal_words or 250
        today_words = current_user.today_words or 0
        progress_percent = min(100, int((today_words / daily_goal) * 100)) if daily_goal > 0 else 0

        # Check if goal is met
        goal_met = today_words >= daily_goal

        # Update goal status if just met
        if goal_met and not current_user.today_goal_met:
            logger.info(f"🎉 User {current_user.id} just met their daily goal!")
            current_user.today_goal_met = True
            current_user.can_share_today = True
            db.commit()
            db.refresh(current_user)

        response = {
            "today_words": today_words,
            "daily_goal": daily_goal,
            "goal_met": current_user.today_goal_met or False,
            "can_share": current_user.can_share_today or False,
            "progress_percent": progress_percent,
            "words_remaining": max(0, daily_goal - today_words),
            "last_check_date": current_user.last_goal_check_date.isoformat() if current_user.last_goal_check_date else None
        }

        logger.info(f"📊 Daily progress for user {current_user.id}: {response}")
        return response

    except Exception as e:
        logger.error(f"Error getting daily progress: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get daily progress: {str(e)}")


@router.get("/writing-patterns")
async def get_writing_patterns(
    days: int = Query(default=7, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed writing patterns analysis."""
    try:
        patterns = AnalyticsService.get_writing_patterns(db, current_user, days)
        return patterns
    except Exception as e:
        logger.error(f"Error in writing patterns: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get writing patterns: {str(e)}")


@router.get("/progress")
async def get_progress(
    days: int = Query(default=7, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's writing progress over time."""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import and_
        from app.models.writing_session import WritingSession

        logger.info(f"Getting progress for user: {current_user.id}, days: {days}")

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        sessions = db.query(WritingSession).filter(
            and_(
                WritingSession.user_id == current_user.id,
                WritingSession.created_at >= cutoff_date
            )
        ).order_by(WritingSession.created_at).all()

        # Group by date
        daily_progress = {}
        for session in sessions:
            date_key = session.created_at.date().isoformat()
            if date_key not in daily_progress:
                daily_progress[date_key] = {
                    "date": date_key,
                    "sessions": 0,
                    "words": 0,
                    "duration": 0
                }
            daily_progress[date_key]["sessions"] += 1
            daily_progress[date_key]["words"] += session.word_count
            daily_progress[date_key]["duration"] += session.duration_minutes or 0

        # Calculate cumulative totals
        cumulative_words = 0
        progress_data = []
        for date_key in sorted(daily_progress.keys()):
            data = daily_progress[date_key]
            cumulative_words += data["words"]
            progress_data.append({
                **data,
                "cumulative_words": cumulative_words
            })

        return {
            "days": days,
            "data": progress_data,
            "summary": {
                "total_sessions": sum(d["sessions"] for d in progress_data),
                "total_words": sum(d["words"] for d in progress_data),
                "total_duration": sum(d["duration"] for d in progress_data),
                "days_active": len(progress_data)
            }
        }

    except Exception as e:
        logger.error(f"Error getting progress: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch progress data: {str(e)}")


@router.get("/streak-history")
async def get_streak_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed streak history with breaks."""
    try:
        streak_history = AnalyticsService.get_streak_history(db, current_user)
        return {
            "current_streak": current_user.current_streak or 0,
            "longest_streak": current_user.longest_streak or 0,
            "history": streak_history
        }
    except Exception as e:
        logger.error(f"Error in streak history: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get streak history: {str(e)}")


@router.get("/word-count-trends")
async def get_word_count_trends(
    period: str = Query(default="week", pattern="^(week|month|year)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get word count trends over time."""
    try:
        trends = AnalyticsService.get_word_count_trends(db, current_user, period)
        return trends
    except Exception as e:
        logger.error(f"Error in word count trends: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get word count trends: {str(e)}")


@router.get("/performance")
async def get_performance_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive performance metrics."""
    try:
        metrics = AnalyticsService.get_performance_metrics(db, current_user)
        return metrics
    except Exception as e:
        logger.error(f"Error in performance metrics: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")


@router.get("/publishing-stats")
async def get_publishing_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get newsletter publishing statistics."""
    try:
        stats = AnalyticsService.get_publishing_stats(db, current_user)
        return stats
    except Exception as e:
        logger.error(f"Error in publishing stats: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get publishing stats: {str(e)}")


@router.get("/community-comparison")
async def compare_with_community(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compare user's stats with community averages."""
    try:
        comparison = AnalyticsService.compare_with_community(db, current_user)
        return comparison
    except Exception as e:
        logger.error(f"Error in community comparison: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get community comparison: {str(e)}")


@router.get("/dashboard")
async def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all analytics data for the dashboard."""
    try:
        return {
            "overview": AnalyticsService.get_performance_metrics(db, current_user),
            "patterns": AnalyticsService.get_writing_patterns(db, current_user, days=30),
            "trends": AnalyticsService.get_word_count_trends(db, current_user, period="week"),
            "publishing": AnalyticsService.get_publishing_stats(db, current_user),
            "community": AnalyticsService.compare_with_community(db, current_user)
        }
    except Exception as e:
        logger.error(f"Error in dashboard data: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")


@router.post("/session")
async def save_session_analytics(
    session_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save writing session analytics."""
    try:
        logger.info(f"Saving session analytics for user {current_user.id}: {session_data}")

        from app.models.writing_session import WritingSession

        # Create session record
        session = WritingSession(
            user_id=current_user.id,
            content="",
            word_count=session_data.get("word_count", 0),
            duration_minutes=session_data.get("duration_seconds", 0) // 60,
            session_type=session_data.get("session_type"),
            goal_met=session_data.get("goal_met", False),
            created_at=datetime.fromisoformat(session_data.get("started_at").replace('Z', '+00:00')) if session_data.get("started_at") else datetime.utcnow()
        )

        db.add(session)

        # Update user stats
        word_count = session_data.get("word_count", 0)
        current_user.total_words = (current_user.total_words or 0) + word_count
        current_user.total_sessions = (current_user.total_sessions or 0) + 1

        # ✅ NEW: Update today's word count for daily goal tracking
        today = date.today()
        if current_user.last_goal_check_date != today:
            # Reset if new day
            current_user.today_words = 0
            current_user.today_goal_met = False
            current_user.can_share_today = False
            current_user.last_goal_check_date = today

        # Add words to today's count
        current_user.today_words = (current_user.today_words or 0) + word_count

        # Check if daily goal met
        daily_goal = current_user.daily_goal_words or 250
        if current_user.today_words >= daily_goal and not current_user.today_goal_met:
            logger.info(f"🎉 User {current_user.id} just met their daily goal during session save!")
            current_user.today_goal_met = True
            current_user.can_share_today = True

        # Update last_write_date
        if current_user.last_write_date != today:
            current_user.last_write_date = today
            logger.info(f"✍️ Updated last_write_date for user {current_user.id} to {today}")

        db.commit()
        db.refresh(session)

        logger.info(f"✓ Session saved with ID: {session.id}")

        return {
            "success": True,
            "session_id": session.id,
            "today_words": current_user.today_words,
            "goal_met": current_user.today_goal_met,
            "can_share": current_user.can_share_today,
            "message": "Session analytics saved successfully"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error saving session: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to save session: {str(e)}")


@router.put("/session/{session_id}")
async def update_session(
    session_id: int,
    session_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update and finalize a writing session."""
    try:
        from app.models.writing_session import WritingSession

        logger.info(f"🔄 Updating session {session_id} for user {current_user.id}")
        logger.info(f"📊 Session data: {session_data}")

        session = db.query(WritingSession).filter(
            WritingSession.id == session_id,
            WritingSession.user_id == current_user.id
        ).first()

        if not session:
            logger.error(f"❌ Session {session_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Session not found")

        # Calculate word difference for today's count
        old_word_count = session.word_count
        new_word_count = session_data.get("final_word_count", session_data.get("word_count", 0))
        word_diff = new_word_count - old_word_count

        # Update session
        session.word_count = new_word_count
        session.duration_minutes = session_data.get("time_spent", 0) // 60
        session.goal_met = session_data.get("completed", False)

        metadata = {
            "avg_wpm": session_data.get("avg_wpm"),
            "peak_wpm": session_data.get("peak_wpm"),
            "pauses": session_data.get("pauses", 0),
            "edits": session_data.get("edits", 0),
            "updated_at": datetime.utcnow().isoformat()
        }

        if hasattr(session, 'session_metadata'):
            session.session_metadata = metadata

        # ✅ NEW: Update today's word count
        today = date.today()
        if current_user.last_goal_check_date != today:
            current_user.today_words = 0
            current_user.today_goal_met = False
            current_user.can_share_today = False
            current_user.last_goal_check_date = today

        current_user.today_words = (current_user.today_words or 0) + word_diff

        # Check if daily goal met
        daily_goal = current_user.daily_goal_words or 250
        if current_user.today_words >= daily_goal and not current_user.today_goal_met:
            logger.info(f"🎉 User {current_user.id} just met their daily goal during session update!")
            current_user.today_goal_met = True
            current_user.can_share_today = True

        # Update last_write_date
        if current_user.last_write_date != today:
            current_user.last_write_date = today
            logger.info(f"✍️ Updated last_write_date for user {current_user.id} to {today}")

        db.commit()
        db.refresh(session)

        logger.info(f"✅ Session {session_id} saved: {session.word_count} words, {session.duration_minutes} min")

        return {
            "success": True,
            "session_id": session.id,
            "final_word_count": session.word_count,
            "duration_minutes": session.duration_minutes,
            "goal_met": session.goal_met,
            "today_words": current_user.today_words,
            "daily_goal_met": current_user.today_goal_met,
            "can_share": current_user.can_share_today,
            "message": "Session updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to update session {session_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")
