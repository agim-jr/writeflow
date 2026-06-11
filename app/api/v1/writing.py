from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.writing_session import WritingSession
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/save")
async def save_writing(
    writing_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save written content."""
    try:
        logger.info(f"Saving writing for user {current_user.id}")

        # Find the session if session_id provided, otherwise create new
        session_id = writing_data.get("session_id")

        if session_id:
            session = db.query(WritingSession).filter(
                WritingSession.id == session_id,
                WritingSession.user_id == current_user.id
            ).first()

            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

            # Update existing session with content
            session.content = writing_data.get("content", "")
            session.topic = writing_data.get("title", "")[:255]  # Use title as topic

        else:
            # Create new session
            session = WritingSession(
                user_id=current_user.id,
                content=writing_data.get("content", ""),
                word_count=writing_data.get("word_count", 0),
                topic=writing_data.get("title", "")[:255],
                session_type=writing_data.get("session_type")
            )
            db.add(session)

        db.commit()
        db.refresh(session)

        logger.info(f"✓ Writing saved to session {session.id}")

        return {
            "success": True,
            "session_id": session.id,
            "message": "Writing saved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving writing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save writing: {str(e)}")

@router.get("/")
async def get_user_writings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's saved writings."""
    try:
        sessions = db.query(WritingSession).filter(
            WritingSession.user_id == current_user.id
        ).order_by(WritingSession.created_at.desc()).limit(50).all()

        return {
            "writings": [
                {
                    "id": s.id,
                    "title": s.topic or "Untitled",
                    "content": s.content,
                    "word_count": s.word_count,
                    "created_at": s.created_at.isoformat() if s.created_at else None
                }
                for s in sessions
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching writings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch writings")
