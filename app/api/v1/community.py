# app/api/v1/community.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.post import Post
from app.schemas.post import (
    PostCreate, PostUpdate, PostResponse,
    ReactionCreate, ReactionResponse
)
from app.services.post_service import PostService

router = APIRouter()


@router.get("/can-post")
async def check_can_post(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if user can post today."""
    return PostService.can_user_post_today(db, current_user)


@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new post (one per day after meeting daily goal)."""
    post = PostService.create_post(db, current_user, post_data)

    # Build response with engagement data
    return {
        **post.__dict__,
        "author": {
            "id": current_user.id,
            "username": current_user.username,
            "current_streak": current_user.current_streak
        },
        "reaction_count": 0,
        "user_reacted": False,
        "user_reaction_type": None
    }


@router.get("/posts", response_model=List[PostResponse])
async def get_feed(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get community feed."""
    return PostService.get_feed(db, current_user, skip, limit)


@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific post."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # Get engagement data
    feed = PostService.get_feed(db, current_user, skip=0, limit=1)
    # Filter to just this post
    post_data = next((p for p in feed if p["id"] == post_id), None)

    if not post_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    return post_data


@router.put("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    post_data: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a post (only author can update)."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this post"
        )

    updated_post = PostService.update_post(db, post, post_data)

    # Build response
    feed = PostService.get_feed(db, current_user, skip=0, limit=1)
    post_data = next((p for p in feed if p["id"] == post_id), None)

    return post_data


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a post (only author can delete)."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this post"
        )

    PostService.delete_post(db, post)


@router.post("/posts/{post_id}/react", response_model=ReactionResponse)
async def add_reaction(
    post_id: int,
    reaction_data: ReactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add or update a reaction to a post."""
    return PostService.add_reaction(
        db, post_id, current_user, reaction_data.reaction_type
    )


@router.delete("/posts/{post_id}/react", status_code=status.HTTP_204_NO_CONTENT)
async def remove_reaction(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove your reaction from a post."""
    PostService.remove_reaction(db, post_id, current_user)


@router.get("/my-posts", response_model=List[PostResponse])
async def get_my_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's posts."""
    posts = PostService.get_user_posts(db, current_user.id, skip, limit)

    # Convert to response format
    result = []
    for post in posts:
        feed_item = PostService.get_feed(db, current_user, skip=0, limit=1)
        post_data = next((p for p in feed_item if p["id"] == post.id), None)
        if post_data:
            result.append(post_data)

    return result
