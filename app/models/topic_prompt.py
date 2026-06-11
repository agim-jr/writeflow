from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class TopicPrompt(Base):
    __tablename__ = "topic_prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    title = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    difficulty = Column(String)  # beginner, intermediate, advanced
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
