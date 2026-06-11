from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.ml_integration_service import MLIntegrationService
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()

ml_service = MLIntegrationService()


class UserResponseRequest(BaseModel):
    personality: str
    response_type: str
    time_to_action: Optional[float] = None


@router.get("/insights")
async def get_ml_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Get complete ML insights for current user."""
    try:
        insights = ml_service.get_complete_insights(db, current_user)
        return {
            "success": True,
            "data": insights
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/coaching-message")
async def get_coaching_message(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Generate personalized coaching message."""
    try:
        coaching = ml_service.generate_coaching_message(db, current_user)
        return {
            "success": True,
            "data": coaching
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/record-response")
async def record_user_response(
    request: UserResponseRequest,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Record user's response to coaching message."""
    try:
        ml_service.record_user_response(
            personality=request.personality,
            response_type=request.response_type,
            time_to_action=request.time_to_action
        )
        return {
            "success": True,
            "message": "Response recorded"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/personality-stats")
async def get_personality_stats(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Get performance statistics for all coaching personalities."""
    try:
        stats = ml_service.personality_engine.get_performance_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
