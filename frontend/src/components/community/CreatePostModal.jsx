import React, { useState, useEffect } from "react";
import { createPost } from "../../services/api";

const CreatePostModal = ({
  isOpen,
  onClose,
  onPostCreated,
  canPost,
  initialContent = "", // ← NEW
  initialWordCount = 0, // ← NEW
}) => {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  // ← NEW: Pre-fill content when modal opens
  useEffect(() => {
    if (isOpen && initialContent) {
      setContent(initialContent);
    }
  }, [isOpen, initialContent]);

  const wordCount = content.trim().split(/\s+/).filter(Boolean).length;
  const minWords = 250;
  const isValidLength = wordCount >= minWords;

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!isValidLength) {
      setError(
        `Your post must be at least ${minWords} words. Current: ${wordCount} words.`,
      );
      return;
    }

    if (!title.trim()) {
      setError("Please enter a title for your post.");
      return;
    }

    setIsSubmitting(true);
    setError("");

    try {
      const newPost = await createPost({ title, content });
      onPostCreated(newPost);
      setTitle("");
      setContent("");
    } catch (err) {
      setError(
        err.response?.data?.error || "Failed to create post. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setTitle("");
      setContent("");
      setError("");
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">
            Share Your Writing
          </h2>
          <button
            onClick={handleClose}
            disabled={isSubmitting}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <form
          onSubmit={handleSubmit}
          className="overflow-y-auto max-h-[calc(90vh-8rem)]"
        >
          <div className="px-6 py-6 space-y-4">
            {!canPost.can_post && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-sm text-yellow-800">⚠️ {canPost.message}</p>
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Title
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Give your writing a title..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isSubmitting}
                maxLength={200}
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-semibold text-gray-700">
                  Your Writing
                </label>
                <span
                  className={`text-sm font-medium ${
                    isValidLength ? "text-green-600" : "text-gray-500"
                  }`}
                >
                  {wordCount} / {minWords} words
                </span>
              </div>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Share what you wrote today..."
                rows={12}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-serif resize-none"
                disabled={isSubmitting}
              />
              {!isValidLength && wordCount > 0 && (
                <p className="text-sm text-gray-500 mt-2">
                  You need {minWords - wordCount} more words to share your post.
                </p>
              )}
            </div>
          </div>

          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={handleClose}
              disabled={isSubmitting}
              className="px-6 py-3 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={
                isSubmitting ||
                !isValidLength ||
                !title.trim() ||
                !canPost.can_post
              }
              className="px-6 py-3 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? "Sharing..." : "Share Post"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreatePostModal;
