from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.models.user import User
from app.models.writing_session import WritingSession
from app.utils.time_helpers import get_current_time_in_timezone, is_same_day, days_between
import httpx
import json


class AICoachService:
    """
    Service to interact with the custom AI coaching system.
    This service prepares data and communicates with your multi-model AI ensemble.
    """

    def __init__(self, ai_api_url: str = None, ai_api_key: str = None):
        """Initialize AI Coach Service with custom AI endpoint."""
        self.ai_api_url = ai_api_url or "http://localhost:8001/ai"  # Your AI service URL
        self.ai_api_key = ai_api_key

    async def prepare_user_context(self, db: Session, user: User) -> Dict[str, Any]:
        """
        Prepare comprehensive user context for AI models.
        This is the rich data your AI ensemble needs for deep personalization.
        """
        # Get recent writing sessions (last 90 days for pattern analysis)
        recent_sessions = db.query(WritingSession).filter(
            WritingSession.user_id == user.id,
            WritingSession.created_at >= datetime.utcnow() - timedelta(days=90)
        ).order_by(desc(WritingSession.created_at)).all()

        # Calculate behavioral patterns
        behavioral_data = self._extract_behavioral_patterns(recent_sessions, user)

        # Calculate psychological state indicators
        psychological_data = self._extract_psychological_indicators(recent_sessions, user)

        # Calculate risk metrics
        risk_data = self._calculate_risk_metrics(recent_sessions, user)

        # Prepare temporal context
        temporal_data = self._prepare_temporal_context(user)

        # Build complete context
        context = {
            "user_id": user.id,
            "timestamp": datetime.utcnow().isoformat(),
            "profile": {
                "current_streak": user.current_streak,
                "longest_streak": user.longest_streak,
                "total_words": user.total_words,
                "total_sessions": user.total_sessions,
                "days_since_signup": (datetime.utcnow() - user.created_at).days,
                "is_qualified": user.is_qualified,
                "timezone": user.timezone,
            },
            "behavioral": behavioral_data,
            "psychological": psychological_data,
            "risk": risk_data,
            "temporal": temporal_data,
            "recent_sessions": [
                {
                    "date": s.created_at.isoformat(),
                    "word_count": s.word_count,
                    "duration_minutes": s.duration_minutes,
                    "time_of_day": s.created_at.hour if s.created_at else 0,
                    "day_of_week": s.created_at.weekday() if s.created_at else 0,
                }
                for s in recent_sessions[:30]  # Last 30 sessions
            ]
        }

        return context

    def _extract_behavioral_patterns(self, sessions: List[WritingSession], user: User) -> Dict[str, Any]:
        """Extract behavioral patterns for LSTM model."""
        if not sessions:
            return {
                "writing_times": [],
                "session_durations": [],
                "word_counts": [],
                "consistency_score": 0.0,
                "preferred_days": [],
                "session_frequency": 0.0
            }

        writing_times = [s.created_at.hour for s in sessions if s.created_at]
        session_durations = [s.duration_minutes for s in sessions if s.duration_minutes]
        word_counts = [s.word_count for s in sessions]
        day_of_week = [s.created_at.weekday() for s in sessions if s.created_at]

        # Calculate consistency score (0-1)
        if len(sessions) >= 7:
            last_7_days = sessions[:7]
            unique_days = len(set(s.created_at.date() for s in last_7_days if s.created_at))
            consistency_score = unique_days / 7.0
        else:
            consistency_score = len(sessions) / 7.0

        # Find preferred days
        from collections import Counter
        day_counts = Counter(day_of_week)
        preferred_days = [day for day, count in day_counts.most_common(3)]

        # Session frequency (sessions per week)
        if len(sessions) > 0:
            first_date = sessions[0].created_at
            last_date = sessions[-1].created_at
            if first_date and last_date:
                days_range = (first_date - last_date).days or 1
                session_frequency = (len(sessions) / days_range) * 7
            else:
                session_frequency = 0.0
        else:
            session_frequency = 0.0

        return {
            "writing_times": writing_times,
            "session_durations": session_durations,
            "word_counts": word_counts,
            "consistency_score": consistency_score,
            "preferred_days": preferred_days,
            "session_frequency": session_frequency,
            "average_word_count": sum(word_counts) / len(word_counts) if word_counts else 0,
            "average_duration": sum(session_durations) / len(session_durations) if session_durations else 0
        }

    def _extract_psychological_indicators(self, sessions: List[WritingSession], user: User) -> Dict[str, Any]:
        """Extract psychological state indicators."""
        if not sessions:
            return {
                "motivation_trend": "unknown",
                "burnout_risk": 0.0,
                "engagement_level": 0.0,
                "stress_indicators": []
            }

        # Analyze recent trend (last 14 days vs previous 14 days)
        recent = [s for s in sessions if s.created_at and (datetime.utcnow() - s.created_at).days <= 14]
        previous = [s for s in sessions if s.created_at and 14 < (datetime.utcnow() - s.created_at).days <= 28]

        recent_avg_words = sum(s.word_count for s in recent) / len(recent) if recent else 0
        previous_avg_words = sum(s.word_count for s in previous) / len(previous) if previous else 0

        # Determine motivation trend
        if previous_avg_words == 0:
            motivation_trend = "building"
        elif recent_avg_words > previous_avg_words * 1.1:
            motivation_trend = "increasing"
        elif recent_avg_words < previous_avg_words * 0.9:
            motivation_trend = "declining"
        else:
            motivation_trend = "stable"

        # Calculate burnout risk (0-1)
        burnout_indicators = 0
        if motivation_trend == "declining":
            burnout_indicators += 0.3
        if len(recent) < len(previous) * 0.7:
            burnout_indicators += 0.3
        if user.current_streak < user.longest_streak * 0.5:
            burnout_indicators += 0.2
        if recent_avg_words < 100:
            burnout_indicators += 0.2

        burnout_risk = min(burnout_indicators, 1.0)

        # Engagement level
        engagement = len(recent) / 14.0  # How many of last 14 days

        return {
            "motivation_trend": motivation_trend,
            "burnout_risk": burnout_risk,
            "engagement_level": engagement,
            "recent_avg_words": recent_avg_words,
            "previous_avg_words": previous_avg_words,
            "stress_indicators": self._detect_stress_indicators(sessions)
        }

    def _detect_stress_indicators(self, sessions: List[WritingSession]) -> List[str]:
        """Detect stress indicators from session patterns."""
        indicators = []

        if not sessions or len(sessions) < 5:
            return indicators

        recent_5 = sessions[:5]

        # Declining word counts
        word_counts = [s.word_count for s in recent_5]
        if len(word_counts) >= 3:
            if word_counts[0] < word_counts[2] * 0.5:
                indicators.append("declining_output")

        # Irregular timing
        times = [s.created_at.hour for s in recent_5 if s.created_at]
        if len(times) >= 3:
            time_variance = max(times) - min(times)
            if time_variance > 6:
                indicators.append("irregular_timing")

        # Short sessions
        durations = [s.duration_minutes for s in recent_5 if s.duration_minutes]
        if durations and sum(durations) / len(durations) < 15:
            indicators.append("short_sessions")

        return indicators

    def _calculate_risk_metrics(self, sessions: List[WritingSession], user: User) -> Dict[str, Any]:
        """Calculate risk metrics for Gradient Boosting model."""
        # Get the most recent session to determine last write date
        if not sessions:
            return {
                "streak_break_risk": 1.0,
                "hours_since_last_write": 999,
                "risk_level": "critical",
                "prediction_confidence": 0.0
            }

        last_write_date = sessions[0].created_at  # Most recent session
        hours_since_last = (datetime.utcnow() - last_write_date).total_seconds() / 3600

        # Calculate streak break risk (0-1)
        if hours_since_last < 12:
            risk = 0.0
        elif hours_since_last < 18:
            risk = 0.2
        elif hours_since_last < 22:
            risk = 0.5
        elif hours_since_last < 24:
            risk = 0.8
        else:
            risk = 1.0

        # Determine risk level
        if risk < 0.3:
            risk_level = "safe"
        elif risk < 0.6:
            risk_level = "warning"
        elif risk < 0.9:
            risk_level = "critical"
        else:
            risk_level = "broken"

        # Historical streak break analysis
        streak_breaks = self._analyze_historical_breaks(sessions, user)

        return {
            "streak_break_risk": risk,
            "hours_since_last_write": hours_since_last,
            "risk_level": risk_level,
            "prediction_confidence": 0.85,  # Your AI will calculate this
            "historical_break_patterns": streak_breaks
        }

    def _analyze_historical_breaks(self, sessions: List[WritingSession], user: User) -> Dict[str, Any]:
        """Analyze when user historically breaks streaks."""
        if len(sessions) < 14:
            return {"patterns": [], "common_day": None, "common_time": None}

        # Find gaps > 1 day
        breaks = []
        for i in range(len(sessions) - 1):
            if sessions[i].created_at and sessions[i+1].created_at:
                gap_days = (sessions[i].created_at - sessions[i+1].created_at).days
                if gap_days > 1:
                    breaks.append({
                        "date": sessions[i+1].created_at,
                        "day_of_week": sessions[i+1].created_at.weekday(),
                        "preceded_by_streak": i
                    })

        if not breaks:
            return {"patterns": [], "common_day": None, "common_time": None}

        # Find patterns
        from collections import Counter
        break_days = [b["day_of_week"] for b in breaks]
        common_day = Counter(break_days).most_common(1)[0][0] if break_days else None

        return {
            "total_breaks": len(breaks),
            "common_day": common_day,
            "average_streak_before_break": sum(b["preceded_by_streak"] for b in breaks) / len(breaks)
        }

    def _prepare_temporal_context(self, user: User) -> Dict[str, Any]:
        """Prepare temporal context (time, day, calendar info)."""
        now = get_current_time_in_timezone(user.timezone)

        return {
            "current_time": now.isoformat(),
            "hour": now.hour,
            "day_of_week": now.weekday(),
            "day_name": now.strftime("%A"),
            "is_weekend": now.weekday() >= 5,
            "is_morning": 5 <= now.hour < 12,
            "is_afternoon": 12 <= now.hour < 17,
            "is_evening": 17 <= now.hour < 22,
            "is_night": now.hour >= 22 or now.hour < 5
        }

    async def get_coaching_intervention(
        self,
        db: Session,
        user: User,
        intervention_type: str = "check_in"
    ) -> Dict[str, Any]:
        """
        Get AI coaching intervention.
        Types: check_in, reminder, encouragement, warning, celebration, experiment
        """
        context = await self.prepare_user_context(db, user)
        context["intervention_type"] = intervention_type

        # Call your custom AI service
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {}
                if self.ai_api_key:
                    headers["Authorization"] = f"Bearer {self.ai_api_key}"

                response = await client.post(
                    f"{self.ai_api_url}/coaching/intervention",
                    json=context,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            # Fallback to rule-based coaching if AI is unavailable
            return self._fallback_intervention(context, intervention_type)

    async def predict_streak_risk(self, db: Session, user: User) -> Dict[str, Any]:
        """
        Predict streak break risk 48 hours ahead.
        Uses your Gradient Boosting + Time Series models.
        """
        context = await self.prepare_user_context(db, user)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {}
                if self.ai_api_key:
                    headers["Authorization"] = f"Bearer {self.ai_api_key}"

                response = await client.post(
                    f"{self.ai_api_url}/prediction/streak-risk",
                    json=context,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            # Fallback prediction
            return {
                "risk_score": context["risk"]["streak_break_risk"],
                "risk_level": context["risk"]["risk_level"],
                "confidence": 0.5,
                "prediction_horizon_hours": 48,
                "recommended_action": "Write within the next 4 hours to maintain streak"
            }

    async def predict_burnout(self, db: Session, user: User) -> Dict[str, Any]:
        """
        Predict burnout 7 days ahead.
        Uses your Time Series + Psychological models.
        """
        context = await self.prepare_user_context(db, user)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {}
                if self.ai_api_key:
                    headers["Authorization"] = f"Bearer {self.ai_api_key}"

                response = await client.post(
                    f"{self.ai_api_url}/prediction/burnout",
                    json=context,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {
                "burnout_risk": context["psychological"]["burnout_risk"],
                "prediction_horizon_days": 7,
                "confidence": 0.5,
                "early_warning_signs": context["psychological"]["stress_indicators"]
            }

    async def analyze_writing_dna(self, db: Session, user: User) -> Dict[str, Any]:
        """
        Generate user's Writing DNA fingerprint.
        Uses your LSTM + Behavioral Analysis models.
        """
        context = await self.prepare_user_context(db, user)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {}
                if self.ai_api_key:
                    headers["Authorization"] = f"Bearer {self.ai_api_key}"

                response = await client.post(
                    f"{self.ai_api_url}/analysis/writing-dna",
                    json=context,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            # Fallback DNA analysis
            behavioral = context["behavioral"]
            return {
                "dna_fingerprint": {
                    "consistency_score": behavioral["consistency_score"],
                    "preferred_writing_times": behavioral["writing_times"][:5],
                    "average_session_length": behavioral["average_duration"],
                    "productivity_pattern": "morning" if any(t < 12 for t in behavioral["writing_times"][:5]) else "evening"
                },
                "insights": [
                    "Your writing patterns are still forming",
                    f"You typically write around {behavioral.get('average_word_count', 0):.0f} words per session"
                ]
            }

    async def suggest_optimal_time(self, db: Session, user: User) -> Dict[str, Any]:
        """
        Suggest optimal writing time for next session.
        Uses your Reinforcement Learning + Behavioral models.
        """
        context = await self.prepare_user_context(db, user)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {}
                if self.ai_api_key:
                    headers["Authorization"] = f"Bearer {self.ai_api_key}"

                response = await client.post(
                    f"{self.ai_api_url}/recommendation/optimal-time",
                    json=context,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            # Fallback suggestion
            behavioral = context["behavioral"]
            if behavioral["writing_times"]:
                from collections import Counter
                most_common_hour = Counter(behavioral["writing_times"]).most_common(1)[0][0]
                return {
                    "suggested_time": f"{most_common_hour:02d}:00",
                    "confidence": 0.6,
                    "reasoning": f"You've successfully written at {most_common_hour}:00 multiple times before"
                }
            return {
                "suggested_time": "09:00",
                "confidence": 0.3,
                "reasoning": "Morning writing sessions tend to have higher completion rates"
            }

    def _fallback_intervention(self, context: Dict[str, Any], intervention_type: str) -> Dict[str, Any]:
        """Fallback rule-based intervention when AI is unavailable."""
        profile = context["profile"]
        risk = context["risk"]

        messages = {
            "check_in": f"You're on a {profile['current_streak']} day streak. Keep it going!",
            "reminder": f"It's been {risk['hours_since_last_write']:.0f} hours since your last session. Time to write?",
            "warning": f"Your streak is at risk. Write something in the next {24 - risk['hours_since_last_write']:.0f} hours.",
            "celebration": f"Amazing! You've hit {profile['current_streak']} days in a row!",
            "encouragement": "Every word counts. Just show up today."
        }

        return {
            "intervention_type": intervention_type,
            "message": messages.get(intervention_type, "Keep writing!"),
            "tone": "supportive",
            "action_required": risk["risk_level"] in ["warning", "critical"],
            "metadata": {
                "is_fallback": True,
                "risk_level": risk["risk_level"]
            }
        }
