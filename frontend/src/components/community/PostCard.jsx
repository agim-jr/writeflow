import React, { useState } from "react";
import { Heart, Trash2 } from "lucide-react";
import { addReaction, removeReaction, deletePost } from "../../services/api";
import { useAuth } from "../../context/AuthContext";

const PostCard = ({ post, onPostDeleted }) => {
  const { user } = useAuth();
  const [isDeleting, setIsDeleting] = useState(false);
  const [localReactionCount, setLocalReactionCount] = useState(
    post.reaction_count || 0,
  );
  const [localUserReacted, setLocalUserReacted] = useState(
    post.user_reacted || false,
  );
  const [isReacting, setIsReacting] = useState(false);

  const isAuthor = user && user.id === post.author.id;

  const handleReaction = async () => {
    if (isReacting) return;

    setIsReacting(true);

    try {
      if (localUserReacted) {
        // Remove reaction
        await removeReaction(post.id);
        setLocalReactionCount((prev) => prev - 1);
        setLocalUserReacted(false);
      } else {
        // Add reaction (heart/like)
        await addReaction(post.id, "like");
        setLocalReactionCount((prev) => prev + 1);
        setLocalUserReacted(true);
      }
    } catch (error) {
      console.error("Failed to toggle reaction:", error);
    } finally {
      setIsReacting(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm("Are you sure you want to delete this post?")) {
      return;
    }

    setIsDeleting(true);
    try {
      await deletePost(post.id);
      onPostDeleted(post.id);
    } catch (error) {
      console.error("Failed to delete post:", error);
      alert("Failed to delete post. Please try again.");
    } finally {
      setIsDeleting(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));

    if (diffInHours < 1) {
      return "Just now";
    } else if (diffInHours < 24) {
      return `${diffInHours}h ago`;
    } else {
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
      });
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900 mb-1">{post.title}</h3>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span className="font-medium">{post.author.username}</span>
            {post.author.current_streak > 0 && (
              <span className="text-orange-600 font-semibold">
                🔥 {post.author.current_streak} day streak
              </span>
            )}
            <span>•</span>
            <span>{formatDate(post.created_at)}</span>
          </div>
        </div>

        {isAuthor && (
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="text-gray-400 hover:text-red-600 transition-colors p-2 rounded-lg hover:bg-red-50"
            title="Delete post"
          >
            <Trash2 size={18} />
          </button>
        )}
      </div>

      {/* Content */}
      <div className="prose prose-sm max-w-none mb-4">
        <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
          {post.content}
        </p>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
        <button
          onClick={handleReaction}
          disabled={isReacting}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
            localUserReacted
              ? "text-red-600 bg-red-50 hover:bg-red-100"
              : "text-gray-600 hover:text-red-600 hover:bg-red-50"
          }`}
        >
          <Heart size={20} className={localUserReacted ? "fill-current" : ""} />
          <span className="font-medium">
            {localReactionCount} {localReactionCount === 1 ? "like" : "likes"}
          </span>
        </button>

        <div className="text-sm text-gray-500">
          {post.content.split(/\s+/).filter(Boolean).length} words
        </div>
      </div>
    </div>
  );
};

export default PostCard;
