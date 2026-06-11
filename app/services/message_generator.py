"""Message generation service using trained neural model."""
from typing import Optional
from app.ml_models.message_generation.inference import MessageInference
from app.ml_models.message_generation.config import ModelConfig


class MessageGenerator:
    """Service for generating personalized coaching messages."""

    def __init__(self):
        self.config = ModelConfig()
        self.inference = MessageInference()
        self.is_loaded = False

        # Try to load the trained model
        try:
            self.is_loaded = self.inference.load()
            if self.is_loaded:
                print("✓ Neural message generator loaded successfully")
        except Exception as e:
            print(f"⚠ Could not load neural model: {e}")
            print("⚠ Falling back to rule-based messages")

    def generate_message(
        self,
        personality_type: str,
        current_streak: int,
        days_since_last_write: int,
        risk_level: str,
        model_type: str = 'markov'  # Keep for compatibility
    ) -> str:
        """
        Generate a personalized coaching message.

        Args:
            personality_type: One of the personality types
            current_streak: User's current streak count
            days_since_last_write: Days since last write
            risk_level: 'low', 'medium', or 'high'
            model_type: Ignored (kept for compatibility)

        Returns:
            Generated message string
        """

        # If neural model is loaded, use it
        if self.is_loaded:
            try:
                user_context = {
                    'current_streak': current_streak,
                    'days_since_last_write': days_since_last_write
                }

                message = self.inference.generate(
                    personality=personality_type,
                    risk_level=risk_level,
                    user_context=user_context
                )

                return message

            except Exception as e:
                print(f"⚠ Neural generation failed: {e}, using fallback")
                # Fall through to fallback

        # Fallback to rule-based messages
        return self._generate_fallback_message(
            personality_type,
            current_streak,
            days_since_last_write,
            risk_level
        )

    def _generate_fallback_message(
        self,
        personality: str,
        streak: int,
        days_since: int,
        risk: str
    ) -> str:
        """Fallback rule-based messages when neural model unavailable."""

        templates = {
            'direct_challenging': {
                'low': f"Your {streak}-day streak is strong. Keep pushing.",
                'medium': f"It's been {days_since} days. Write now to save your {streak}-day streak.",
                'high': f"URGENT: {streak} days at risk. Write immediately."
            },
            'gentle_encouraging': {
                'low': f"You're doing great with {streak} days! Ready for today?",
                'medium': f"I notice it's been {days_since} days. Your {streak}-day journey misses you!",
                'high': f"Please don't give up on {streak} days of progress. You've got this!"
            },
            'analytical_factual': {
                'low': f"Streak: {streak} days. Status: stable. Continue pattern.",
                'medium': f"Alert: {days_since} days elapsed. {streak}-day streak at risk.",
                'high': f"Critical: Immediate action required to preserve {streak}-day data."
            }
        }

        # Get template or use default
        personality_templates = templates.get(personality, templates['gentle_encouraging'])
        message = personality_templates.get(risk, personality_templates['low'])

        return message
