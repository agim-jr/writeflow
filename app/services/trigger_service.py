"""
Smart Trigger System
Decides when and how to intervene based on user behavior, risk levels, and AI predictions
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Dict, Optional
import logging

from app.models.user import User
from app.models.writing_session import WritingSession
from app.services.ai_coach_service import AICoachService
from app.services.notification_service import NotificationService
from app.schemas.notification import NotificationCreate

logger = logging.getLogger(__name__)


class TriggerService:
    """Manages all proactive intervention triggers"""

    def __init__(self):
        self.ai_coach = AICoachService()

    async def evaluate_all_triggers(self, db: Session, user: User) -> List[Dict]:
        """
        Evaluate all possible triggers for a user
        Returns list of triggered interventions sorted by priority
        """

        triggers = []

        # === TEMPORAL TRIGGERS ===
        temporal = await self._check_temporal_triggers(db, user)
        triggers.extend(temporal)

        # === BEHAVIORAL TRIGGERS ===
        behavioral = await self._check_behavioral_triggers(db, user)
        triggers.extend(behavioral)

        # === PREDICTIVE TRIGGERS ===
        predictive = await self._check_predictive_triggers(db, user)
        triggers.extend(predictive)

        # === MILESTONE TRIGGERS ===
        milestone = await self._check_milestone_triggers(db, user)
        triggers.extend(milestone)

        # === SOCIAL TRIGGERS ===
        social = await self._check_social_triggers(db, user)
        triggers.extend(social)

        # Sort by priority (high -> medium -> low)
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        triggers.sort(key=lambda x: priority_order.get(x['priority'], 999))

        return triggers

    async def _check_temporal_triggers(self, db: Session, user: User) -> List[Dict]:
        """Time-based triggers"""

        triggers = []
        now = datetime.utcnow()

        if not user.last_write_date:
            return triggers

        hours_since_write = (now - datetime.combine(user.last_write_date, datetime.min.time())).total_seconds() / 3600

        # Streak at risk
        if hours_since_write >= 18 and user.current_streak > 0:
            triggers.append({
                'type': 'temporal',
                'trigger': 'streak_risk',
                'priority': 'high' if hours_since_write >= 22 else 'medium',
                'action': 'send_streak_reminder',
                'data': {
                    'hours_since': hours_since_write,
                    'streak': user.current_streak
                }
            })

        # Long absence (3+ days)
        if hours_since_write >= 72:
            triggers.append({
                'type': 'temporal',
                'trigger': 'long_absence',
                'priority': 'medium',
                'action': 'send_comeback_message',
                'data': {
                    'days_absent': int(hours_since_write / 24)
                }
            })

        return triggers

    async def _check_behavioral_triggers(self, db: Session, user: User) -> List[Dict]:
        """Behavior pattern triggers"""

        triggers = []

        # Get recent sessions (last 14 days)
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)
        recent_sessions = db.query(WritingSession).filter(
            and_(
                WritingSession.user_id == user.id,
                WritingSession.created_at >= two_weeks_ago
            )
        ).all()

        if len(recent_sessions) == 0:
            return triggers

        # Declining engagement pattern
        if len(recent_sessions) < 5:
            triggers.append({
                'type': 'behavioral',
                'trigger': 'declining_engagement',
                'priority': 'medium',
                'action': 'send_encouragement',
                'data': {
                    'sessions_count': len(recent_sessions),
                    'period_days': 14
                }
            })

        # Declining word count pattern
        recent_words = [s.word_count or 0 for s in recent_sessions[:5]]
        if len(recent_words) >= 3:
            avg_recent = sum(recent_words[:2]) / 2
            avg_older = sum(recent_words[2:]) / len(recent_words[2:])

            if avg_recent < avg_older * 0.6:  # 40% drop
                triggers.append({
                    'type': 'behavioral',
                    'trigger': 'declining_output',
                    'priority': 'medium',
                    'action': 'send_output_check',
                    'data': {
                        'recent_avg': avg_recent,
                        'previous_avg': avg_older,
                        'drop_percentage': ((avg_older - avg_recent) / avg_older * 100)
                    }
                })

        # Irregular timing pattern
        if len(recent_sessions) >= 5:
            write_hours = [s.created_at.hour for s in recent_sessions if s.created_at]
            if write_hours:
                hour_variance = max(write_hours) - min(write_hours)
                if hour_variance > 8:  # Writing at very different times
                    triggers.append({
                        'type': 'behavioral',
                        'trigger': 'irregular_timing',
                        'priority': 'low',
                        'action': 'suggest_routine',
                        'data': {
                            'variance_hours': hour_variance
                        }
                    })

        return triggers

    async def _check_predictive_triggers(self, db: Session, user: User) -> List[Dict]:
        """AI prediction-based triggers"""

        triggers = []

        # Only run predictions for established users
        if user.total_sessions < 5:
            return triggers

        try:
            # Burnout prediction
            burnout = await self.ai_coach.predict_burnout(db, user)
            burnout_risk = burnout.get('burnout_risk', 0)

            if burnout_risk > 0.7:
                triggers.append({
                    'type': 'predictive',
                    'trigger': 'high_burnout_risk',
                    'priority': 'high',
                    'action': 'send_burnout_prevention',
                    'data': burnout
                })

            elif burnout_risk > 0.5:
                triggers.append({
                    'type': 'predictive',
                    'trigger': 'medium_burnout_risk',
                    'priority': 'medium',
                    'action': 'send_wellness_tip',
                    'data': burnout
                })

            # Streak break prediction
            streak_risk = await self.ai_coach.predict_streak_risk(db, user)
            risk_score = streak_risk.get('risk_score', 0)

            if risk_score > 0.8 and user.current_streak >= 7:
                triggers.append({
                    'type': 'predictive',
                    'trigger': 'streak_break_predicted',
                    'priority': 'critical',
                    'action': 'send_urgent_intervention',
                    'data': streak_risk
                })

        except Exception as e:
            logger.error(f"Error in predictive triggers: {str(e)}")

        return triggers

    async def _check_milestone_triggers(self, db: Session, user: User) -> List[Dict]:
        """Achievement milestone triggers"""

        triggers = []

        # Streak milestones
        milestone_streaks = [7, 14, 21, 30, 50, 75, 100, 365]
        if user.current_streak in milestone_streaks:
            triggers.append({
                'type': 'milestone',
                'trigger': 'streak_milestone',
                'priority': 'high',
                'action': 'send_celebration',
                'data': {
                    'milestone_type': 'streak',
                    'value': user.current_streak
                }
            })

        # Word count milestones
        word_milestones = [10000, 25000, 50000, 100000, 250000, 500000, 1000000]
        for milestone in word_milestones:
            if milestone <= user.total_words < milestone + 500:
                triggers.append({
                    'type': 'milestone',
                    'trigger': 'word_milestone',
                    'priority': 'medium',
                    'action': 'send_word_celebration',
                    'data': {
                        'milestone_type': 'words',
                        'value': milestone
                    }
                })
                break

        # First qualification
        if user.is_qualified and user.total_sessions <= user.total_sessions:  # Just qualified
            # Check if we haven't sent qualification celebration yet
            triggers.append({
                'type': 'milestone',
                'trigger': 'qualification_achieved',
                'priority': 'high',
                'action': 'send_qualification_celebration',
                'data': {
                    'milestone_type': 'qualification'
                }
            })

        return triggers

    async def _check_social_triggers(self, db: Session, user: User) -> List[Dict]:
        """Social/community triggers"""

        triggers = []

        # Newsletter eligibility
        if user.is_qualified and user.current_streak >= 7:
            # Check if user has published recently
            # (You'll need to add newsletter tracking)
            triggers.append({
                'type': 'social',
                'trigger': 'newsletter_reminder',
                'priority': 'low',
                'action': 'remind_newsletter_eligibility',
                'data': {
                    'streak': user.current_streak,
                    'is_qualified': user.is_qualified
                }
            })

        return triggers

    async def execute_trigger(self, db: Session, user: User, trigger: Dict) -> bool:
        """Execute a trigger's action"""

        action = trigger.get('action')
        data = trigger.get('data', {})

        try:
            if action == 'send_streak_reminder':
                await NotificationService.send_streak_reminder(db, user, self.ai_coach)
                return True

            elif action == 'send_streak_warning':
                await NotificationService.send_streak_warning(db, user, self.ai_coach)
                return True

            elif action == 'send_encouragement':
                intervention = await self.ai_coach.get_coaching_intervention(
                    db, user, intervention_type="encouragement"
                )
                notification = NotificationCreate(
                    type="encouragement",
                    title="💪 Keep Going",
                    message=intervention.get('message', "You're doing great!"),
                    action_url="/write",
                    metadata={'intervention_data': intervention}
                )
                NotificationService.create_notification(db, user.id, notification)
                return True

            elif action == 'send_burnout_prevention':
                await NotificationService.send_burnout_warning(db, user, data)
                return True

            elif action == 'send_celebration':
                milestone_type = data.get('milestone_type')
                await NotificationService.send_celebration(db, user, milestone_type, self.ai_coach)
                return True

            elif action == 'send_comeback_message':
                days_absent = data.get('days_absent', 0)
                notification = NotificationCreate(
                    type="comeback",
                    title="We Miss You! 🌟",
                    message=f"It's been {days_absent} days. Ready to write again? Every journey starts with a single word.",
                    action_url="/write",
                    metadata={'days_absent': days_absent}
                )
                NotificationService.create_notification(db, user.id, notification)
                return True

            elif action == 'suggest_routine':
                optimal_time = await self.ai_coach.suggest_optimal_time(db, user)
                notification = NotificationCreate(
                    type="experiment_suggestion",
                    title="💡 Build a Writing Routine",
                    message=f"Try writing at {optimal_time.get('suggested_time', '9:00')} every day. Consistency builds habits.",
                    action_url="/insights",
                    metadata={'optimal_time_data': optimal_time}
                )
                NotificationService.create_notification(db, user.id, notification)
                return True

            else:
                logger.warning(f"Unknown trigger action: {action}")
                return False

        except Exception as e:
            logger.error(f"Error executing trigger {action}: {str(e)}")
            return False


# Global trigger service instance
trigger_service = TriggerService()
