import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Flame,
  BookOpen,
  Clock,
  Zap,
  Target,
  TrendingUp,
  Sparkles,
  Lock,
  Unlock,
  LogOut,
  BarChart3,
  ArrowRight,
  CheckCircle,
  Share2,
  Users,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";

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

// Add custom styles for Space Mono
const fontStyle = `
  .font-mono {
    font-family: 'Space Mono', monospace !important;
  }
`;

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [dailyProgress, setDailyProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    // Load the font
    loadFont();

    // Add style tag for font
    if (!document.querySelector("#space-mono-style")) {
      const style = document.createElement("style");
      style.id = "space-mono-style";
      style.textContent = fontStyle;
      document.head.appendChild(style);
    }

    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [overviewResponse, progressResponse] = await Promise.all([
        api.get("/analytics/overview"),
        api.get("/analytics/daily-progress"),
      ]);

      console.log("📊 Dashboard data:", overviewResponse.data);
      console.log("📈 Daily progress:", progressResponse.data);

      // Map the API response to what the UI expects
      const userData = overviewResponse.data.user;
      const perfData = overviewResponse.data.performance;

      setStats({
        current_streak: userData?.current_streak || 0,
        longest_streak: userData?.longest_streak || 0,
        total_words: userData?.total_words || 0,
        total_sessions: userData?.total_sessions || 0,
        average_session_duration: perfData?.time?.average_session_minutes || 0,
      });

      setDailyProgress(progressResponse.data);
    } catch (err) {
      setError("Failed to load dashboard data");
      console.error("Dashboard error:", err);
      console.error("Error details:", err.response?.data);
    } finally {
      setLoading(false);
    }
  };

  const startWriting = (mode) => {
    navigate("/write", { state: { mode } });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center font-mono">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 border-4 border-black border-t-transparent rounded-full animate-spin mx-auto"></div>
          <div className="text-xl font-bold text-gray-900">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 font-mono">
      {/* Header */}
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
            {/* Navigation */}
            <nav className="hidden md:flex items-center gap-1">
              <Link
                to="/dashboard"
                className="px-4 py-2 text-sm font-bold text-black bg-gray-100 rounded-lg"
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
                className="px-4 py-2 text-sm font-bold text-gray-600 hover:text-black hover:bg-gray-100 rounded-lg transition-all"
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
        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border-2 border-red-300 rounded-xl p-4">
            <p className="text-red-800 font-bold text-sm">{error}</p>
          </div>
        )}

        {/* Welcome Section */}
        <section className="space-y-2">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900">
            Welcome back, {user?.username}
          </h1>
          <p className="text-lg text-gray-600 font-bold">
            Ready to write today?
          </p>
        </section>

        {/* Daily Goal Progress Card */}
        {dailyProgress && (
          <section className="bg-white rounded-xl border-2 border-gray-300 p-6 hover:border-black hover:shadow-lg transition-all">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
              <div className="flex items-center gap-3">
                <div
                  className={`w-12 h-12 rounded-lg border-2 flex items-center justify-center ${
                    dailyProgress.goal_met
                      ? "bg-green-100 border-green-300"
                      : "bg-blue-100 border-blue-300"
                  }`}
                >
                  {dailyProgress.goal_met ? (
                    <CheckCircle className="w-6 h-6 text-green-600" />
                  ) : (
                    <Target className="w-6 h-6 text-blue-600" />
                  )}
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900">
                    {dailyProgress.goal_met
                      ? "Today's Goal Complete! 🎉"
                      : "Today's Writing Goal"}
                  </h3>
                  <p className="text-sm text-gray-600 font-bold">
                    {dailyProgress.today_words.toLocaleString()} /{" "}
                    {dailyProgress.daily_goal.toLocaleString()} words
                  </p>
                </div>
              </div>

              {/* Sharing Status */}
              <div
                className={`flex items-center gap-2 px-4 py-2 rounded-lg border-2 ${
                  dailyProgress.can_share
                    ? "bg-green-50 border-green-300"
                    : "bg-gray-50 border-gray-300"
                }`}
              >
                {dailyProgress.can_share ? (
                  <>
                    <Unlock className="w-5 h-5 text-green-600" />
                    <span className="text-sm font-bold text-green-700">
                      Sharing Unlocked
                    </span>
                  </>
                ) : (
                  <>
                    <Lock className="w-5 h-5 text-gray-500" />
                    <span className="text-sm font-bold text-gray-600">
                      Complete goal to share
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* Progress Bar */}
            <div className="relative h-3 bg-gray-200 rounded-full overflow-hidden mb-4">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  dailyProgress.goal_met
                    ? "bg-gradient-to-r from-green-500 to-emerald-500"
                    : "bg-gradient-to-r from-blue-500 to-purple-500"
                }`}
                style={{ width: `${dailyProgress.progress_percent}%` }}
              />
            </div>

            {/* Call to Action */}
            {!dailyProgress.goal_met && (
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <p className="text-sm text-gray-600 font-bold">
                  {(
                    dailyProgress.daily_goal - dailyProgress.today_words
                  ).toLocaleString()}{" "}
                  words to unlock community sharing
                </p>
                <button
                  onClick={() => startWriting("timed")}
                  className="flex items-center justify-center gap-2 px-4 py-2 bg-black text-white rounded-lg font-bold hover:bg-gray-800 transition-all"
                >
                  Start Writing
                  <ArrowRight size={16} />
                </button>
              </div>
            )}

            {dailyProgress.goal_met && dailyProgress.can_share && (
              <div className="flex justify-end">
                <button
                  onClick={() => navigate("/community")}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg font-bold hover:bg-green-700 transition-all"
                >
                  <Share2 size={16} />
                  Share Today's Writing
                </button>
              </div>
            )}
          </section>
        )}

        {/* Stats Grid */}
        <section className="grid md:grid-cols-3 gap-6">
          {/* Current Streak */}
          <div className="bg-white rounded-xl border-2 border-gray-300 p-6 hover:border-black hover:shadow-lg transition-all">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-orange-100 rounded-lg border-2 border-orange-300 flex items-center justify-center">
                <Flame className="w-6 h-6 text-orange-600" />
              </div>
              <span className="text-xs text-gray-500 font-bold uppercase tracking-wide">
                Current Streak
              </span>
            </div>
            <div className="text-5xl font-bold text-gray-900 mb-2">
              {stats?.current_streak || 0}
            </div>
            <p className="text-sm text-gray-600 font-bold">
              {stats?.current_streak === 1 ? "day" : "days"} in a row
            </p>
          </div>

          {/* Total Words */}
          <div className="bg-white rounded-xl border-2 border-gray-300 p-6 hover:border-black hover:shadow-lg transition-all">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-blue-100 rounded-lg border-2 border-blue-300 flex items-center justify-center">
                <BookOpen className="w-6 h-6 text-blue-600" />
              </div>
              <span className="text-xs text-gray-500 font-bold uppercase tracking-wide">
                Total Words
              </span>
            </div>
            <div className="text-5xl font-bold text-gray-900 mb-2">
              {stats?.total_words?.toLocaleString() || 0}
            </div>
            <p className="text-sm text-gray-600 font-bold">
              across {stats?.total_sessions || 0} sessions
            </p>
          </div>

          {/* Average Session */}
          <div className="bg-white rounded-xl border-2 border-gray-300 p-6 hover:border-black hover:shadow-lg transition-all">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-green-100 rounded-lg border-2 border-green-300 flex items-center justify-center">
                <Clock className="w-6 h-6 text-green-600" />
              </div>
              <span className="text-xs text-gray-500 font-bold uppercase tracking-wide">
                Avg Session
              </span>
            </div>
            <div className="text-5xl font-bold text-gray-900 mb-2">
              {Math.round(stats?.average_session_duration || 0)}
            </div>
            <p className="text-sm text-gray-600 font-bold">
              minutes per session
            </p>
          </div>
        </section>

        {/* Writing Modes Section */}
        <section className="space-y-6">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              Start Writing
            </h2>
            <p className="text-gray-600 font-bold">
              Your AI coach will observe and nudge you automatically at key
              moments
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {/* Timed Session */}
            <button
              onClick={() => startWriting("timed")}
              className="group bg-white rounded-xl border-2 border-gray-300 p-8 text-left hover:border-blue-500 hover:shadow-lg transition-all"
            >
              <div className="space-y-4">
                <div className="w-16 h-16 bg-blue-100 rounded-xl border-2 border-blue-300 flex items-center justify-center group-hover:bg-blue-500 transition-all">
                  <Clock className="w-8 h-8 text-blue-600 group-hover:text-white transition-colors" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    Timed Session
                  </h3>
                  <p className="text-sm text-gray-600 font-bold leading-relaxed">
                    25-minute focused sprint with AI insights
                  </p>
                </div>
                <div className="flex items-center gap-2 text-blue-600 font-bold text-sm opacity-0 group-hover:opacity-100 transition-opacity">
                  Start writing
                  <ArrowRight size={16} />
                </div>
              </div>
            </button>

            {/* Word Sprint */}
            <button
              onClick={() => startWriting("sprint")}
              className="group bg-white rounded-xl border-2 border-gray-300 p-8 text-left hover:border-green-500 hover:shadow-lg transition-all"
            >
              <div className="space-y-4">
                <div className="w-16 h-16 bg-green-100 rounded-xl border-2 border-green-300 flex items-center justify-center group-hover:bg-green-500 transition-all">
                  <Zap className="w-8 h-8 text-green-600 group-hover:text-white transition-colors" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    Word Sprint
                  </h3>
                  <p className="text-sm text-gray-600 font-bold leading-relaxed">
                    Race to 500 words with milestone encouragement
                  </p>
                </div>
                <div className="flex items-center gap-2 text-green-600 font-bold text-sm opacity-0 group-hover:opacity-100 transition-opacity">
                  Start writing
                  <ArrowRight size={16} />
                </div>
              </div>
            </button>

            {/* Deep Focus */}
            <button
              onClick={() => startWriting("focus")}
              className="group bg-white rounded-xl border-2 border-gray-300 p-8 text-left hover:border-purple-500 hover:shadow-lg transition-all"
            >
              <div className="space-y-4">
                <div className="w-16 h-16 bg-purple-100 rounded-xl border-2 border-purple-300 flex items-center justify-center group-hover:bg-purple-500 transition-all">
                  <Target className="w-8 h-8 text-purple-600 group-hover:text-white transition-colors" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    Deep Focus
                  </h3>
                  <p className="text-sm text-gray-600 font-bold leading-relaxed">
                    45-minute deep work with stuck detection
                  </p>
                </div>
                <div className="flex items-center gap-2 text-purple-600 font-bold text-sm opacity-0 group-hover:opacity-100 transition-opacity">
                  Start writing
                  <ArrowRight size={16} />
                </div>
              </div>
            </button>
          </div>
        </section>

        {/* AI Coach Info */}
        <section className="bg-white rounded-xl border-2 border-gray-300 p-8">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-blue-100 rounded-lg border-2 border-blue-300 flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-6 h-6 text-blue-600" />
            </div>
            <div className="space-y-3">
              <h3 className="text-xl font-bold text-gray-900">
                How AI Coach Works
              </h3>
              <ul className="space-y-2 text-sm text-gray-600 font-bold">
                <li>• Observes your writing patterns silently</li>
                <li>• Surfaces insights at milestones (100, 250, 500 words)</li>
                <li>• Detects when you're stuck and nudges you forward</li>
                <li>• Celebrates wins automatically</li>
                <li>• No chat needed—just write</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Recent Activity */}
        {stats?.total_sessions > 0 && (
          <section className="space-y-4">
            <h3 className="text-2xl font-bold text-gray-900">
              Recent Activity
            </h3>
            <div className="bg-white rounded-xl border-2 border-gray-300 p-6 hover:border-black hover:shadow-lg transition-all">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-green-100 rounded-lg border-2 border-green-300 flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-green-600" />
                  </div>
                  <p className="text-sm text-gray-600 font-bold">
                    You've written{" "}
                    <span className="text-gray-900">
                      {stats.total_words.toLocaleString()}
                    </span>{" "}
                    words across{" "}
                    <span className="text-gray-900">
                      {stats.total_sessions}
                    </span>{" "}
                    sessions
                  </p>
                </div>
                <Link
                  to="/analytics"
                  className="flex items-center gap-2 text-sm font-bold text-black hover:gap-3 transition-all"
                >
                  View Analytics
                  <ArrowRight size={16} />
                </Link>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
