# app/models/reaction.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Reaction(Base):
    """Simple reactions to posts - one per user per post."""
    __tablename__ = "reactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)

    # Reaction types: "fire" (🔥), "clap" (👏), "heart" (❤️)
    reaction_type = Column(String(20), nullable=False, default="fire")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # One reaction per user per post
    __table_args__ = (
        UniqueConstraint('user_id', 'post_id', name='unique_user_post_reaction'),
    )

    # Relationships
    user = relationship("User")
    post = relationship("Post", back_populates="reactions")

    def __repr__(self):
        return f"<Reaction {self.reaction_type} by User {self.user_id} on Post {self.post_id}>"
