from fastapi import APIRouter
from app.api.v1 import (
    auth,
    users,
    writing,
    analytics,
    ai_coach,
    ai_insights,
    experiments,
    milestones,
    notifications,
    community,
    ml  # Add this
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(writing.router, prefix="/writing", tags=["writing"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(ai_coach.router, prefix="/ai-coach", tags=["ai-coach"])
api_router.include_router(ai_insights.router, prefix="/ai-insights", tags=["ai-insights"])
api_router.include_router(experiments.router, prefix="/experiments", tags=["experiments"])
api_router.include_router(milestones.router, prefix="/milestones", tags=["milestones"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(community.router, prefix="/community", tags=["community"])
api_router.include_router(ml.router, prefix="/ml", tags=["ml"])  # Add this
