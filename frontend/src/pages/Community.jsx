import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Users,
  Sparkles,
  LogOut,
  BarChart3,
  Lock,
  Unlock,
  Share2,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { getPosts, canPostToday } from "../services/api";
import CreatePostModal from "../components/community/CreatePostModal";
import PostCard from "../components/community/PostCard";

// Add Space Mono font
const loadFont = () => {
  if (!document.querySelector('link[href*="Space+Mono"]')) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href =
      "https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap";
    document.head.appendChild(link);
  }
};

const fontStyle = `
  .font-mono {
    font-family: 'Space Mono', monospace !important;
  }
`;

const Community = () => {
  const { user, logout } = useAuth();
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [canPost, setCanPost] = useState({ can_post: false, message: "" });

  useEffect(() => {
    loadFont();

    if (!document.querySelector("#space-mono-style")) {
      const style = document.createElement("style");
      style.id = "space-mono-style";
      style.textContent = fontStyle;
      document.head.appendChild(style);
    }

    loadPosts();
    checkCanPost();
  }, []);

  const loadPosts = async () => {
    try {
      const data = await getPosts();
      setPosts(data);
    } catch (error) {
      console.error("Failed to load posts:", error);
    } finally {
      setLoading(false);
    }
  };

  const checkCanPost = async () => {
    try {
      const data = await canPostToday();
      setCanPost(data);
    } catch (error) {
      console.error("Failed to check post permission:", error);
    }
  };

  const handlePostCreated = (newPost) => {
    setPosts([newPost, ...posts]);
    setCanPost({ can_post: false, message: "You've already shared today!" });
    setShowCreateModal(false);
  };

  const handlePostDeleted = (postId) => {
    setPosts(posts.filter((post) => post.id !== postId));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center font-mono">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 border-4 border-black border-t-transparent rounded-full animate-spin mx-auto"></div>
          <div className="text-xl font-bold text-gray-900">
            Loading Community...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 font-mono">
      {/* Header - Same as Dashboard and Analytics */}
      <header className="bg-white border-b-2 border-gray-300 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link to="/dashboard" className="flex items-center gap-3">
              <div className="w-10 h-10 bg-yellow-400 rounded-lg border-2 border-black flex items-center justify-center transform rotate-3">
                <Sparkles size={20} className="text-black" />
              </div>
              <span className="text-xl font-bold text-gray-900">
                ProjectWriter
              </span>
            </Link>

            {/* Navigation */}
            <nav className="hidden md:flex items-center gap-1">
              <Link
                to="/dashboard"
                className="px-4 py-2 text-sm font-bold text-gray-600 hover:text-black hover:bg-gray-100 rounded-lg transition-all"
              >
                Dashboard
              </Link>
              <Link
                to="/analytics"
                className="px-4 py-2 text-sm font-bold text-gray-600 hover:text-black hover:bg-gray-100 rounded-lg transition-all"
              >
                <BarChart3 size={16} className="inline mr-2" />
                Analytics
              </Link>
              <Link
                to="/community"
                className="px-4 py-2 text-sm font-bold text-black bg-gray-100 rounded-lg"
              >
                <Users size={16} className="inline mr-2" />
                Community
              </Link>
            </nav>

            {/* User Menu */}
            <div className="flex items-center gap-3">
              <button
                onClick={logout}
                className="hidden md:flex items-center gap-2 px-4 py-2 text-sm font-bold text-gray-600 hover:text-black hover:bg-gray-100 rounded-lg transition-all"
              >
                <LogOut size={16} />
                Logout
              </button>
              <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center">
                <span className="text-white text-sm font-bold">
                  {user?.username?.substring(0, 2).toUpperCase() || "U"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 space-y-8">
        {/* Page Header */}
        <section className="space-y-4">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-2">
                Community
              </h1>
              <p className="text-lg text-gray-600 font-bold">
                Share your daily writing and connect with other writers
              </p>
            </div>

            <button
              onClick={() => setShowCreateModal(true)}
              disabled={!canPost.can_post}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold border-2 transition-all ${
                canPost.can_post
                  ? "bg-black text-white border-black hover:bg-gray-800 hover:shadow-lg"
                  : "bg-gray-100 text-gray-400 border-gray-300 cursor-not-allowed"
              }`}
            >
              {canPost.can_post ? (
                <>
                  <Share2 size={18} />
                  Share Today's Writing
                </>
              ) : (
                <>
                  <Lock size={18} />
                  Already Shared Today
                </>
              )}
            </button>
          </div>

          {/* Status Banner */}
          {!canPost.can_post && canPost.message && (
            <div className="bg-blue-50 border-2 border-blue-300 rounded-xl p-4 flex items-start gap-3">
              <div className="w-6 h-6 bg-blue-100 rounded-lg border-2 border-blue-300 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Lock className="w-4 h-4 text-blue-600" />
              </div>
              <p className="text-sm text-blue-900 font-bold">
                {canPost.message}
              </p>
            </div>
          )}

          {canPost.can_post && (
            <div className="bg-green-50 border-2 border-green-300 rounded-xl p-4 flex items-start gap-3">
              <div className="w-6 h-6 bg-green-100 rounded-lg border-2 border-green-300 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Unlock className="w-4 h-4 text-green-600" />
              </div>
              <p className="text-sm text-green-900 font-bold">
                You've hit your daily goal! Sharing is now unlocked. Share your
                progress with the community.
              </p>
            </div>
          )}
        </section>

        {/* Posts */}
        <section>
          {posts.length === 0 ? (
            <div className="bg-white rounded-xl border-2 border-gray-300 p-12 text-center space-y-4 hover:border-black hover:shadow-lg transition-all">
              <div className="text-6xl mb-4">📝</div>
              <h3 className="text-2xl font-bold text-gray-900">No posts yet</h3>
              <p className="text-gray-600 font-bold max-w-md mx-auto">
                Be the first to share your writing with the community!
              </p>
              {canPost.can_post && (
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="inline-flex items-center gap-2 px-8 py-4 bg-black text-white rounded-xl font-bold border-2 border-black hover:bg-gray-800 hover:shadow-lg transition-all mt-4"
                >
                  <Share2 size={20} />
                  Share Your Writing
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-6">
              {posts.map((post) => (
                <PostCard
                  key={post.id}
                  post={post}
                  onDelete={handlePostDeleted}
                />
              ))}
            </div>
          )}
        </section>
      </main>

      <CreatePostModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onPostCreated={handlePostCreated}
        canPost={canPost}
      />
    </div>
  );
};

export default Community;
