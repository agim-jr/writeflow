# app/routers/ai_coach.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, date
from pydantic import BaseModel
import logging
import traceback

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.writing_session import WritingSession
from app.schemas.ai_coach import (
    CoachNudge,
    CoachInsight,
    PersonalityType,
    RiskLevel,
    NudgeRequest,
    PersonalityPreferenceUpdate
)
from app.services.ml_integration_service import MLIntegrationService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize ML Integration Service (now using rule-based coach)
try:
    ml_service = MLIntegrationService()
    logger.info("ML Integration Service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize ML service: {str(e)}")
    logger.error(traceback.format_exc())
    ml_service = None


# Request model for /message endpoint
class CoachMessageRequest(BaseModel):
    context: str
    milestone: Optional[int] = None
    word_count: Optional[int] = None
    time_elapsed: Optional[int] = None
    session_type: Optional[str] = None
    inactivity_duration: Optional[int] = None
    recent_text: Optional[str] = None


def get_days_since_last_write(user: User) -> int:
    """Helper function to safely calculate days since last write"""
    if not user.last_write_date:
        return 999

    # Handle both date and datetime objects
    if isinstance(user.last_write_date, datetime):
        last_write = user.last_write_date.date()
    else:
        last_write = user.last_write_date

    return (datetime.utcnow().date() - last_write).days


@router.post("/message", response_model=CoachNudge)
async def get_coaching_message(
    request: CoachMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate AI coaching message for real-time session feedback.
    Called by frontend during active writing sessions.
    """
    try:
        logger.info(f"=== Coach Message Request from user {current_user.id} ===")
        logger.info(f"Request data: {request.dict()}")

        if ml_service is None:
            raise HTTPException(status_code=503, detail="ML service not available")

        # Build context for AI
        ai_context = {
            'context_type': request.context,
            'current_streak': current_user.current_streak,
            'longest_streak': current_user.longest_streak,
            'milestone': request.milestone,
            'word_count': request.word_count,
            'time_elapsed': request.time_elapsed,
            'session_type': request.session_type,
            'inactivity_duration': request.inactivity_duration
        }

        logger.info(f"AI Context: {ai_context}")

        # Generate message using rule-based system
        logger.info("Calling ML service generate_coaching_message...")
        result = ml_service.generate_coaching_message(
            db=db,
            user=current_user,
            context=ai_context
        )
        logger.info(f"ML service result: {result}")

        # Get risk level from result
        risk_level = result['streak_risk']['risk_level']

        # Calculate days since last write (FIXED)
        days_since = get_days_since_last_write(current_user)

        response = CoachNudge(
            message=result['message'],
            personality_type=result['personality'],
            risk_level=risk_level,
            current_streak=current_user.current_streak,
            days_since_last_write=days_since,
            timestamp=datetime.utcnow()
        )

        logger.info(f"Returning response: {response}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ERROR in get_coaching_message: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"AI Coach error: {str(e)}")


@router.get("/nudge", response_model=CoachNudge)
async def get_coach_nudge(
    request: Optional[NudgeRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a personalized AI-generated coaching nudge.
    For reminders, check-ins, and motivation outside active sessions.
    """
    try:
        if ml_service is None:
            raise HTTPException(status_code=503, detail="ML service not available")

        # Calculate days since last write (FIXED)
        days_since = get_days_since_last_write(current_user)

        # Build context
        context = {
            'context_type': 'check_in',
            'current_streak': current_user.current_streak,
            'days_since_last_write': days_since,
        }

        # Override personality if requested
        if request and request.preferred_personality:
            context['preferred_personality'] = request.preferred_personality

        # Generate message using rule-based system
        result = ml_service.generate_coaching_message(db, current_user, context)

        return CoachNudge(
            message=result['message'],
            personality_type=result['personality'],
            risk_level=result['streak_risk']['risk_level'],
            current_streak=current_user.current_streak,
            days_since_last_write=days_since,
            timestamp=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ERROR in get_coach_nudge: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights", response_model=List[CoachInsight])
async def get_coach_insights(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get AI-powered insights about writing patterns.
    Uses rule-based analysis to detect patterns, risks, and opportunities.
    """
    try:
        if ml_service is None:
            raise HTTPException(status_code=503, detail="ML service not available")

        # Get complete analysis
        ml_insights = ml_service.get_complete_insights(db, current_user)

        insights = []

        # 1. Streak Risk Insight
        streak_risk = ml_insights['streak_risk']

        # Calculate hours remaining (if applicable) (FIXED)
        hours_remaining = None
        if current_user.last_write_date:
            days_since = get_days_since_last_write(current_user)
            hours_since = days_since * 24
            hours_remaining = max(0, 24 - hours_since)

        if streak_risk['risk_level'] == 'high':
            hours_text = f"{hours_remaining} hours" if hours_remaining is not None else "a few hours"
            insights.append(CoachInsight(
                insight_type="risk_alert",
                title="⚠️ Streak at Risk",
                message=f"Your {current_user.current_streak}-day streak is in danger. Write within {hours_text}.",
                priority="high",
                actionable=True,
                action_text="Start a quick 5-minute session now"
            ))
        elif streak_risk['risk_level'] == 'medium':
            insights.append(CoachInsight(
                insight_type="risk_alert",
                title="⏰ Streak Check-in",
                message=f"Your {current_user.current_streak}-day streak needs attention today.",
                priority="medium",
                actionable=True,
                action_text="Schedule 15 minutes to write"
            ))

        # 2. Burnout Analysis
        burnout = ml_insights['burnout_analysis']
        if burnout['burnout_risk'] > 0.6:
            insights.append(CoachInsight(
                insight_type="motivation_boost",
                title="🧘 Burnout Prevention",
                message=f"Analysis shows elevated burnout risk. Consider shorter sessions or a rest day.",
                priority="high",
                actionable=True,
                action_text="Try a 10-minute session instead of your usual"
            ))

        # 3. Streak Milestones
        if current_user.current_streak >= 7 and current_user.current_streak % 7 == 0:
            weeks = current_user.current_streak // 7
            insights.append(CoachInsight(
                insight_type="streak_milestone",
                title=f"🔥 {weeks}-Week Streak!",
                message=f"You've maintained consistency for {current_user.current_streak} days. This is exceptional!",
                priority="high",
                actionable=False
            ))

        # 4. Writing Patterns (from personality stats)
        coaching = ml_insights['coaching']
        personality_stats = coaching['personality_stats']

        # Find best performing personality
        valid_personalities = {k: v for k, v in personality_stats.items() if v['total_trials'] > 0}

        if valid_personalities:
            best_personality = max(
                valid_personalities.items(),
                key=lambda x: x[1]['success_rate']
            )

            if best_personality[1]['total_trials'] >= 5:
                personality_name = best_personality[0].replace('_', ' ').title()
                success_pct = best_personality[1]['success_rate'] * 100
                insights.append(CoachInsight(
                    insight_type="writing_pattern",
                    title="🎯 AI Optimization Active",
                    message=f"Analysis shows '{personality_name}' coaching style works best for you ({success_pct:.0f}% success rate)",
                    priority="medium",
                    actionable=False
                ))

        # 5. Get recent sessions for pattern analysis
        recent_sessions = db.query(WritingSession).filter(
            WritingSession.user_id == current_user.id,
            WritingSession.created_at >= datetime.utcnow() - timedelta(days=days)
        ).all()

        if recent_sessions:
            total_words = sum(s.word_count or 0 for s in recent_sessions)
            avg_words = total_words / len(recent_sessions)

            if avg_words >= 500:
                pages = int(avg_words / 250)
                insights.append(CoachInsight(
                    insight_type="writing_pattern",
                    title="📈 High Output Writer",
                    message=f"Averaging {int(avg_words)} words/session over the last {days} days. That's about {pages} pages of content per session!",
                    priority="medium",
                    actionable=False
                ))

            # Check for consistency
            if len(recent_sessions) >= days * 0.8:  # 80% or more days
                insights.append(CoachInsight(
                    insight_type="writing_pattern",
                    title="⭐ Consistency Champion",
                    message=f"You've written on {len(recent_sessions)} of the last {days} days. Your consistency is outstanding!",
                    priority="medium",
                    actionable=False
                ))

        # 6. Add risk factor insights if present
        if streak_risk.get('contributing_factors'):
            for factor in streak_risk['contributing_factors'][:2]:  # Top 2 factors
                if factor['severity'] == 'high':
                    insights.append(CoachInsight(
                        insight_type="risk_alert",
                        title="⚠️ Pattern Alert",
                        message=factor['description'],
                        priority="high",
                        actionable=True,
                        action_text="Address this today"
                    ))

        return insights

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ERROR in get_coach_insights: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/personality", response_model=dict)
async def update_personality_preference(
    update: PersonalityPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's AI personality preference.
    The system will use this as the starting preference.
    """
    try:
        current_user.personality_preference = update.personality_type.value
        db.commit()

        return {
            "message": f"AI personality updated to: {update.personality_type.value}",
            "personality": update.personality_type.value,
            "note": "The system will continue to learn which style works best for you"
        }
    except Exception as e:
        logger.error(f"ERROR in update_personality_preference: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def record_user_feedback(
    personality: str,
    response_type: str,
    time_to_action: Optional[float] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Record user response to AI coaching for learning.
    Frontend calls this when user takes action after seeing a message.
    """
    try:
        if ml_service is None:
            raise HTTPException(status_code=503, detail="ML service not available")

        # FIX: Call rule_coach.record_user_response instead
        ml_service.rule_coach.record_user_response(
            personality=personality,
            response_type=response_type,
            time_to_action=time_to_action
        )

        return {
            "message": "Feedback recorded. AI will adapt to your preferences.",
            "personality": personality,
            "response": response_type
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ERROR in record_user_feedback: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")  # Added full traceback
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/personality-stats")
async def get_personality_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get current performance stats for all AI personalities.
    Useful for dashboard/analytics.
    """
    try:
        if ml_service is None:
            raise HTTPException(status_code=503, detail="ML service not available")

        stats = ml_service.rule_coach.get_personality_stats()

        return {
            "personalities": stats,
            "active_learning": True,
            "total_interactions": sum(p['total_trials'] for p in stats.values()),
            "note": "Stats are based on user responses to different coaching styles"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ERROR in get_personality_stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
