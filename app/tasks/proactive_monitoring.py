"""
Proactive AI Monitoring System
Runs background jobs to monitor users and send interventions automatically
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.database import SessionLocal
from app.models.user import User
from app.models.writing_session import WritingSession
from app.services.ai_coach_service import AICoachService
from app.services.notification_service import NotificationService
from app.utils.time_helpers import get_current_time_in_timezone
import logging

logger = logging.getLogger(__name__)


class ProactiveMonitor:
    """Central hub for all proactive AI monitoring"""

    def __init__(self):
        self.ai_coach = AICoachService()

    async def monitor_streak_risks(self):
        """
        CRITICAL: Check all users for streak risks every 5 minutes
        This is the heart of proactive intervention
        """
        db = SessionLocal()
        try:
            logger.info("🔍 Starting streak risk monitoring...")

            now = datetime.utcnow()
            today = now.date()

            # Get all active users with current streaks
            active_users = db.query(User).filter(
                User.is_active == True,
                User.current_streak > 0
            ).all()

            interventions_sent = 0

            for user in active_users:
                try:
                    # Skip if already written today
                    if user.last_write_date and user.last_write_date >= today:
                        continue

                    # Calculate hours since last write
                    if user.last_write_date:
                        last_write_datetime = datetime.combine(user.last_write_date, datetime.min.time())
                        hours_since = (now - last_write_datetime).total_seconds() / 3600
                    else:
                        hours_since = 999

                    # Get user's local time
                    user_local_time = get_current_time_in_timezone(user.timezone)
                    user_hour = user_local_time.hour

                    # === INTERVENTION LOGIC ===

                    # Level 1: Gentle reminder (18 hours, only during waking hours)
                    if 18 <= hours_since < 19 and 8 <= user_hour <= 22:
                        await self._send_gentle_reminder(db, user)
                        interventions_sent += 1
                        logger.info(f"📬 Sent gentle reminder to user {user.id} ({hours_since:.1f}h)")

                    # Level 2: Strong reminder (20 hours)
                    elif 20 <= hours_since < 21 and 8 <= user_hour <= 23:
                        await self._send_strong_reminder(db, user)
                        interventions_sent += 1
                        logger.warning(f"⚠️ Sent strong reminder to user {user.id} ({hours_since:.1f}h)")

                    # Level 3: Urgent warning (22 hours)
                    elif 22 <= hours_since < 23:
                        await self._send_urgent_warning(db, user)
                        interventions_sent += 1
                        logger.error(f"🚨 Sent urgent warning to user {user.id} ({hours_since:.1f}h)")

                    # Level 4: Last chance (23.5 hours)
                    elif 23.5 <= hours_since < 24:
                        await self._send_last_chance(db, user)
                        interventions_sent += 1
                        logger.critical(f"⏰ Sent last chance to user {user.id}")

                    # Streak broken (24+ hours)
                    elif hours_since >= 24:
                        await self._handle_streak_break(db, user)
                        logger.error(f"💔 User {user.id} streak broken after {user.current_streak} days")

                except Exception as e:
                    logger.error(f"Error monitoring user {user.id}: {str(e)}")
                    continue

            logger.info(f"✅ Streak monitoring complete. Sent {interventions_sent} interventions")

        except Exception as e:
            logger.error(f"Critical error in streak monitoring: {str(e)}")
        finally:
            db.close()

    async def _send_gentle_reminder(self, db: Session, user: User):
        """First gentle nudge"""
        intervention = await self.ai_coach.get_coaching_intervention(
            db, user, intervention_type="reminder"
        )
        await NotificationService.send_streak_reminder(db, user, self.ai_coach)

    async def _send_strong_reminder(self, db: Session, user: User):
        """Stronger reminder with urgency"""
        intervention = await self.ai_coach.get_coaching_intervention(
            db, user, intervention_type="warning"
        )
        await NotificationService.send_streak_reminder(db, user, self.ai_coach)

    async def _send_urgent_warning(self, db: Session, user: User):
        """Urgent warning - streak in danger"""
        await NotificationService.send_streak_warning(db, user, self.ai_coach)

    async def _send_last_chance(self, db: Session, user: User):
        """Final warning before streak breaks"""
        from app.schemas.notification import NotificationCreate

        notification = NotificationCreate(
            type="streak_critical",
            title=f"🚨 {user.current_streak}-Day Streak Ends in 30 Minutes!",
            message=f"This is your last chance to save your {user.current_streak}-day streak. Write anything - even one sentence counts!",
            action_url="/write",
            metadata={
                "urgency": "critical",
                "hours_remaining": 0.5,
                "streak_value": user.current_streak
            }
        )
        NotificationService.create_notification(db, user.id, notification)

    async def _handle_streak_break(self, db: Session, user: User):
        """Handle broken streak with empathy"""
        from app.schemas.notification import NotificationCreate

        old_streak = user.current_streak
        user.current_streak = 0
        user.last_write_date = None
        db.commit()

        notification = NotificationCreate(
            type="streak_broken",
            title="Streak Reset - But You're Not Starting Over",
            message=f"Your {old_streak}-day streak ended, but you proved you can do it. Start again today - you know the way.",
            action_url="/write",
            metadata={
                "previous_streak": old_streak,
                "encouragement": True
            }
        )
        NotificationService.create_notification(db, user.id, notification)

    async def send_morning_check_ins(self):
        """Send personalized morning check-ins at each user's 9 AM"""
        db = SessionLocal()
        try:
            logger.info("☀️ Starting morning check-ins...")

            active_users = db.query(User).filter(User.is_active == True).all()
            sent_count = 0

            for user in active_users:
                try:
                    user_local_time = get_current_time_in_timezone(user.timezone)

                    # Send at user's 9 AM (±5 min window)
                    if user_local_time.hour == 9 and 0 <= user_local_time.minute < 5:
                        await NotificationService.send_daily_check_in(db, user, self.ai_coach)
                        sent_count += 1
                        logger.info(f"☀️ Sent morning check-in to user {user.id}")

                except Exception as e:
                    logger.error(f"Error sending check-in to user {user.id}: {str(e)}")
                    continue

            logger.info(f"✅ Morning check-ins complete. Sent {sent_count} messages")

        except Exception as e:
            logger.error(f"Error in morning check-ins: {str(e)}")
        finally:
            db.close()

    async def detect_burnout_patterns(self):
        """Predict and prevent burnout before it happens"""
        db = SessionLocal()
        try:
            logger.info("🧘 Starting burnout detection...")

            active_users = db.query(User).filter(
                User.is_active == True,
                User.current_streak >= 14  # Only check users with established streaks
            ).all()

            warnings_sent = 0

            for user in active_users:
                try:
                    # Get AI burnout prediction
                    burnout_prediction = await self.ai_coach.predict_burnout(db, user)

                    risk_score = burnout_prediction.get('burnout_risk', 0)

                    # High risk: immediate intervention
                    if risk_score > 0.7:
                        await NotificationService.send_burnout_warning(db, user, burnout_prediction)
                        warnings_sent += 1
                        logger.warning(f"🧘 Sent burnout warning to user {user.id} (risk: {risk_score:.2f})")

                    # Medium risk: gentle suggestion
                    elif risk_score > 0.5:
                        from app.schemas.notification import NotificationCreate

                        notification = NotificationCreate(
                            type="wellness_tip",
                            title="💙 Taking Care of Yourself",
                            message="You're doing great, but remember: rest is part of the process. Consider shorter sessions this week.",
                            action_url="/insights",
                            metadata={
                                "burnout_risk": risk_score,
                                "suggestion": "reduce_intensity"
                            }
                        )
                        NotificationService.create_notification(db, user.id, notification)
                        logger.info(f"💙 Sent wellness tip to user {user.id}")

                except Exception as e:
                    logger.error(f"Error detecting burnout for user {user.id}: {str(e)}")
                    continue

            logger.info(f"✅ Burnout detection complete. Sent {warnings_sent} warnings")

        except Exception as e:
            logger.error(f"Error in burnout detection: {str(e)}")
        finally:
            db.close()

    async def send_weekly_insights(self):
        """Send personalized weekly performance analysis"""
        db = SessionLocal()
        try:
            logger.info("📊 Generating weekly insights...")

            active_users = db.query(User).filter(
                User.is_active == True,
                User.total_sessions >= 7  # Only users with enough data
            ).all()

            insights_sent = 0

            for user in active_users:
                try:
                    # Get user's Sunday 8 PM
                    user_local_time = get_current_time_in_timezone(user.timezone)

                    if user_local_time.weekday() == 6 and user_local_time.hour == 20:
                        # Generate Writing DNA analysis
                        dna_analysis = await self.ai_coach.analyze_writing_dna(db, user)

                        # Get week's sessions
                        week_ago = datetime.utcnow() - timedelta(days=7)
                        week_sessions = db.query(WritingSession).filter(
                            and_(
                                WritingSession.user_id == user.id,
                                WritingSession.created_at >= week_ago
                            )
                        ).all()

                        total_words = sum(s.word_count or 0 for s in week_sessions)

                        from app.schemas.notification import NotificationCreate

                        notification = NotificationCreate(
                            type="weekly_insights",
                            title=f"📊 Your Week: {len(week_sessions)} Sessions, {total_words:,} Words",
                            message=f"This week you wrote {total_words:,} words across {len(week_sessions)} sessions. {dna_analysis.get('insights', ['Keep going!'])[0]}",
                            action_url="/insights",
                            metadata={
                                "weekly_stats": {
                                    "sessions": len(week_sessions),
                                    "total_words": total_words,
                                    "dna_analysis": dna_analysis
                                }
                            }
                        )
                        NotificationService.create_notification(db, user.id, notification)
                        insights_sent += 1
                        logger.info(f"📊 Sent weekly insights to user {user.id}")

                except Exception as e:
                    logger.error(f"Error sending insights to user {user.id}: {str(e)}")
                    continue

            logger.info(f"✅ Weekly insights complete. Sent {insights_sent} reports")

        except Exception as e:
            logger.error(f"Error in weekly insights: {str(e)}")
        finally:
            db.close()

    async def celebrate_milestones(self):
        """Automatically celebrate achievements"""
        db = SessionLocal()
        try:
            logger.info("🎉 Checking for milestones...")

            # Get users who just hit milestones today
            today = datetime.utcnow().date()

            # Streak milestones (7, 14, 30, 50, 100 days)
            milestone_days = [7, 14, 30, 50, 100, 365]

            for milestone in milestone_days:
                users_at_milestone = db.query(User).filter(
                    User.current_streak == milestone,
                    User.last_write_date == today
                ).all()

                for user in users_at_milestone:
                    try:
                        await NotificationService.send_celebration(
                            db, user, "streak_milestone", self.ai_coach
                        )
                        logger.info(f"🎉 Celebrated {milestone}-day streak for user {user.id}")
                    except Exception as e:
                        logger.error(f"Error celebrating for user {user.id}: {str(e)}")

            # Word count milestones
            word_milestones = [10000, 50000, 100000, 250000, 500000, 1000000]

            for milestone in word_milestones:
                users_near_milestone = db.query(User).filter(
                    User.total_words >= milestone,
                    User.total_words < milestone + 1000  # Just crossed it
                ).all()

                for user in users_near_milestone:
                    try:
                        # Check if we already celebrated this milestone
                        from app.models.notification import Notification
                        already_celebrated = db.query(Notification).filter(
                            Notification.user_id == user.id,
                            Notification.type == "celebration",
                            Notification.metadata.contains({"milestone_type": "word_milestone", "words": milestone})
                        ).first()

                        if not already_celebrated:
                            await NotificationService.send_celebration(
                                db, user, "word_milestone", self.ai_coach
                            )
                            logger.info(f"🎉 Celebrated {milestone:,} words for user {user.id}")
                    except Exception as e:
                        logger.error(f"Error celebrating words for user {user.id}: {str(e)}")

            logger.info("✅ Milestone celebrations complete")

        except Exception as e:
            logger.error(f"Error in milestone celebrations: {str(e)}")
        finally:
            db.close()

    async def optimize_writing_times(self):
        """Suggest optimal writing times based on AI analysis"""
        db = SessionLocal()
        try:
            logger.info("⏰ Analyzing optimal writing times...")

            active_users = db.query(User).filter(
                User.is_active == True,
                User.total_sessions >= 10
            ).all()

            suggestions_sent = 0

            for user in active_users:
                try:
                    # Get AI suggestion for optimal time
                    optimal_time = await self.ai_coach.suggest_optimal_time(db, user)

                    if optimal_time.get('confidence', 0) > 0.7:
                        from app.schemas.notification import NotificationCreate

                        notification = NotificationCreate(
                            type="experiment_suggestion",
                            title=f"💡 Try Writing at {optimal_time['suggested_time']}",
                            message=optimal_time.get('reasoning', 'AI analysis suggests this might be your best time'),
                            action_url="/experiments",
                            metadata={
                                "experiment_type": "time_optimization",
                                "suggested_time": optimal_time['suggested_time'],
                                "confidence": optimal_time['confidence']
                            }
                        )
                        NotificationService.create_notification(db, user.id, notification)
                        suggestions_sent += 1
                        logger.info(f"⏰ Sent time optimization to user {user.id}")

                except Exception as e:
                    logger.error(f"Error optimizing time for user {user.id}: {str(e)}")
                    continue

            logger.info(f"✅ Time optimization complete. Sent {suggestions_sent} suggestions")

        except Exception as e:
            logger.error(f"Error in time optimization: {str(e)}")
        finally:
            db.close()


# Global monitor instance
proactive_monitor = ProactiveMonitor()
