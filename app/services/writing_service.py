from datetime import datetime, timedelta, date
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.user import User
from app.models.writing_session import WritingSession
from app.schemas.writing_session import WritingSessionCreate, WritingSessionUpdate
from app.services.streak_service import StreakService
from app.services.milestone_service import MilestoneService
from app.utils.time_helpers import is_same_day


class WritingService:

    @staticmethod
    def check_and_reset_daily_goal(db: Session, user: User):
        """Reset daily goal tracking if it's a new day."""
        today = date.today()

        # If it's a new day, reset daily counters
        if user.last_goal_check_date != today:
            user.today_words = 0
            user.today_goal_met = False
            user.can_share_today = False
            user.last_goal_check_date = today
            db.commit()

    @staticmethod
    def create_session(
        db: Session,
        user: User,
        session_data: WritingSessionCreate
    ) -> WritingSession:
        """Create a new writing session."""
        # Reset daily tracking if new day
        WritingService.check_and_reset_daily_goal(db, user)

        # Check if user already wrote today
        now = datetime.utcnow()
        already_wrote_today = False

        if user.last_write_date:
            already_wrote_today = is_same_day(user.last_write_date, now, user.timezone)

        # Create session
        session = WritingSession(
            user_id=user.id,
            word_count=session_data.word_count,
            duration_minutes=session_data.duration_minutes,
            content=session_data.content,
            session_date=now,
            started_at=now,
            is_counted_for_streak=not already_wrote_today  # Only first session of day counts
        )

        db.add(session)

        # Update user stats
        user.total_words += session_data.word_count
        user.total_sessions += 1

        # ✅ NEW: Track today's words
        user.today_words += session_data.word_count

        # ✅ NEW: Check if daily goal is met
        if user.today_words >= user.daily_goal_words and not user.today_goal_met:
            user.today_goal_met = True
            user.can_share_today = True  # Unlock sharing!
            print(f"🎉 Daily goal reached! {user.today_words}/{user.daily_goal_words} words")

        # Update streak if this is first write of the day
        if not already_wrote_today:
            StreakService.update_streak(db, user)

            # Check qualification
            if not user.is_qualified:
                StreakService.check_qualification(db, user)

            # Check for milestones
            MilestoneService.check_and_award_milestones(db, user)

        db.commit()
        db.refresh(session)

        return session

    @staticmethod
    def update_session(
        db: Session,
        session: WritingSession,
        session_data: WritingSessionUpdate
    ) -> WritingSession:
        """Update an existing writing session."""
        if session_data.content is not None:
            session.content = session_data.content

        if session_data.word_count is not None:
            # Update user's total word count
            word_diff = session_data.word_count - session.word_count
            user = db.query(User).filter(User.id == session.user_id).first()

            user.total_words += word_diff

            # ✅ NEW: Update today's words
            user.today_words += word_diff

            # ✅ NEW: Check if goal met
            if user.today_words >= user.daily_goal_words and not user.today_goal_met:
                user.today_goal_met = True
                user.can_share_today = True
                print(f"🎉 Daily goal reached during update! {user.today_words}/{user.daily_goal_words} words")

            session.word_count = session_data.word_count

        if session_data.ended_at is not None:
            session.ended_at = session_data.ended_at

        if session_data.duration_minutes is not None:
            session.duration_minutes = session_data.duration_minutes

        db.commit()
        db.refresh(session)

        return session

    @staticmethod
    def publish_newsletter(
        db: Session,
        session: WritingSession,
        newsletter_title: str
    ) -> WritingSession:
        """Mark a session as published newsletter."""
        session.is_published = True
        session.published_at = datetime.utcnow()
        session.newsletter_title = newsletter_title

        # Update user's newsletter count
        user = db.query(User).filter(User.id == session.user_id).first()
        user.newsletters_published += 1

        # Check for publishing milestones
        MilestoneService.check_and_award_milestones(db, user)

        db.commit()
        db.refresh(session)

        return session

    @staticmethod
    def get_user_sessions(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[WritingSession]:
        """Get user's writing sessions."""
        return db.query(WritingSession).filter(
            WritingSession.user_id == user_id
        ).order_by(desc(WritingSession.session_date)).offset(skip).limit(limit).all()

    @staticmethod
    def get_daily_progress(db: Session, user: User) -> dict:
        """Get today's writing progress and sharing eligibility."""
        WritingService.check_and_reset_daily_goal(db, user)

        progress_percent = 0
        if user.daily_goal_words > 0:
            progress_percent = min(100, int((user.today_words / user.daily_goal_words) * 100))

        return {
            "today_words": user.today_words,
            "daily_goal": user.daily_goal_words,
            "goal_met": user.today_goal_met,
            "can_share": user.can_share_today,
            "progress_percent": progress_percent,
            "words_remaining": max(0, user.daily_goal_words - user.today_words)
        }

    @staticmethod
    def get_session_stats(db: Session, user: User) -> dict:
        """Get comprehensive session statistics."""
        # Total stats
        total_sessions = user.total_sessions
        total_words = user.total_words

        # This week stats
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_sessions = db.query(WritingSession).filter(
            WritingSession.user_id == user.id,
            WritingSession.session_date >= week_ago
        ).all()

        sessions_this_week = len(week_sessions)
        words_this_week = sum(s.word_count for s in week_sessions)

        # Average duration
        sessions_with_duration = db.query(WritingSession).filter(
            WritingSession.user_id == user.id,
            WritingSession.duration_minutes.isnot(None)
        ).all()

        avg_duration = None
        if sessions_with_duration:
            avg_duration = sum(s.duration_minutes for s in sessions_with_duration) / len(sessions_with_duration)

        # Most productive time
        all_sessions = db.query(WritingSession).filter(
            WritingSession.user_id == user.id
        ).all()

        if all_sessions:
            from collections import Counter

            # Time of day
            hours = [s.started_at.hour for s in all_sessions if s.started_at]
            most_common_hour = Counter(hours).most_common(1)[0][0] if hours else None

            # Day of week
            days = [s.session_date.strftime("%A") for s in all_sessions]
            most_common_day = Counter(days).most_common(1)[0][0] if days else None
        else:
            most_common_hour = None
            most_common_day = None

        return {
            "total_sessions": total_sessions,
            "total_words": total_words,
            "average_session_duration": avg_duration,
            "sessions_this_week": sessions_this_week,
            "words_this_week": words_this_week,
            "most_productive_time": f"{most_common_hour}:00" if most_common_hour else None,
            "most_productive_day": most_common_day
        }
