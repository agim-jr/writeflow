from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.user import User
from app.models.writing_session import WritingSession
from app.utils.time_helpers import is_same_day, days_between, get_date_from_datetime


class StreakService:

    @staticmethod
    def calculate_current_streak(db: Session, user: User) -> int:
        """Calculate user's current writing streak."""
        if not user.last_write_date:
            return 0

        # Get all writing sessions ordered by date
        sessions = db.query(WritingSession).filter(
            WritingSession.user_id == user.id,
            WritingSession.is_counted_for_streak == True
        ).order_by(desc(WritingSession.session_date)).all()

        if not sessions:
            return 0

        current_date = get_date_from_datetime(datetime.utcnow(), user.timezone)
        streak = 0
        expected_date = current_date

        # Group sessions by date
        sessions_by_date = {}
        for session in sessions:
            session_date = get_date_from_datetime(session.session_date, user.timezone)
            if session_date not in sessions_by_date:
                sessions_by_date[session_date] = True

        # Count consecutive days
        while expected_date in sessions_by_date:
            streak += 1
            expected_date = expected_date.replace(day=expected_date.day - 1)

        return streak

    @staticmethod
    def update_streak(db: Session, user: User) -> tuple[int, int]:
        """Update user's streak after a writing session."""
        current_streak = StreakService.calculate_current_streak(db, user)

        # Update longest streak if current is higher
        longest_streak = max(user.longest_streak, current_streak)

        user.current_streak = current_streak
        user.longest_streak = longest_streak
        user.last_write_date = datetime.utcnow()

        db.commit()
        db.refresh(user)

        return current_streak, longest_streak

    @staticmethod
    def check_qualification(db: Session, user: User) -> bool:
        """Check if user has qualified (7 consecutive days)."""
        if user.is_qualified:
            return True

        current_streak = StreakService.calculate_current_streak(db, user)

        if current_streak >= 7:
            user.is_qualified = True
            user.qualification_date = datetime.utcnow()
            db.commit()
            return True

        return False

    @staticmethod
    def get_streak_risk_level(db: Session, user: User) -> str:
        """Determine if streak is at risk based on last write time."""
        if not user.last_write_date:
            return "no_streak"

        now = datetime.utcnow()
        hours_since_last_write = (now - user.last_write_date).total_seconds() / 3600

        # Check if already written today
        if is_same_day(user.last_write_date, now, user.timezone):
            return "safe"

        # Check if it's been more than 24 hours
        if hours_since_last_write > 24:
            return "broken"

        # Within 24 hours but not written today
        if hours_since_last_write > 20:
            return "critical"
        elif hours_since_last_write > 16:
            return "warning"
        else:
            return "safe"
