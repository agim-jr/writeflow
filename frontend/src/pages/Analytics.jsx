import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  TrendingUp,
  Calendar,
  Clock,
  BookOpen,
  Target,
  Flame,
  Home,
  Sparkles,
  CheckCircle,
  Lock,
  Unlock,
  LogOut,
  BarChart3,
  Users,
} from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
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

const fontStyle = `
  .font-mono {
    font-family: 'Space Mono', monospace !important;
  }
`;

export default function Analytics() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [overview, setOverview] = useState(null);
  const [patterns, setPatterns] = useState(null);
  const [progress, setProgress] = useState(null);
  const [dailyProgress, setDailyProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState("week");

  useEffect(() => {
    loadFont();

    if (!document.querySelector("#space-mono-style")) {
      const style = document.createElement("style");
      style.id = "space-mono-style";
      style.textContent = fontStyle;
      document.head.appendChild(style);
    }

    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const [overviewRes, patternsRes, progressRes, dailyProgressRes] =
        await Promise.all([
          api.get("/analytics/overview"),
          api.get(
            `/analytics/writing-patterns?days=${timeRange === "week" ? 7 : 30}`,
          ),
          api.get(`/analytics/progress?days=${timeRange === "week" ? 7 : 30}`),
          api.get("/analytics/daily-progress"),
        ]);

      console.log("📊 Full Overview Response:", overviewRes.data);
      console.log("📊 Full Patterns Response:", patternsRes.data);
      console.log("📊 Full Progress Response:", progressRes.data);
      console.log("📊 Daily Progress Response:", dailyProgressRes.data);

      const userData = overviewRes.data.user;
      setOverview({
        current_streak: userData?.current_streak || 0,
        longest_streak: userData?.longest_streak || 0,
        total_words: userData?.total_words || 0,
        total_sessions: userData?.total_sessions || 0,
        average_session_duration:
          overviewRes.data.performance?.time?.average_session_minutes || 0,
      });

      setPatterns(patternsRes.data);
      setProgress(progressRes.data);
      setDailyProgress(dailyProgressRes.data);
    } catch (err) {
      console.error("Failed to fetch analytics:", err);
      console.error("Error details:", err.response?.data);
    } finally {
      setLoading(false);
    }
  };

  const formatTimeOfDay = (hour) => {
    const ampm = hour >= 12 ? "PM" : "AM";
    const displayHour = hour % 12 || 12;
    return `${displayHour}${ampm}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center font-mono">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 border-4 border-black border-t-transparent rounded-full animate-spin mx-auto"></div>
          <div className="text-xl font-bold text-gray-900">
            Loading Analytics...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 font-mono">
      {/* Header - Same as Dashboard */}
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
                className="px-4 py-2 text-sm font-bold text-gray-600 hover:text-black hover:bg-gray-100 rounded-lg transition-all"
              >
                Dashboard
              </Link>
              <Link
                to="/analytics"
                className="px-4 py-2 text-sm font-bold text-black bg-gray-100 rounded-lg"
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
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Analytics</h1>
            <p className="text-gray-600 font-bold">
              Track your writing patterns and progress
            </p>
          </div>

          <div className="flex gap-2 bg-white rounded-xl border-2 border-gray-300 p-1">
            <button
              onClick={() => setTimeRange("week")}
              className={`px-4 py-2 text-sm font-bold rounded-lg transition-all ${
                timeRange === "week"
                  ? "bg-black text-white shadow-md"
                  : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              Week
            </button>
            <button
              onClick={() => setTimeRange("month")}
              className={`px-4 py-2 text-sm font-bold rounded-lg transition-all ${
                timeRange === "month"
                  ? "bg-black text-white shadow-md"
                  : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              Month
            </button>
          </div>
        </div>

        {/* Today's Goal Progress */}
        {dailyProgress && (
          <div className="bg-white rounded-xl border-2 border-gray-300 p-6 space-y-4 hover:border-black hover:shadow-lg transition-all">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div
                  className={`w-10 h-10 rounded-lg border-2 flex items-center justify-center ${
                    dailyProgress.goal_met
                      ? "bg-green-100 border-green-300"
                      : "bg-blue-100 border-blue-300"
                  }`}
                >
                  {dailyProgress.goal_met ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <Target className="w-5 h-5 text-blue-600" />
                  )}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">
                    {dailyProgress.goal_met
                      ? "Today's Goal Complete!"
                      : "Today's Progress"}
                  </h3>
                  <p className="text-sm text-gray-600 font-bold">
                    {dailyProgress.today_words.toLocaleString()} /{" "}
                    {dailyProgress.daily_goal.toLocaleString()} words
                  </p>
                </div>
              </div>

              <div
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border-2 ${
                  dailyProgress.can_share
                    ? "bg-green-50 border-green-300"
                    : "bg-gray-50 border-gray-300"
                }`}
              >
                {dailyProgress.can_share ? (
                  <>
                    <Unlock className="w-4 h-4 text-green-600" />
                    <span className="text-xs font-bold text-green-700">
                      Can Share
                    </span>
                  </>
                ) : (
                  <>
                    <Lock className="w-4 h-4 text-gray-500" />
                    <span className="text-xs font-bold text-gray-600">
                      Locked
                    </span>
                  </>
                )}
              </div>
            </div>

            <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  dailyProgress.goal_met
                    ? "bg-gradient-to-r from-green-500 to-emerald-500"
                    : "bg-gradient-to-r from-blue-500 to-purple-500"
                }`}
                style={{ width: `${dailyProgress.progress_percent}%` }}
              />
            </div>
          </div>
        )}

        {/* Overview Stats */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border-2 border-gray-300 p-6 space-y-3 hover:border-black hover:shadow-lg transition-all">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-orange-100 rounded-lg border-2 border-orange-300 flex items-center justify-center">
                <Flame className="w-5 h-5 text-orange-600" />
              </div>
              <span className="text-xs font-bold uppercase text-gray-500 tracking-wide">
                Current Streak
              </span>
            </div>
            <div className="text-4xl font-bold text-gray-900">
              {overview?.current_streak || 0}
            </div>
            <div className="text-sm text-gray-600 font-bold">
              Best: {overview?.longest_streak || 0} days
            </div>
          </div>

          <div className="bg-white rounded-xl border-2 border-gray-300 p-6 space-y-3 hover:border-black hover:shadow-lg transition-all">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-blue-100 rounded-lg border-2 border-blue-300 flex items-center justify-center">
                <BookOpen className="w-5 h-5 text-blue-600" />
              </div>
              <span className="text-xs font-bold uppercase text-gray-500 tracking-wide">
                Total Words
              </span>
            </div>
            <div className="text-4xl font-bold text-gray-900">
              {overview?.total_words?.toLocaleString() || 0}
            </div>
            <div className="text-sm text-gray-600 font-bold">
              {overview?.total_sessions || 0} sessions
            </div>
          </div>

          <div className="bg-white rounded-xl border-2 border-gray-300 p-6 space-y-3 hover:border-black hover:shadow-lg transition-all">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-purple-100 rounded-lg border-2 border-purple-300 flex items-center justify-center">
                <Clock className="w-5 h-5 text-purple-600" />
              </div>
              <span className="text-xs font-bold uppercase text-gray-500 tracking-wide">
                This {timeRange === "week" ? "Week" : "Month"}
              </span>
            </div>
            <div className="text-4xl font-bold text-gray-900">
              {progress?.summary?.total_sessions || 0}
            </div>
            <div className="text-sm text-gray-600 font-bold">sessions</div>
          </div>

          <div className="bg-white rounded-xl border-2 border-gray-300 p-6 space-y-3 hover:border-black hover:shadow-lg transition-all">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-green-100 rounded-lg border-2 border-green-300 flex items-center justify-center">
                <Target className="w-5 h-5 text-green-600" />
              </div>
              <span className="text-xs font-bold uppercase text-gray-500 tracking-wide">
                This {timeRange === "week" ? "Week" : "Month"}
              </span>
            </div>
            <div className="text-4xl font-bold text-gray-900">
              {progress?.summary?.total_words?.toLocaleString() || 0}
            </div>
            <div className="text-sm text-gray-600 font-bold">words</div>
          </div>
        </div>

        {/* Daily Progress Chart */}
        {progress?.data && progress.data.length > 0 && (
          <div className="bg-white rounded-xl border-2 border-gray-300 p-6 md:p-8 space-y-6 hover:border-black hover:shadow-lg transition-all">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Daily Word Count
                </h2>
                <p className="text-sm text-gray-600 font-bold">
                  Words written each day
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-xl border-2 border-green-300 flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
            </div>

            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={progress.data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="date"
                  stroke="#6b7280"
                  style={{ fontSize: "12px", fontWeight: "bold" }}
                />
                <YAxis
                  stroke="#6b7280"
                  style={{ fontSize: "12px", fontWeight: "bold" }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "white",
                    border: "2px solid #d1d5db",
                    borderRadius: "0.75rem",
                    fontFamily: "'Space Mono', monospace",
                    fontWeight: "bold",
                  }}
                />
                <Bar dataKey="words" fill="#000" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Writing Patterns */}
        <div className="grid lg:grid-cols-2 gap-6">
          {patterns?.hourly_distribution &&
            Object.keys(patterns.hourly_distribution).length > 0 && (
              <div className="bg-white rounded-xl border-2 border-gray-300 p-6 md:p-8 space-y-6 hover:border-black hover:shadow-lg transition-all">
                <div>
                  <h2 className="text-xl font-bold text-gray-900 mb-2">
                    Best Writing Hours
                  </h2>
                  <p className="text-sm text-gray-600 font-bold">
                    When you write most
                  </p>
                </div>

                <ResponsiveContainer width="100%" height={250}>
                  <LineChart
                    data={Object.entries(patterns.hourly_distribution)
                      .map(([hour, data]) => ({
                        hour: parseInt(hour),
                        sessions: data.sessions,
                      }))
                      .sort((a, b) => a.hour - b.hour)}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis
                      dataKey="hour"
                      tickFormatter={formatTimeOfDay}
                      stroke="#6b7280"
                      style={{ fontSize: "11px", fontWeight: "bold" }}
                    />
                    <YAxis
                      stroke="#6b7280"
                      style={{ fontSize: "11px", fontWeight: "bold" }}
                    />
                    <Tooltip
                      labelFormatter={formatTimeOfDay}
                      contentStyle={{
                        backgroundColor: "white",
                        border: "2px solid #d1d5db",
                        borderRadius: "0.75rem",
                        fontFamily: "'Space Mono', monospace",
                        fontWeight: "bold",
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="sessions"
                      stroke="#000"
                      strokeWidth={3}
                      dot={{ fill: "#000", r: 5 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

          {patterns?.daily_patterns && patterns.daily_patterns.length > 0 && (
            <div className="bg-white rounded-xl border-2 border-gray-300 p-6 md:p-8 space-y-6 hover:border-black hover:shadow-lg transition-all">
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-2">
                  Daily Activity
                </h2>
                <p className="text-sm text-gray-600 font-bold">
                  Recent writing pattern
                </p>
              </div>

              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={patterns.daily_patterns.slice(-7)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="date"
                    stroke="#6b7280"
                    style={{ fontSize: "11px", fontWeight: "bold" }}
                  />
                  <YAxis
                    stroke="#6b7280"
                    style={{ fontSize: "11px", fontWeight: "bold" }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "white",
                      border: "2px solid #d1d5db",
                      borderRadius: "0.75rem",
                      fontFamily: "'Space Mono', monospace",
                      fontWeight: "bold",
                    }}
                  />
                  <Bar dataKey="words" fill="#000" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* AI Insights */}
        <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl border-2 border-blue-300 p-6 md:p-8 space-y-4">
          <div className="flex items-start gap-3">
            <div className="w-12 h-12 bg-blue-100 rounded-xl border-2 border-blue-300 flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-6 h-6 text-blue-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-bold text-gray-900 mb-3">
                AI Coach Insights
              </h3>
              <div className="space-y-3 text-sm text-gray-700 font-bold">
                {dailyProgress && !dailyProgress.goal_met && (
                  <div className="flex items-start gap-2">
                    <span className="text-lg flex-shrink-0">🎯</span>
                    <p>
                      You're{" "}
                      {(
                        dailyProgress.daily_goal - dailyProgress.today_words
                      ).toLocaleString()}{" "}
                      words away from unlocking community sharing today. Keep
                      going!
                    </p>
                  </div>
                )}
                {dailyProgress && dailyProgress.goal_met && (
                  <div className="flex items-start gap-2">
                    <span className="text-lg flex-shrink-0">✅</span>
                    <p>
                      You hit your daily goal! Sharing is unlocked. Consider
                      sharing your progress with the community.
                    </p>
                  </div>
                )}
                {overview?.current_streak >= 7 && (
                  <div className="flex items-start gap-2">
                    <span className="text-lg flex-shrink-0">🔥</span>
                    <p>
                      You're on a {overview.current_streak}-day streak! That's
                      impressive consistency.
                    </p>
                  </div>
                )}
                {patterns?.hourly_distribution &&
                  Object.keys(patterns.hourly_distribution).length > 0 && (
                    <div className="flex items-start gap-2">
                      <span className="text-lg flex-shrink-0">⏰</span>
                      <p>
                        Your most productive hour is{" "}
                        <strong>
                          {formatTimeOfDay(
                            parseInt(
                              Object.entries(
                                patterns.hourly_distribution,
                              ).reduce(
                                (max, [hour, data]) =>
                                  data.sessions >
                                  (patterns.hourly_distribution[max]
                                    ?.sessions || 0)
                                    ? hour
                                    : max,
                                "0",
                              ),
                            ),
                          )}
                        </strong>
                        . Try scheduling important writing then.
                      </p>
                    </div>
                  )}
                {progress?.summary?.total_words >= 500 && (
                  <div className="flex items-start gap-2">
                    <span className="text-lg flex-shrink-0">📈</span>
                    <p>
                      You wrote {progress.summary.total_words.toLocaleString()}{" "}
                      words this {timeRange === "week" ? "week" : "month"}. Keep
                      it up!
                    </p>
                  </div>
                )}
                {!overview?.current_streak && (
                  <div className="flex items-start gap-2">
                    <span className="text-lg flex-shrink-0">✍️</span>
                    <p>
                      Start your writing streak today! Consistency is key to
                      building a strong writing habit.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Back to Dashboard */}
        <div className="flex justify-center pt-4">
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 px-8 py-4 bg-black text-white rounded-xl font-bold border-2 border-black hover:bg-gray-800 hover:shadow-lg transition-all"
          >
            <Home size={20} />
            Back to Dashboard
          </Link>
        </div>
      </main>
    </div>
  );
}
