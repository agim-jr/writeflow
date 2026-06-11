import numpy as np
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from typing import Dict


class StreakRiskPredictor:
    def __init__(self, model_path: str = None):
        self.model = None
        if model_path:
            try:
                import lightgbm as lgb
                self.model = lgb.Booster(model_file=model_path)
            except:
                self.model = None

    def predict_risk(self, db: Session, user, current_time: datetime = None) -> dict:
        """Predict probability of streak break in next 48 hours."""
        if current_time is None:
            current_time = datetime.now(timezone.utc)  # FIXED: timezone-aware

        # Get writing sessions
        from app.models.writing_session import WritingSession

        sessions = db.query(WritingSession).filter(
            WritingSession.user_id == user.id
        ).order_by(WritingSession.created_at.desc()).limit(30).all()

        # Calculate features
        hours_since_last = 0
        if sessions:
            last_session = sessions[0]

            # FIXED: Handle timezone-aware datetime comparison
            session_time = last_session.created_at
            if session_time.tzinfo is None:
                session_time = session_time.replace(tzinfo=timezone.utc)

            hours_since_last = (current_time - session_time).total_seconds() / 3600
        else:
            hours_since_last = 168  # 1 week

        current_streak = user.current_streak

        # Calculate completion rate
        recent_sessions = [s for s in sessions if
                          (s.created_at.replace(tzinfo=timezone.utc) if s.created_at.tzinfo is None else s.created_at)
                          >= current_time - timedelta(days=7)]
        completion_rate_7d = len([s for s in recent_sessions if s.goal_met]) / max(len(recent_sessions), 1)

        # Calculate risk
        risk = self._heuristic_risk(hours_since_last, current_streak, completion_rate_7d)

        # Determine risk level
        if risk > 0.7:
            risk_level = "high"
            action = "immediate"
        elif risk > 0.4:
            risk_level = "medium"
            action = "preventive"
        else:
            risk_level = "low"
            action = "monitor"

        return {
            'risk_score': float(risk),
            'risk_level': risk_level,
            'recommended_action': action,
            'contributing_factors': self._identify_risk_factors(hours_since_last, current_streak, completion_rate_7d),
            'intervention_suggestions': self._suggest_interventions(risk, hours_since_last)
        }

    def _heuristic_risk(self, hours_since_last, current_streak, completion_rate_7d):
        """Simple heuristic when model not available."""
        risk = 0.0

        if hours_since_last > 36:
            risk += 0.4
        elif hours_since_last > 24:
            risk += 0.2

        if completion_rate_7d < 0.6:
            risk += 0.3

        if current_streak > 50 and hours_since_last > 20:
            risk += 0.2

        return min(1.0, risk)

    def _identify_risk_factors(self, hours_since_last, current_streak, completion_rate_7d):
        factors = []

        if hours_since_last > 24:
            factors.append({
                'factor': 'time_since_last_write',
                'severity': 'high' if hours_since_last > 36 else 'medium',
                'description': f'{int(hours_since_last)} hours since last write'
            })

        if completion_rate_7d < 0.6:
            factors.append({
                'factor': 'low_completion_rate',
                'severity': 'medium',
                'description': f'Only {int(completion_rate_7d * 100)}% completion rate this week'
            })

        if current_streak > 50:
            factors.append({
                'factor': 'high_stakes',
                'severity': 'info',
                'description': f'{current_streak}-day streak at risk'
            })

        return factors

    def _suggest_interventions(self, risk, hours_since_last):
        suggestions = []

        if risk > 0.7:
            suggestions.append({
                'type': 'urgent_notification',
                'message': 'Write now to save your streak!',
                'priority': 'high'
            })

        if hours_since_last > 24:
            suggestions.append({
                'type': 'gentle_reminder',
                'message': 'Just 100 words to keep your streak alive',
                'priority': 'medium'
            })

        return suggestions
