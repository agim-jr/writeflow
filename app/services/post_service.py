# app/services/post_service.py
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from fastapi import HTTPException, status

from app.models.user import User
from app.models.post import Post
from app.models.reaction import Reaction
from app.schemas.post import PostCreate, PostUpdate


class PostService:

    @staticmethod
    def can_user_post_today(db: Session, user: User) -> Dict:
        """Check if user can post today."""
        # Must meet daily writing goal
        if not user.can_share_today:
            return {
                "can_post": False,
                "reason": "complete_daily_goal",
                "message": f"Write {user.daily_goal_words - user.today_words} more words to unlock sharing"
            }

        # Check if already posted today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        existing_post = db.query(Post).filter(
            and_(
                Post.user_id == user.id,
                Post.created_at >= today_start
            )
        ).first()

        if existing_post:
            return {
                "can_post": False,
                "reason": "already_posted",
                "message": "You've already shared today. Come back tomorrow!"
            }

        return {
            "can_post": True,
            "reason": None,
            "message": "You can post!"
        }

    @staticmethod
    def create_post(
        db: Session,
        user: User,
        post_data: PostCreate
    ) -> Post:
        """Create a new post."""
        # Check if user can post
        permission = PostService.can_user_post_today(db, user)
        if not permission["can_post"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=permission["message"]
            )

        # Calculate word count and excerpt
        word_count = len(post_data.content.split())
        excerpt = post_data.content[:500] + "..." if len(post_data.content) > 500 else post_data.content

        # Create post
        post = Post(
            user_id=user.id,
            title=post_data.title,
            content=post_data.content,
            excerpt=excerpt,
            word_count=word_count,
            is_published=True
        )

        db.add(post)
        db.commit()
        db.refresh(post)

        return post

    @staticmethod
    def update_post(
        db: Session,
        post: Post,
        post_data: PostUpdate
    ) -> Post:
        """Update an existing post."""
        if post_data.title is not None:
            post.title = post_data.title

        if post_data.content is not None:
            post.content = post_data.content
            post.word_count = len(post_data.content.split())
            post.excerpt = post_data.content[:500] + "..." if len(post_data.content) > 500 else post_data.content

        if post_data.is_published is not None:
            post.is_published = post_data.is_published

        db.commit()
        db.refresh(post)

        return post

    @staticmethod
    def delete_post(db: Session, post: Post):
        """Delete a post."""
        db.delete(post)
        db.commit()

    @staticmethod
    def get_feed(
        db: Session,
        current_user: Optional[User] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict]:
        """Get community feed with engagement data."""
        # Get published posts
        posts_query = db.query(Post).filter(
            Post.is_published == True
        ).order_by(desc(Post.created_at))

        posts = posts_query.offset(skip).limit(limit).all()

        # Build response with engagement
        feed = []
        for post in posts:
            # Count reactions
            reaction_count = db.query(func.count(Reaction.id)).filter(
                Reaction.post_id == post.id
            ).scalar() or 0

            # Check if current user reacted
            user_reaction = None
            if current_user:
                user_reaction = db.query(Reaction).filter(
                    and_(
                        Reaction.post_id == post.id,
                        Reaction.user_id == current_user.id
                    )
                ).first()

            feed.append({
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "excerpt": post.excerpt,
                "word_count": post.word_count,
                "is_featured": post.is_featured,
                "created_at": post.created_at,
                "updated_at": post.updated_at,
                "author": {
                    "id": post.user.id,
                    "username": post.user.username,
                    "current_streak": post.user.current_streak
                },
                "reaction_count": reaction_count,
                "user_reacted": user_reaction is not None,
                "user_reaction_type": user_reaction.reaction_type if user_reaction else None
            })

        return feed

    @staticmethod
    def get_user_posts(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[Post]:
        """Get posts by a specific user."""
        return db.query(Post).filter(
            Post.user_id == user_id
        ).order_by(desc(Post.created_at)).offset(skip).limit(limit).all()

    @staticmethod
    def add_reaction(
        db: Session,
        post_id: int,
        user: User,
        reaction_type: str
    ) -> Reaction:
        """Add or update a reaction to a post."""
        # Check if post exists
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )

        # Can't react to own post
        if post.user_id == user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot react to your own post"
            )

        # Check if already reacted
        existing_reaction = db.query(Reaction).filter(
            and_(
                Reaction.post_id == post_id,
                Reaction.user_id == user.id
            )
        ).first()

        if existing_reaction:
            # Update reaction type
            existing_reaction.reaction_type = reaction_type
            db.commit()
            db.refresh(existing_reaction)
            return existing_reaction

        # Create new reaction
        reaction = Reaction(
            user_id=user.id,
            post_id=post_id,
            reaction_type=reaction_type
        )

        db.add(reaction)
        db.commit()
        db.refresh(reaction)

        return reaction

    @staticmethod
    def remove_reaction(
        db: Session,
        post_id: int,
        user: User
    ):
        """Remove a reaction from a post."""
        reaction = db.query(Reaction).filter(
            and_(
                Reaction.post_id == post_id,
                Reaction.user_id == user.id
            )
        ).first()

        if reaction:
            db.delete(reaction)
            db.commit()
