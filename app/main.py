from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import auth, users, writing, analytics, ai_insights, notifications, experiments, ai_coach, websocket, community
from app.tasks.scheduler import setup_scheduler, start_scheduler, shutdown_scheduler

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting WriteCircle API...")

    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")

    # Setup and start scheduler (includes proactive AI monitoring)
    setup_scheduler()
    start_scheduler()
    logger.info("Background task scheduler started")

    logger.info("✅ All systems operational!")

    yield

    # Shutdown
    logger.info("🛑 Shutting down WriteCircle API...")
    shutdown_scheduler()
    logger.info("✅ Shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Writing Coach Platform with Proactive Interventions",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(writing.router, prefix=f"{settings.API_V1_STR}/writing", tags=["Writing"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["Analytics"])
app.include_router(ai_insights.router, prefix=f"{settings.API_V1_STR}/ai-insights", tags=["AI Insights"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["Notifications"])
app.include_router(experiments.router, prefix=f"{settings.API_V1_STR}/experiments", tags=["Experiments"])
app.include_router(ai_coach.router, prefix=f"{settings.API_V1_STR}/ai-coach", tags=["AI Coach"])
app.include_router(community.router, prefix=f"{settings.API_V1_STR}/community", tags=["Community"])



# WebSocket router for real-time writing session monitoring
app.include_router(
    websocket.router,
    prefix=f"{settings.API_V1_STR}",
    tags=["WebSocket"]
)


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "features": {
            "proactive_ai": "enabled",
            "websocket_coaching": "enabled",
            "background_monitoring": "enabled"
        }
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "proactive_ai": "operational"
    }
