# app/models/post.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Post(Base):
    """Community posts - limited to one per day after meeting daily goal."""
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    excerpt = Column(String(500))  # First 500 chars for preview

    word_count = Column(Integer, default=0)

    # Metadata
    is_published = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)  # For highlighting great posts

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="posts")
    reactions = relationship("Reaction", back_populates="post", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Post {self.id}: {self.title[:30]}>"
