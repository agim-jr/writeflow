"""
Real-Time WebSocket System for Live Writing Session Monitoring
Enables proactive AI interventions DURING writing
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta, date
from typing import Dict, Optional
import json
import asyncio
import logging

from app.core.database import get_db
from app.models.user import User
from app.models.writing_session import WritingSession
from app.ml_models.state_detector import StateDetector
from app.services.ai_coach_service import AICoachService
from app.services.notification_service import NotificationService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize AI components
state_detector = StateDetector()
ai_coach = AICoachService()

# Active WebSocket connections
active_sessions: Dict[int, WebSocket] = {}  # {user_id: websocket}
session_data: Dict[int, dict] = {}  # {user_id: session_info}


class SessionMonitor:
    """Monitors a single writing session in real-time"""

    def __init__(self, user: User, session_id: int, db: Session):
        self.user = user
        self.session_id = session_id
        self.db = db
        self.typing_buffer = []
        self.last_state_check = datetime.now(timezone.utc)
        self.last_intervention = datetime.now(timezone.utc)
        self.word_count = 0
        self.last_activity = datetime.now(timezone.utc)
        self.interventions_sent = 0
        self.has_written_today = False  # NEW: Track if user wrote today

    async def process_keystroke(self, event: dict) -> Optional[dict]:
        """Process keystroke event and decide if intervention needed"""

        self.typing_buffer.append(event)
        self.last_activity = datetime.now(timezone.utc)

        # Update word count if provided
        if 'word_count' in event:
            old_count = self.word_count
            self.word_count = event['word_count']

            # NEW: Update last_write_date when user actually writes
            if self.word_count > old_count and not self.has_written_today:
                self._update_last_write_date()
                self.has_written_today = True

        # Check state every 10 seconds
        now = datetime.now(timezone.utc)
        if (now - self.last_state_check).seconds >= 10:
            return await self._check_state()

        return None

    def _update_last_write_date(self):
        """Update user's last_write_date to today"""
        try:
            today = date.today()
            if self.user.last_write_date != today:
                self.user.last_write_date = today
                self.db.commit()
                logger.info(f"✍️ Updated last_write_date for user {self.user.id} to {today}")
        except Exception as e:
            logger.error(f"Failed to update last_write_date for user {self.user.id}: {str(e)}")
            self.db.rollback()

    async def check_inactivity(self) -> Optional[dict]:
        """Check if user has been inactive and needs nudge"""

        now = datetime.now(timezone.utc)
        inactive_seconds = (now - self.last_activity).seconds

        # 2 minutes of inactivity
        if inactive_seconds >= 120:
            # Don't spam - wait 5 minutes between interventions
            if (now - self.last_intervention).seconds < 300:
                return None

            self.last_intervention = now
            self.interventions_sent += 1

            return {
                'type': 'inactivity_nudge',
                'message': "Still there? Just write one sentence to get back in flow.",
                'reason': 'inactivity_detected',
                'inactive_minutes': inactive_seconds // 60
            }

        return None

    async def _check_state(self) -> Optional[dict]:
        """Detect psychological state and intervene if needed"""

        self.last_state_check = datetime.now(timezone.utc)

        if len(self.typing_buffer) < 10:
            return None

        # Use AI to detect state
        state = state_detector.predict_state(self.typing_buffer)

        logger.info(f"User {self.user.id} state: {state['state']} (confidence: {state['confidence']:.2f})")

        # Only intervene if high confidence and haven't intervened recently
        if state['confidence'] < 0.7:
            return None

        now = datetime.now(timezone.utc)
        if (now - self.last_intervention).seconds < 180:  # 3 min cooldown
            return None

        intervention = None

        # === STATE-BASED INTERVENTIONS ===

        if state['state'] == 'blocked':
            intervention = {
                'type': 'coaching_nudge',
                'message': "Feeling stuck? Try writing badly on purpose. Just get words down.",
                'reason': 'writer_block_detected',
                'state': state
            }

        elif state['state'] == 'procrastinating':
            intervention = {
                'type': 'coaching_nudge',
                'message': "I see you. Stop overthinking. Write one terrible sentence. Go.",
                'reason': 'procrastination_detected',
                'state': state
            }

        elif state['state'] == 'struggling':
            intervention = {
                'type': 'coaching_nudge',
                'message': "This is hard, I know. But you're here. That's what matters. Keep going.",
                'reason': 'struggle_detected',
                'state': state
            }

        elif state['state'] == 'rushing':
            intervention = {
                'type': 'coaching_nudge',
                'message': "Slow down. Quality over speed. You've got time.",
                'reason': 'rushing_detected',
                'state': state
            }

        elif state['state'] == 'flow' and len(self.typing_buffer) > 200:
            intervention = {
                'type': 'encouragement',
                'message': "🔥 You're in the zone! This is what it feels like. Keep riding the wave.",
                'reason': 'flow_detected',
                'state': state
            }

        if intervention:
            self.last_intervention = now
            self.interventions_sent += 1
            logger.info(f"📬 Sent intervention to user {self.user.id}: {intervention['reason']}")

        # Keep only recent events
        self.typing_buffer = self.typing_buffer[-150:]

        return intervention

    async def check_milestones(self) -> Optional[dict]:
        """Check for word count milestones during session"""

        milestones = [100, 250, 500, 750, 1000, 1500, 2000]

        for milestone in milestones:
            # Just crossed milestone
            if self.word_count >= milestone and self.word_count < milestone + 10:
                return {
                    'type': 'milestone_celebration',
                    'message': f"🎯 {milestone} words! You're crushing it!",
                    'reason': 'word_milestone',
                    'milestone': milestone
                }

        return None


@router.websocket("/ws/writing-session")
async def writing_session_websocket(
    websocket: WebSocket,
    user_id: Optional[int] = Query(None),
    session_id: Optional[int] = Query(None)
):
    """
    WebSocket endpoint for real-time writing session monitoring
    Usage: ws://localhost:8000/api/v1/ws/writing-session?user_id=1&session_id=123
    """

    await websocket.accept()

    user = None
    monitor = None
    db = None

    try:
        # Simple authentication via query params
        if not user_id:
            await websocket.send_json({'error': 'user_id required in query params'})
            await websocket.close()
            return

        # Get database session
        db = next(get_db())

        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await websocket.send_json({'error': 'User not found'})
            await websocket.close()
            return

        # Store connection
        active_sessions[user.id] = websocket

        # Initialize session monitor
        monitor = SessionMonitor(user, session_id or 0, db)
        session_data[user.id] = {
            'monitor': monitor,
            'started_at': datetime.now(timezone.utc)
        }

        logger.info(f"✅ WebSocket connected for user {user.id}")

        # Send confirmation
        await websocket.send_json({
            'type': 'connection_established',
            'message': 'AI coach is now monitoring your session',
            'user_id': user.id
        })

        # Start background inactivity checker
        inactivity_task = asyncio.create_task(check_inactivity_loop(user.id, websocket, monitor))

        # Main event loop
        while True:
            try:
                # Receive keystroke event
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=1.0  # 1 second timeout to allow inactivity checks
                )

                # Process event
                intervention = await monitor.process_keystroke(data)

                if intervention:
                    await websocket.send_json(intervention)

                # Check for milestones
                milestone = await monitor.check_milestones()
                if milestone:
                    await websocket.send_json(milestone)

            except asyncio.TimeoutError:
                # No data received, continue (allows inactivity checks to run)
                continue

            except WebSocketDisconnect:
                raise

            except Exception as e:
                logger.error(f"Error processing event: {str(e)}")
                continue

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.id if user else 'unknown'}")

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")

    finally:
        # Cleanup
        if user and user.id in active_sessions:
            active_sessions.pop(user.id)
            session_data.pop(user.id, None)

        if monitor:
            logger.info(f"Session stats for user {user.id}: {monitor.interventions_sent} interventions sent, {monitor.word_count} words")

        if db:
            db.close()

        try:
            await websocket.close()
        except:
            pass


async def check_inactivity_loop(user_id: int, websocket: WebSocket, monitor: SessionMonitor):
    """Background task to check for inactivity"""
    try:
        while user_id in active_sessions:
            await asyncio.sleep(30)  # Check every 30 seconds

            intervention = await monitor.check_inactivity()
            if intervention:
                try:
                    await websocket.send_json(intervention)
                except:
                    break
    except Exception as e:
        logger.error(f"Inactivity checker error for user {user_id}: {str(e)}")


async def push_message_to_user(user_id: int, message: dict) -> bool:
    """
    Push a message to user if they have an active WebSocket connection
    Used by background tasks to send proactive messages
    """
    if user_id in active_sessions:
        try:
            websocket = active_sessions[user_id]
            await websocket.send_json(message)
            logger.info(f"📤 Pushed message to user {user_id} via WebSocket")
            return True
        except Exception as e:
            logger.error(f"Failed to push message to user {user_id}: {str(e)}")
            return False
    return False


@router.get("/active-sessions")
async def get_active_sessions():
    """Debug endpoint to see active WebSocket sessions"""
    return {
        "active_sessions": list(active_sessions.keys()),
        "total": len(active_sessions)
    }
