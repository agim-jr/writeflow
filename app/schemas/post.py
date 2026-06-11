# app/schemas/post.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class PostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)


class PostCreate(PostBase):
    """Create a new post."""
    pass

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

    @field_validator('content')
    @classmethod
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()


class PostUpdate(BaseModel):
    """Update an existing post."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    is_published: Optional[bool] = None


class PostAuthor(BaseModel):
    """Author information for posts."""
    id: int
    username: str
    current_streak: int

    class Config:
        from_attributes = True


class PostResponse(PostBase):
    """Post response with metadata."""
    id: int
    user_id: int
    excerpt: Optional[str]
    word_count: int
    is_published: bool
    is_featured: bool
    created_at: datetime
    updated_at: Optional[datetime]

    # Author info
    author: PostAuthor

    # Engagement
    reaction_count: int = 0
    user_reacted: bool = False
    user_reaction_type: Optional[str] = None

    class Config:
        from_attributes = True


class ReactionCreate(BaseModel):
    """Add a reaction to a post."""
    reaction_type: str = Field(..., pattern="^(fire|clap|heart)$")


class ReactionResponse(BaseModel):
    """Reaction response."""
    id: int
    user_id: int
    post_id: int
    reaction_type: str
    created_at: datetime

    class Config:
        from_attributes = True
