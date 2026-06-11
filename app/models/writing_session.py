from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB  # ← Add this import
from sqlalchemy.sql import func
from app.core.database import Base


class WritingSession(Base):
    __tablename__ = "writing_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    content = Column(Text, default="")
    word_count = Column(Integer, default=0)
    duration_minutes = Column(Integer)

    # Session metadata
    session_type = Column(String)  # 'timed', 'sprint', 'focus'
    goal_met = Column(Boolean, default=False)

    topic = Column(String)
    prompt_id = Column(Integer, ForeignKey("topic_prompts.id"))

    ai_feedback = Column(JSONB)  # ← Changed from JSON to JSONB
    sentiment_score = Column(Integer)

    session_metadata = Column(JSONB)  # ← ADD THIS LINE

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
