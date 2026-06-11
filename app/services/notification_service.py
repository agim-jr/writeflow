from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate
from app.services.ai_coach_service import AICoachService
from app.utils.time_helpers import get_current_time_in_timezone
import logging

logger = logging.getLogger(__name__)


class NotificationService:

    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        notification_data: NotificationCreate
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            user_id=user_id,
            type=notification_data.type,
            title=notification_data.title,
            message=notification_data.message,
            action_url=notification_data.action_url,
            metadata=notification_data.metadata
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: int,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50
    ) -> List[Notification]:
        """Get user's notifications."""
        query = db.query(Notification).filter(Notification.user_id == user_id)

        if unread_only:
            query = query.filter(Notification.is_read == False)

        return query.order_by(desc(Notification.created_at)).offset(skip).limit(limit).all()

    @staticmethod
    def mark_as_read(db: Session, notification_id: int) -> Optional[Notification]:
        """Mark notification as read."""
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.commit()
            db.refresh(notification)
        return notification

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        """Mark all user notifications as read."""
        count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({
            "is_read": True,
            "read_at": datetime.utcnow()
        })
        db.commit()
        return count

    @staticmethod
    def delete_notification(db: Session, notification_id: int) -> bool:
        """Delete a notification."""
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            db.delete(notification)
            db.commit()
            return True
        return False

    @staticmethod
    async def send_streak_reminder(db: Session, user: User, ai_service: AICoachService) -> Optional[Notification]:
        """Send AI-powered streak reminder."""
        try:
            # Get AI coaching intervention
            intervention = await ai_service.get_coaching_intervention(
                db, user, intervention_type="reminder"
            )

            notification_data = NotificationCreate(
                type="streak_reminder",
                title="Time to Write! ✍️",
                message=intervention.get("message", "Keep your streak alive!"),
                action_url="/write",
                metadata={
                    "ai_generated": True,
                    "intervention_data": intervention,
                    "risk_level": intervention.get("metadata", {}).get("risk_level")
                }
            )

            return NotificationService.create_notification(db, user.id, notification_data)
        except Exception as e:
            logger.error(f"Error sending streak reminder: {str(e)}")
            return None

    @staticmethod
    async def send_streak_warning(db: Session, user: User, ai_service: AICoachService) -> Optional[Notification]:
        """Send urgent streak warning."""
        try:
            intervention = await ai_service.get_coaching_intervention(
                db, user, intervention_type="warning"
            )

            notification_data = NotificationCreate(
                type="streak_warning",
                title="⚠️ Streak at Risk!",
                message=intervention.get("message", "Your streak is about to break!"),
                action_url="/write",
                metadata={
                    "ai_generated": True,
                    "intervention_data": intervention,
                    "priority": "high"
                }
            )

            return NotificationService.create_notification(db, user.id, notification_data)
        except Exception as e:
            logger.error(f"Error sending streak warning: {str(e)}")
            return None

    @staticmethod
    async def send_celebration(db: Session, user: User, milestone_type: str, ai_service: AICoachService) -> Optional[Notification]:
        """Send celebration notification."""
        try:
            intervention = await ai_service.get_coaching_intervention(
                db, user, intervention_type="celebration"
            )

            titles = {
                "streak_milestone": f"🎉 {user.current_streak} Day Streak!",
                "word_milestone": f"🎯 {user.total_words:,} Words Written!",
                "qualification": "🏆 You're Qualified!",
                "newsletter": "📧 Newsletter Published!"
            }

            notification_data = NotificationCreate(
                type="celebration",
                title=titles.get(milestone_type, "🎉 Achievement Unlocked!"),
                message=intervention.get("message", "Keep up the amazing work!"),
                action_url="/profile",
                metadata={
                    "ai_generated": True,
                    "milestone_type": milestone_type,
                    "intervention_data": intervention
                }
            )

            return NotificationService.create_notification(db, user.id, notification_data)
        except Exception as e:
            logger.error(f"Error sending celebration: {str(e)}")
            return None

    @staticmethod
    async def send_daily_check_in(db: Session, user: User, ai_service: AICoachService) -> Optional[Notification]:
        """Send personalized daily check-in."""
        try:
            intervention = await ai_service.get_coaching_intervention(
                db, user, intervention_type="check_in"
            )

            notification_data = NotificationCreate(
                type="daily_check_in",
                title="Good Morning! ☀️",
                message=intervention.get("message", "Ready to write today?"),
                action_url="/write",
                metadata={
                    "ai_generated": True,
                    "intervention_data": intervention
                }
            )

            return NotificationService.create_notification(db, user.id, notification_data)
        except Exception as e:
            logger.error(f"Error sending daily check-in: {str(e)}")
            return None

    @staticmethod
    async def send_burnout_warning(db: Session, user: User, burnout_data: Dict[str, Any]) -> Optional[Notification]:
        """Send burnout prevention warning."""
        try:
            notification_data = NotificationCreate(
                type="burnout_warning",
                title="Take Care of Yourself 💙",
                message="We've noticed some patterns that suggest you might need a break. Your well-being matters more than any streak.",
                action_url="/insights",
                metadata={
                    "ai_generated": True,
                    "burnout_risk": burnout_data.get("burnout_risk"),
                    "early_warning_signs": burnout_data.get("early_warning_signs", [])
                }
            )

            return NotificationService.create_notification(db, user.id, notification_data)
        except Exception as e:
            logger.error(f"Error sending burnout warning: {str(e)}")
            return None

    @staticmethod
    async def send_experiment_suggestion(
        db: Session,
        user: User,
        experiment_data: Dict[str, Any]
    ) -> Optional[Notification]:
        """Send AI-suggested experiment."""
        try:
            notification_data = NotificationCreate(
                type="experiment_suggestion",
                title="💡 Try Something New",
                message=experiment_data.get("suggestion", "We have an idea that might boost your writing!"),
                action_url="/experiments",
                metadata={
                    "ai_generated": True,
                    "experiment_type": experiment_data.get("type"),
                    "expected_impact": experiment_data.get("expected_impact"),
                    "experiment_data": experiment_data
                }
            )

            return NotificationService.create_notification(db, user.id, notification_data)
        except Exception as e:
            logger.error(f"Error sending experiment suggestion: {str(e)}")
            return None
