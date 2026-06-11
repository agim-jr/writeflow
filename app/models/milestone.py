from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class Milestone(Base):
    __tablename__ = "milestones"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    title = Column(String, nullable=False)
    description = Column(String)
    target_value = Column(Integer, nullable=False)
    current_value = Column(Integer, default=0)
    milestone_type = Column(String, nullable=False)  # streak, words, sessions, etc.
    
    is_achieved = Column(Boolean, default=False)
    achieved_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
