from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, cast, Date
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.models.user import User
from app.models.writing_session import WritingSession


class AnalyticsService:
    """Service for generating user analytics and insights."""

    @staticmethod
    def get_performance_metrics(db: Session, user: User) -> Dict:
        """Calculate comprehensive performance metrics for a user."""

        # Time periods
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Get writing sessions
        total_sessions = db.query(WritingSession).filter(
            WritingSession.user_id == user.id
        ).count()

        sessions_this_week = db.query(WritingSession).filter(
            and_(
                WritingSession.user_id == user.id,
                WritingSession.created_at >= week_ago
            )
        ).count()

        sessions_this_month = db.query(WritingSession).filter(
            and_(
                WritingSession.user_id == user.id,
                WritingSession.created_at >= month_ago
            )
        ).count()

        # Word count statistics
        total_words = db.query(func.sum(WritingSession.word_count)).filter(
            WritingSession.user_id == user.id
        ).scalar() or 0

        words_this_week = db.query(func.sum(WritingSession.word_count)).filter(
            and_(
                WritingSession.user_id == user.id,
                WritingSession.created_at >= week_ago
            )
        ).scalar() or 0

        words_this_month = db.query(func.sum(WritingSession.word_count)).filter(
            and_(
                WritingSession.user_id == user.id,
                WritingSession.created_at >= month_ago
            )
        ).scalar() or 0

        # Average words per session
        avg_words = total_words / total_sessions if total_sessions > 0 else 0

        # Writing duration
        total_duration = db.query(func.sum(WritingSession.duration_minutes)).filter(
            WritingSession.user_id == user.id
        ).scalar() or 0

        avg_session_duration = total_duration / total_sessions if total_sessions > 0 else 0

        return {
            "sessions": {
                "total": total_sessions,
                "this_week": sessions_this_week,
                "this_month": sessions_this_month
            },
            "words": {
                "total": int(total_words),
                "this_week": int(words_this_week),
                "this_month": int(words_this_month),
                "average_per_session": round(avg_words, 2)
            },
            "streaks": {
                "current": user.current_streak or 0,
                "longest": user.longest_streak or 0
            },
            "time": {
                "total_minutes": int(total_duration),
                "average_session_minutes": round(avg_session_duration, 2)
            }
        }

    @staticmethod
    def get_writing_patterns(db: Session, user: User, days: int = 7) -> Dict:
        """Analyze writing patterns over a specified period."""

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        sessions = db.query(WritingSession).filter(
            and_(
                WritingSession.user_id == user.id,
                WritingSession.created_at >= cutoff_date
            )
        ).order_by(WritingSession.created_at).all()

        if not sessions:
            return {
                "daily_patterns": [],
                "hourly_distribution": {},
                "productivity_insights": {
                    "most_productive_day": None,
                    "most_productive_hour": None,
                    "consistency_score": 0
                }
            }

        # Daily patterns
        daily_data = {}
        for session in sessions:
            date_key = session.created_at.date().isoformat()
            if date_key not in daily_data:
                daily_data[date_key] = {
                    "date": date_key,
                    "sessions": 0,
                    "words": 0,
                    "duration": 0
                }
            daily_data[date_key]["sessions"] += 1
            daily_data[date_key]["words"] += session.word_count
            daily_data[date_key]["duration"] += session.duration_minutes or 0

        # Hourly distribution
        hourly_data = {}
        for session in sessions:
            hour = session.created_at.hour
            if hour not in hourly_data:
                hourly_data[hour] = {
                    "sessions": 0,
                    "words": 0
                }
            hourly_data[hour]["sessions"] += 1
            hourly_data[hour]["words"] += session.word_count

        # Find most productive times
        most_productive_day = max(daily_data.items(), key=lambda x: x[1]["words"])[0] if daily_data else None
        most_productive_hour = max(hourly_data.items(), key=lambda x: x[1]["words"])[0] if hourly_data else None

        # Consistency score (percentage of days with activity)
        days_with_activity = len(daily_data)
        consistency_score = (days_with_activity / days) * 100

        return {
            "daily_patterns": list(daily_data.values()),
            "hourly_distribution": hourly_data,
            "productivity_insights": {
                "most_productive_day": most_productive_day,
                "most_productive_hour": most_productive_hour,
                "consistency_score": round(consistency_score, 2)
            }
        }

    @staticmethod
    def get_streak_history(db: Session, user: User) -> List[Dict]:
        """Get detailed streak history with breaks."""

        sessions = db.query(
            cast(WritingSession.created_at, Date).label('date')
        ).filter(
            WritingSession.user_id == user.id
        ).distinct().order_by(desc('date')).limit(90).all()

        if not sessions:
            return []

        dates = [session.date for session in sessions]
        streaks = []
        current_streak = {"start": dates[0], "end": dates[0], "days": 1}

        for i in range(1, len(dates)):
            if (dates[i-1] - dates[i]).days == 1:
                current_streak["days"] += 1
                current_streak["start"] = dates[i]
            else:
                streaks.append({
                    "start_date": current_streak["start"].isoformat(),
                    "end_date": current_streak["end"].isoformat(),
                    "days": current_streak["days"]
                })
                current_streak = {"start": dates[i], "end": dates[i], "days": 1}

        streaks.append({
            "start_date": current_streak["start"].isoformat(),
            "end_date": current_streak["end"].isoformat(),
            "days": current_streak["days"]
        })

        return streaks

    @staticmethod
    def get_word_count_trends(db: Session, user: User, period: str = "week") -> Dict:
        """Get word count trends over time."""

        if period == "week":
            days = 7
        elif period == "month":
            days = 30
        else:  # year
            days = 365

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        sessions = db.query(
            cast(WritingSession.created_at, Date).label('date'),
            func.sum(WritingSession.word_count).label('words')
        ).filter(
            and_(
                WritingSession.user_id == user.id,
                WritingSession.created_at >= cutoff_date
            )
        ).group_by(cast(WritingSession.created_at, Date)).order_by('date').all()

        trend_data = [
            {"date": session.date.isoformat(), "words": session.words}
            for session in sessions
        ]

        total_words = sum(item["words"] for item in trend_data)
        avg_words_per_day = total_words / days if days > 0 else 0

        return {
            "period": period,
            "data": trend_data,
            "summary": {
                "total_words": total_words,
                "average_per_day": round(avg_words_per_day, 2),
                "days_analyzed": days
            }
        }

    @staticmethod
    def compare_with_community(db: Session, user: User) -> Dict:
        """Compare user's stats with community averages."""

        # Get community averages
        community_stats = db.query(
            func.avg(User.total_words).label('avg_words'),
            func.avg(User.current_streak).label('avg_streak'),
            func.avg(User.total_sessions).label('avg_sessions')
        ).filter(User.is_active == True).first()

        user_percentile_words = db.query(func.count(User.id)).filter(
            and_(
                User.is_active == True,
                User.total_words < user.total_words
            )
        ).scalar() or 0

        total_users = db.query(func.count(User.id)).filter(
            User.is_active == True
        ).scalar() or 1

        percentile = (user_percentile_words / total_users) * 100 if total_users > 0 else 0

        return {
            "user": {
                "total_words": user.total_words or 0,
                "current_streak": user.current_streak or 0,
                "total_sessions": user.total_sessions or 0
            },
            "community": {
                "average_words": round(community_stats.avg_words or 0, 2),
                "average_streak": round(community_stats.avg_streak or 0, 2),
                "average_sessions": round(community_stats.avg_sessions or 0, 2)
            },
            "percentile": round(percentile, 2)
        }
