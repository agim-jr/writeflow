# app/services/rule_based_coach.py
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.writing_session import WritingSession
import logging
import random
from collections import Counter

logger = logging.getLogger(__name__)


class RuleBasedCoach:
    """
    Rule-based AI coach that uses heuristics and patterns to generate
    personalized coaching messages without requiring ML models.
    """

    def __init__(self):
        # Use the exact personality types from your API schema
        self.personality_stats = {
            'gentle_encouraging': {'total_trials': 0, 'successes': 0, 'success_rate': 0.0},
            'analytical_factual': {'total_trials': 0, 'successes': 0, 'success_rate': 0.0},
            'direct_challenging': {'total_trials': 0, 'successes': 0, 'success_rate': 0.0},
            'coach_mentor': {'total_trials': 0, 'successes': 0, 'success_rate': 0.0},
            'playful_casual': {'total_trials': 0, 'successes': 0, 'success_rate': 0.0},
        }

        # Message templates by personality and context
        self.message_templates = self._init_message_templates()

    def _init_message_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize message templates for each personality type and context"""
        return {
            'gentle_encouraging': {
                'session_start': [
                    "You've got this. Let's write together, one word at a time.",
                    "Ready when you are. I'm here to support your writing journey.",
                    "Take a breath. Your words matter, and I'm here to help them flow.",
                ],
                'milestone': [
                    "Look at you go! {milestone} words of pure progress. 🎉",
                    "You're doing amazing! {milestone} words closer to your goal.",
                    "Beautiful work! {milestone} words that didn't exist before today.",
                ],
                'stuck': [
                    "It's okay to pause. Sometimes the best words come after a moment of silence.",
                    "Feeling stuck? Try writing the worst version first. You can always fix it.",
                    "Writer's block is normal. What if you wrote just one sentence? Just to see what happens.",
                ],
                'encouragement': [
                    "You're in a beautiful flow. Keep riding this wave! 🌊",
                    "This is what momentum looks like. You're doing wonderful.",
                    "Look at this rhythm you've found. Let it carry you forward.",
                ],
            },
            'analytical_factual': {
                'session_start': [
                    "Session initialized. Current streak: {streak} days. Let's maintain momentum.",
                    "Based on your pattern, writing now maximizes your {time_of_day} productivity.",
                    "Optimal conditions detected. Your average {mode} session: {avg_words} words.",
                ],
                'milestone': [
                    "{milestone} words completed. That's {percent}% of your typical output. Efficiency: high.",
                    "Milestone reached: {milestone} words in {minutes} minutes. Current pace: {wpm} WPM.",
                    "Progress checkpoint: {milestone} words. Projected completion: {eta}.",
                ],
                'stuck': [
                    "Writing velocity decreased by {percent}%. Strategy: lower expectations for 5 minutes.",
                    "Inactivity detected: {minutes} minutes. Data shows 60-second bursts restart momentum.",
                    "Pattern analysis: you typically resume after {strategy}. Try that now.",
                ],
                'encouragement': [
                    "Peak performance detected. Current WPM: {wpm}. This is {percent}% above your average.",
                    "Flow state identified. Maintain current pace for optimal session outcome.",
                    "Consistency score: {score}/10. You're tracking {percent}% above last week.",
                ],
            },
            'direct_challenging': {
                'session_start': [
                    "Let's write. No excuses, no overthinking.",
                    "Time to work. Your {mode} session starts now.",
                    "Words don't write themselves. Get started.",
                ],
                'milestone': [
                    "{milestone} words. Keep going.",
                    "Nice. {milestone} down. Don't stop.",
                    "{milestone} words. Momentum. Use it.",
                ],
                'stuck': [
                    "Stuck? Write badly. You can fix it later.",
                    "Stop thinking. Start typing. Anything.",
                    "You're wasting time. Write one sentence. Now.",
                ],
                'encouragement': [
                    "You're on fire. Don't stop.",
                    "This is the zone. Stay in it.",
                    "Perfect pace. Keep pushing.",
                ],
            },
            'coach_mentor': {
                'session_start': [
                    "Today's the day you make magic happen! Let's GO! 🚀",
                    "You're about to create something AMAZING! I believe in you!",
                    "Every great writer started with a blank page. Time to fill yours with brilliance! ✨",
                ],
                'milestone': [
                    "BOOM! {milestone} words of PURE AWESOME! You're unstoppable! 🔥",
                    "YES! {milestone} words! You're not just writing, you're CONQUERING! 💪",
                    "{milestone} words of VICTORY! Keep this energy flowing! ⚡",
                ],
                'stuck': [
                    "Champions don't quit! Write ONE word. Then another. You've got this! 💪",
                    "This is your hero moment! Push through! The breakthrough is coming!",
                    "Resistance means you're growing! Write through it! Future you will thank you!",
                ],
                'encouragement': [
                    "YOU'RE IN THE ZONE! This is what excellence looks like! 🌟",
                    "INCREDIBLE! Look at you absolutely CRUSHING this session!",
                    "THIS is your superpower! Keep channeling this energy! ⚡",
                ],
            },
            'playful_casual': {
                'session_start': [
                    "Hey there! Ready to make some word magic? ✨",
                    "Let's do this thing! No pressure, just vibes and words.",
                    "Alright wordsmith, let's see what you've got today! 😄",
                ],
                'milestone': [
                    "Whoa, {milestone} words already? You're crushing it! 🎉",
                    "Look at you go! {milestone} words and counting. Nice!",
                    "{milestone} words? That's what I'm talking about! Keep it flowing! 🌊",
                ],
                'stuck': [
                    "Brain feeling foggy? Totally normal! Maybe try a different scene?",
                    "Stuck? No worries! Sometimes the best stuff comes after a quick break. ☕",
                    "Writer's block? Pfft. Just write something silly first. Seriously, it works!",
                ],
                'encouragement': [
                    "Dude, you're in the zone right now! This is awesome! 🚀",
                    "Look at this flow! You're making it look easy!",
                    "This is exactly what writing should feel like. You're nailing it! 🎯",
                ],
            },
        }

    def generate_message(self, db: Session, user: User, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a coaching message based on user context and personality preference.

        Args:
            db: Database session
            user: User object
            context: Dictionary with context info (context_type, streak, word_count, etc.)

        Returns:
            Dictionary with message, personality, and risk analysis
        """
        try:
            # 1. Analyze user patterns
            user_analysis = self._analyze_user(db, user, context)

            # 2. Select appropriate personality
            personality = self._select_personality(user, user_analysis, context)

            # 3. Generate message
            message = self._generate_message_for_context(
                personality,
                context,
                user_analysis
            )

            # 4. Calculate streak risk
            streak_risk = self._calculate_streak_risk(user, user_analysis)

            return {
                'message': message,
                'personality': personality,
                'streak_risk': streak_risk,
                'user_analysis': user_analysis
            }

        except Exception as e:
            logger.error(f"Error in generate_message: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # Fallback to simple message
            return {
                'message': "Ready to write? Let's make it count.",
                'personality': 'gentle_encouraging',
                'streak_risk': {'risk_level': 'low', 'contributing_factors': []},
                'user_analysis': {}
            }

    def _analyze_user(self, db: Session, user: User, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user's writing patterns and current state"""
        try:
            # Get recent sessions - make datetime timezone-aware
            now = datetime.now(timezone.utc)
            recent_sessions = db.query(WritingSession).filter(
                WritingSession.user_id == user.id,
                WritingSession.created_at >= now - timedelta(days=30)
            ).all()

            # Make all datetime comparisons timezone-aware
            last_7_days = []
            for s in recent_sessions:
                # Make session created_at timezone-aware if it's naive
                session_time = s.created_at
                if session_time.tzinfo is None:
                    session_time = session_time.replace(tzinfo=timezone.utc)

                # Check if within last 7 days
                if (now - session_time).days <= 7:
                    last_7_days.append(s)

            last_30_days = recent_sessions

            # Calculate metrics
            avg_word_count = (
                sum(s.word_count or 0 for s in last_7_days) / len(last_7_days)
                if last_7_days else 0
            )

            # FIX: Use duration_minutes, not duration_seconds
            avg_session_duration = (
                sum((s.duration_minutes or 0) * 60 for s in last_7_days) / len(last_7_days)
                if last_7_days else 0
            )

            # Check if user prefers certain times
            session_hours = [s.created_at.hour for s in last_30_days if s.created_at]
            preferred_time = None
            if session_hours:
                hour_counts = Counter(session_hours)
                most_common_hour = hour_counts.most_common(1)[0][0]
                if 5 <= most_common_hour < 12:
                    preferred_time = 'morning'
                elif 12 <= most_common_hour < 17:
                    preferred_time = 'afternoon'
                elif 17 <= most_common_hour < 22:
                    preferred_time = 'evening'
                else:
                    preferred_time = 'night'

            # Days since last write
            if user.last_write_date:
                # Handle both naive and aware datetimes
                last_write = user.last_write_date
                if isinstance(last_write, datetime):
                    if last_write.tzinfo is None:
                        last_write = last_write.replace(tzinfo=timezone.utc)
                    days_since_last = (now - last_write).days
                else:
                    # It's a date object
                    days_since_last = (now.date() - last_write).days
            else:
                days_since_last = 999

            return {
                'total_sessions_30d': len(last_30_days),
                'total_sessions_7d': len(last_7_days),
                'avg_word_count': avg_word_count,
                'avg_session_duration': avg_session_duration,
                'preferred_time': preferred_time,
                'days_since_last_write': days_since_last,
                'current_streak': user.current_streak,
                'longest_streak': user.longest_streak,
            }

        except Exception as e:
            logger.error(f"Error analyzing user: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'total_sessions_30d': 0,
                'total_sessions_7d': 0,
                'avg_word_count': 0,
                'avg_session_duration': 0,
                'preferred_time': None,
                'days_since_last_write': 0,
                'current_streak': user.current_streak or 0,
                'longest_streak': user.longest_streak or 0,
            }

    def _select_personality(self, user: User, analysis: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Select best personality type based on user preference and performance stats"""

        # 1. Check if user has explicit preference
        if hasattr(user, 'personality_preference') and user.personality_preference:
            if user.personality_preference in self.personality_stats:
                return user.personality_preference

        # 2. Check context preferences
        if context.get('preferred_personality'):
            return context['preferred_personality']

        # 3. Use performance-based selection (epsilon-greedy)
        # 10% exploration
        if random.random() < 0.1:
            return random.choice(list(self.personality_stats.keys()))

        # 90% exploitation - use best performing personality
        best_personality = max(
            self.personality_stats.items(),
            key=lambda x: x[1]['success_rate'] if x[1]['total_trials'] > 0 else 0
        )

        # If no trials yet, default to gentle_encouraging
        if best_personality[1]['total_trials'] == 0:
            return 'gentle_encouraging'

        return best_personality[0]

    def _generate_message_for_context(
        self,
        personality: str,
        context: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> str:
        """Generate specific message based on context and personality"""

        context_type = context.get('context_type', 'session_start')

        # Get templates for this personality and context
        templates = self.message_templates.get(personality, {}).get(context_type, [])

        if not templates:
            return "Let's write. You've got this."

        # Select random template
        template = random.choice(templates)

        # Fill in template variables
        try:
            # Calculate some dynamic values
            time_elapsed_minutes = int(context.get('time_elapsed', 0) / 60)
            word_count = context.get('word_count', 0)

            # Avoid division by zero
            wpm = 0
            if time_elapsed_minutes > 0 and word_count > 0:
                wpm = int(word_count / time_elapsed_minutes)

            avg_words = max(int(analysis.get('avg_word_count', 0)), 1)
            percent = int((word_count / avg_words) * 100) if avg_words > 0 else 0

            message = template.format(
                milestone=context.get('milestone', 0),
                streak=context.get('current_streak', analysis.get('current_streak', 0)),
                mode=context.get('session_type', 'writing'),
                time_of_day=analysis.get('preferred_time', 'preferred'),
                avg_words=avg_words,
                minutes=time_elapsed_minutes,
                wpm=wpm,
                percent=percent,
                score=min(10, int(analysis.get('current_streak', 0) / 3)),
                strategy="taking a short break",
                eta="soon"
            )
        except (KeyError, ZeroDivisionError) as e:
            # If template has variables we don't have, use it as-is
            logger.debug(f"Template formatting issue: {e}, using template as-is")
            message = template

        return message

    def _calculate_streak_risk(self, user: User, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk of losing current streak"""

        days_since = analysis.get('days_since_last_write', 0)
        current_streak = analysis.get('current_streak', 0)

        risk_factors = []
        risk_level = 'low'

        # High risk: Haven't written today and it's late
        if days_since >= 1:
            risk_level = 'high'
            risk_factors.append({
                'factor': 'days_since_last_write',
                'severity': 'high',
                'description': f"Haven't written in {days_since} days - streak at immediate risk"
            })

        # Medium risk: Written today but long streak means higher stakes
        elif current_streak >= 30 and days_since == 0:
            risk_level = 'medium'
            risk_factors.append({
                'factor': 'high_streak_maintenance',
                'severity': 'medium',
                'description': f"Your {current_streak}-day streak is valuable - stay consistent"
            })

        # Check session frequency
        if analysis.get('total_sessions_7d', 0) < 3:
            risk_factors.append({
                'factor': 'low_frequency',
                'severity': 'medium',
                'description': "Writing less than 3x per week increases risk"
            })
            if risk_level == 'low':
                risk_level = 'medium'

        return {
            'risk_level': risk_level,
            'days_since_last_write': days_since,
            'contributing_factors': risk_factors,
            'current_streak': current_streak
        }

    def record_user_response(self, personality: str, response_type: str, time_to_action: Optional[float] = None):
        """Record user's response to coaching for learning"""

        if personality not in self.personality_stats:
            logger.warning(f"Unknown personality type: {personality}")
            return

        self.personality_stats[personality]['total_trials'] += 1

        # Count as success if user wrote within reasonable time
        if response_type in ['wrote_within_60min', 'session_completed', 'milestone_reached']:
            self.personality_stats[personality]['successes'] += 1

        # Update success rate
        trials = self.personality_stats[personality]['total_trials']
        successes = self.personality_stats[personality]['successes']
        self.personality_stats[personality]['success_rate'] = successes / trials if trials > 0 else 0

        logger.info(f"Personality '{personality}' stats updated: {self.personality_stats[personality]}")

    def get_personality_stats(self) -> Dict[str, Dict[str, float]]:
        """Get current performance statistics for all personalities"""
        return self.personality_stats

    def get_complete_insights(self, db: Session, user: User) -> Dict[str, Any]:
        """Get comprehensive analysis and insights for user"""

        context = {'context_type': 'analysis'}
        analysis = self._analyze_user(db, user, context)
        streak_risk = self._calculate_streak_risk(user, analysis)

        # Calculate burnout risk based on session intensity
        burnout_risk = 0.0
        if analysis['total_sessions_7d'] > 0:
            avg_duration = analysis['avg_session_duration']
            # High burnout risk if consistently long sessions (>90 min)
            if avg_duration > 5400:  # 90 minutes
                burnout_risk = 0.7
            elif avg_duration > 3600:  # 60 minutes
                burnout_risk = 0.4
            else:
                burnout_risk = 0.1

        return {
            'user_analysis': analysis,
            'streak_risk': streak_risk,
            'burnout_analysis': {
                'burnout_risk': burnout_risk,
                'avg_session_duration': analysis['avg_session_duration'],
                'sessions_per_week': analysis['total_sessions_7d']
            },
            'coaching': {
                'personality_stats': self.personality_stats,
                'recommended_personality': self._select_personality(user, analysis, context)
            }
        }
