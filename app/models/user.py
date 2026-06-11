# app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Date
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)

    is_active = Column(Boolean, default=True)
    is_qualified = Column(Boolean, default=False)

    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    total_words = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    last_write_date = Column(DateTime(timezone=True))

    # ✅ NEW: Daily goal tracking
    daily_goal_words = Column(Integer, default=250)  # Customizable goal
    today_words = Column(Integer, default=0)  # Words written today
    today_goal_met = Column(Boolean, default=False)  # Unlocks sharing
    last_goal_check_date = Column(Date)  # Reset counter daily
    can_share_today = Column(Boolean, default=False)  # Explicit sharing permission

    timezone = Column(String, default="UTC")
    reminder_time = Column(String)

    user_metadata = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
