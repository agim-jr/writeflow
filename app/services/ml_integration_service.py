# app/services/ml_integration_service.py
"""ML Integration Service - Now using rule-based system."""
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.rule_based_coach import RuleBasedCoach

class MLIntegrationService:
    """Coordinates AI coaching using rule-based system."""

    def __init__(self):
        self.rule_coach = RuleBasedCoach()
        print("✓ Rule-based coach initialized successfully")

    def generate_coaching_message(
        self,
        db: Session,
        user: User,
        context: Optional[Dict] = None
    ) -> Dict:
        """Generate personalized coaching message using rules."""
        if context is None:
            context = {}

        # Generate message using rule-based system
        result = self.rule_coach.generate_message(db, user, context)

        return result

    def record_user_response(
        self,
        personality: str,
        response_type: str,
        time_to_action: Optional[float] = None
    ):
        """Record user response to update personality effectiveness."""
        success = response_type in ['wrote_within_60min', 'wrote_same_day']
        self.rule_coach.record_feedback(personality, success)

    def get_complete_insights(self, db: Session, user: User) -> Dict:
        """Get all AI insights for a user."""
        # Generate a message to get full analysis
        result = self.rule_coach.generate_message(db, user, {'context_type': 'check_in'})

        return {
            'streak_risk': result['streak_risk'],
            'burnout_analysis': {
                'burnout_risk': result['streak_risk']['risk_score'] * 0.6,  # Derive from streak risk
                'prediction_horizon_days': 7,
                'early_warning_signs': [f['description'] for f in result['streak_risk']['contributing_factors']]
            },
            'coaching': {
                'selected_personality': result['personality'],
                'personality_stats': self.rule_coach.get_personality_stats(),
                'context': result['context']
            },
            'generated_at': datetime.utcnow().isoformat()
        }
