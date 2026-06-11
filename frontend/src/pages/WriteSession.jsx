import React, { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Play,
  Pause,
  X,
  Sparkles,
  Trophy,
  Lightbulb,
  Home,
  Check,
  Zap,
  Heart,
  Download,
  Share2,
} from "lucide-react";
import api, { WS_BASE_URL } from "../services/api";
import CreatePostModal from "../components/community/CreatePostModal";

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

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .animate-fadeIn {
    animation: fadeIn 0.4s ease-out;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  .animate-pulse-slow {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }

  @keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .animate-slideUp {
    animation: slideUp 0.3s ease-out;
  }
`;

export default function WriteSession() {
  const navigate = useNavigate();
  const location = useLocation();
  const mode = location.state?.mode || "timed";

  const [isActive, setIsActive] = useState(false);
  const [timeLeft, setTimeLeft] = useState(0);
  const [wordCount, setWordCount] = useState(0);
  const [text, setText] = useState("");
  const [goal, setGoal] = useState({ type: "time", value: 25 });
  const [showComplete, setShowComplete] = useState(false);
  const [showAICoach, setShowAICoach] = useState(true);
  const [coachMessage, setCoachMessage] = useState("");
  const [coachMessageType, setCoachMessageType] = useState("info");
  const [sessionStartTime, setSessionStartTime] = useState(null);
  const [currentPersonality, setCurrentPersonality] = useState(null);
  const [lastMessageTime, setLastMessageTime] = useState(null);
  const [showExportMenu, setShowExportMenu] = useState(false);

  // Goal completion state
  const [goalComplete, setGoalComplete] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [canPost, setCanPost] = useState({ can_post: false, message: "" });
  const [showGoalBanner, setShowGoalBanner] = useState(false);

  const [wpmHistory, setWpmHistory] = useState([]);
  const [pauseCount, setPauseCount] = useState(0);
  const [editCount, setEditCount] = useState(0);
  const [lastKeystrokeTime, setLastKeystrokeTime] = useState(Date.now());
  const [lastWordCount, setLastWordCount] = useState(0);

  const [wsConnected, setWsConnected] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const ws = useRef(null);
  const textareaRef = useRef(null);
  const initializedRef = useRef(false);
  const exportMenuRef = useRef(null);
  const autoSaveInterval = useRef(null);

  useEffect(() => {
    loadFont();
    if (!document.querySelector("#space-mono-style")) {
      const style = document.createElement("style");
      style.id = "space-mono-style";
      style.textContent = fontStyle;
      document.head.appendChild(style);
    }
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        exportMenuRef.current &&
        !exportMenuRef.current.contains(event.target)
      ) {
        setShowExportMenu(false);
      }
    };

    if (showExportMenu) {
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [showExportMenu]);

  // Initialize session
  useEffect(() => {
    if (initializedRef.current) return;
    initializedRef.current = true;

    const initSession = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) {
          console.error("No auth token found");
          return;
        }

        const userId = parseInt(JSON.parse(atob(token.split(".")[1])).sub);
        console.log("🔑 User ID:", userId);

        // Set goal based on mode FIRST
        if (mode === "timed") {
          setTimeLeft(25 * 60);
          setGoal({ type: "time", value: 25 });
        } else if (mode === "sprint") {
          setTimeLeft(0);
          setGoal({ type: "words", value: 500 });
        } else if (mode === "focus") {
          setTimeLeft(45 * 60);
          setGoal({ type: "time", value: 45 });
        }

        // Create session
        const sessionResponse = await api.post("/analytics/session", {
          word_count: 0,
          duration_seconds: 0,
          session_type: mode,
          goal_met: false,
          started_at: new Date().toISOString(),
        });

        const newSessionId = sessionResponse.data.session_id;
        setSessionId(newSessionId);
        setSessionStartTime(new Date());
        console.log("📝 Session created:", newSessionId);

        // Check if can post
        await checkCanPost();

        // Initialize WebSocket
        await initWebSocket(userId, newSessionId);

        // Get initial coach message
        await fetchInitialCoachMessage();

        // Start session
        setTimeout(() => {
          setIsActive(true);
          textareaRef.current?.focus();
        }, 500);
      } catch (err) {
        console.error("❌ Failed to initialize session:", err);
      }
    };

    initSession();

    return () => {
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        ws.current.close();
      }
      if (autoSaveInterval.current) {
        clearInterval(autoSaveInterval.current);
      }
    };
  }, [mode]);

  const checkCanPost = async () => {
    try {
      const response = await api.get("/community/can-post-today");
      setCanPost(response.data);
      console.log("📊 Can post today:", response.data);
    } catch (error) {
      console.error("Failed to check post permission:", error);
    }
  };

  const initWebSocket = async (userId, sessionId) => {
    try {
      const wsUrl = `${WS_BASE_URL}/ws/writing-session?user_id=${userId}&session_id=${sessionId}`;
      console.log("🔌 Connecting to WebSocket:", wsUrl);

      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log("✅ WebSocket connected");
        setWsConnected(true);
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      ws.current.onerror = (error) => {
        console.error("❌ WebSocket error:", error);
        setWsConnected(false);
      };

      ws.current.onclose = () => {
        console.log("🔌 WebSocket closed");
        setWsConnected(false);
      };
    } catch (err) {
      console.error("❌ WebSocket init failed:", err);
    }
  };

  const handleWebSocketMessage = (data) => {
    console.log("📨 WebSocket message:", data);

    switch (data.type) {
      case "connection_established":
        console.log("✅ AI Coach monitoring");
        break;

      case "coaching_nudge":
        setCoachMessage(data.message);
        setCoachMessageType(
          data.reason === "writer_block_detected" ? "stuck" : "encouragement",
        );
        if (data.personality) {
          setCurrentPersonality(data.personality);
          setLastMessageTime(Date.now());
        }
        break;

      case "inactivity_nudge":
        setCoachMessage(data.message);
        setCoachMessageType("stuck");
        if (data.personality) {
          setCurrentPersonality(data.personality);
          setLastMessageTime(Date.now());
        }
        break;

      case "milestone_celebration":
        setCoachMessage(data.message);
        setCoachMessageType("milestone");
        if (data.personality) {
          setCurrentPersonality(data.personality);
          setLastMessageTime(Date.now());
        }
        setTimeout(() => setCoachMessage(""), 8000);
        break;

      case "encouragement":
        setCoachMessage(data.message);
        setCoachMessageType("encouragement");
        if (data.personality) {
          setCurrentPersonality(data.personality);
          setLastMessageTime(Date.now());
        }
        setTimeout(() => setCoachMessage(""), 6000);
        break;
    }
  };

  const fetchInitialCoachMessage = async () => {
    try {
      const response = await api.post("/ai-coach/message", {
        context: "session_start",
        session_type: mode,
        word_count: 0,
        time_elapsed: 0,
      });

      setCoachMessage(response.data.message);
      setCoachMessageType("info");
      setCurrentPersonality(response.data.personality_type);
      setLastMessageTime(Date.now());
      setShowAICoach(true);
    } catch (err) {
      console.error("❌ Failed to fetch coach message:", err);
    }
  };

  const sendKeystrokeEvent = (event) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(
        JSON.stringify({
          type: "keypress",
          key: event.key,
          timestamp: new Date().toISOString(),
          word_count: wordCount,
        }),
      );
    }
  };

  // Auto-save every 30 seconds
  useEffect(() => {
    if (!sessionId || !text.trim()) return;

    autoSaveInterval.current = setInterval(() => {
      saveSession();
    }, 30000);

    return () => {
      if (autoSaveInterval.current) {
        clearInterval(autoSaveInterval.current);
      }
    };
  }, [sessionId, text, wordCount]);

  const saveSession = async () => {
    if (!sessionId) return;

    try {
      const durationSeconds = sessionStartTime
        ? Math.floor((Date.now() - sessionStartTime.getTime()) / 1000)
        : 0;

      await api.put(`/analytics/session/${sessionId}`, {
        final_word_count: wordCount,
        time_spent: durationSeconds,
        completed: goalComplete,
        avg_wpm:
          wpmHistory.length > 0
            ? Math.round(
                wpmHistory.reduce((a, b) => a + b, 0) / wpmHistory.length,
              )
            : 0,
        peak_wpm: wpmHistory.length > 0 ? Math.max(...wpmHistory) : 0,
        pauses: pauseCount,
        edits: editCount,
      });

      console.log("💾 Session auto-saved");
    } catch (err) {
      console.error("❌ Save failed:", err);
    }
  };

  // Timer countdown - FIXED
  useEffect(() => {
    let interval = null;
    if (isActive && timeLeft > 0 && mode !== "sprint") {
      interval = setInterval(() => {
        setTimeLeft((time) => time - 1);
      }, 1000);
    } else if (timeLeft === 0 && isActive && mode !== "sprint") {
      handleComplete();
    }
    return () => clearInterval(interval);
  }, [isActive, timeLeft, mode]);

  // Track word count and check goal
  useEffect(() => {
    const words = text
      .trim()
      .split(/\s+/)
      .filter((word) => word.length > 0).length;
    setWordCount(words);

    // Check if 250-word daily goal reached
    if (words >= 250 && !goalComplete) {
      setGoalComplete(true);
      setShowGoalBanner(true);
      saveSession();
      console.log("🎉 Daily goal complete! 250 words reached");
    }

    // Send feedback if user wrote after coach message
    if (words > lastWordCount) {
      setLastWordCount(words);

      if (currentPersonality && lastMessageTime) {
        const timeSinceMessage = Date.now() - lastMessageTime;

        if (timeSinceMessage < 300000) {
          api
            .post("/ai-coach/feedback", null, {
              params: {
                personality: currentPersonality,
                response_type: "wrote_within_60min",
                time_to_action: timeSinceMessage / 1000,
              },
            })
            .then(() => {
              console.log("✅ Feedback sent");
              setCurrentPersonality(null);
              setLastMessageTime(null);
            })
            .catch((err) => console.error("❌ Feedback failed:", err));
        }
      }
    }

    // Check mode-specific sprint goal
    if (mode === "sprint" && words >= goal.value) {
      handleComplete();
    }
  }, [text, mode, goal.value, goalComplete, lastWordCount]);

  // Calculate WPM
  useEffect(() => {
    if (!isActive || !sessionStartTime) return;

    const interval = setInterval(() => {
      const timeInMinutes = (Date.now() - sessionStartTime.getTime()) / 60000;
      if (timeInMinutes > 0 && wordCount > 0) {
        const currentWPM = Math.round(wordCount / timeInMinutes);
        setWpmHistory((prev) => [...prev, currentWPM]);
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [isActive, wordCount, sessionStartTime]);

  const handleComplete = async () => {
    setIsActive(false);
    setShowComplete(true);

    if (ws.current) {
      ws.current.close();
    }

    // Final save
    await saveSession();

    // Save content
    if (text.trim()) {
      try {
        await api.post("/writing/save", {
          content: text,
          word_count: wordCount,
          title: `${mode.charAt(0).toUpperCase() + mode.slice(1)} Session - ${new Date().toLocaleDateString()}`,
          session_id: sessionId,
          session_type: mode,
        });
        console.log("✅ Content saved");
      } catch (err) {
        console.error("❌ Content save failed:", err);
      }
    }
  };

  const handleTextareaKeyDown = (e) => {
    sendKeystrokeEvent(e);

    const now = Date.now();
    if (now - lastKeystrokeTime > 3000) {
      setPauseCount((prev) => prev + 1);
    }
    setLastKeystrokeTime(now);

    if (e.key === "Backspace" || e.key === "Delete") {
      setEditCount((prev) => prev + 1);
    }
  };

  const handleShare = () => {
    setShowShareModal(true);
  };

  const handlePostCreated = () => {
    setCanPost({ can_post: false, message: "Already shared today!" });
    setShowShareModal(false);
    setShowGoalBanner(false);
  };

  const generateFilename = (extension) => {
    const date = new Date().toISOString().split("T")[0];
    const modeLabel = mode.charAt(0).toUpperCase() + mode.slice(1);
    return `${modeLabel}_Session_${date}.${extension}`;
  };

  const exportAsTXT = () => {
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = generateFilename("txt");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    setShowExportMenu(false);
  };

  const exportAsMarkdown = () => {
    const markdown = `# ${mode.charAt(0).toUpperCase() + mode.slice(1)} Session
**Date:** ${new Date().toLocaleDateString()}
**Word Count:** ${wordCount}
**Duration:** ${mode === "sprint" ? "Sprint" : `${goal.value} minutes`}

---

${text}`;

    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = generateFilename("md");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    setShowExportMenu(false);
  };

  const exportAsHTML = () => {
    const html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${mode.charAt(0).toUpperCase() + mode.slice(1)} Session - ${new Date().toLocaleDateString()}</title>
    <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Space Mono', monospace;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            line-height: 1.6;
            color: #1f2937;
        }
        .header {
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        h1 {
            margin: 0 0 10px 0;
            font-size: 24px;
        }
        .meta {
            color: #6b7280;
            font-size: 14px;
        }
        .content {
            white-space: pre-wrap;
            font-size: 16px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>${mode.charAt(0).toUpperCase() + mode.slice(1)} Session</h1>
        <div class="meta">
            <strong>Date:</strong> ${new Date().toLocaleDateString()} |
            <strong>Word Count:</strong> ${wordCount} |
            <strong>Duration:</strong> ${mode === "sprint" ? "Sprint" : `${goal.value} minutes`}
        </div>
    </div>
    <div class="content">${text}</div>
</body>
</html>`;

    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = generateFilename("html");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    setShowExportMenu(false);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  // FIXED: Progress calculation for display
  const getProgress = () => {
    if (mode === "sprint") {
      // Sprint mode: show progress toward 500-word goal
      return Math.min((wordCount / goal.value) * 100, 100);
    } else {
      // Timed/Focus mode: show time progress
      const totalTime = goal.value * 60;
      return ((totalTime - timeLeft) / totalTime) * 100;
    }
  };

  if (showComplete) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4 font-mono">
        <div className="max-w-2xl w-full">
          <div className="bg-white rounded-xl border-2 border-gray-300 p-8 md:p-12 space-y-8 text-center">
            <div className="flex justify-center">
              <div className="w-20 h-20 bg-green-100 rounded-full border-2 border-green-300 flex items-center justify-center">
                <Check className="w-10 h-10 text-green-600" />
              </div>
            </div>

            <div className="space-y-3">
              <h2 className="text-4xl font-bold text-gray-900">
                Session Complete!
              </h2>
              <p className="text-lg text-gray-600 font-bold">
                Great work staying focused
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-xl border-2 border-gray-300 p-6">
                <div className="text-5xl font-bold text-gray-900 mb-2">
                  {wordCount}
                </div>
                <div className="text-sm text-gray-600 font-bold uppercase tracking-wide">
                  Words Written
                </div>
              </div>
              <div className="bg-gray-50 rounded-xl border-2 border-gray-300 p-6">
                <div className="text-5xl font-bold text-gray-900 mb-2">
                  {mode === "sprint" ? "✓" : goal.value}
                </div>
                <div className="text-sm text-gray-600 font-bold uppercase tracking-wide">
                  {mode === "sprint" ? "Sprint Done" : "Minutes"}
                </div>
              </div>
            </div>

            {(wpmHistory.length > 0 || pauseCount > 0 || editCount > 0) && (
              <div className="grid grid-cols-3 gap-4 pt-4 border-t-2 border-gray-200">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {wpmHistory.length > 0
                      ? Math.round(
                          wpmHistory.reduce((a, b) => a + b, 0) /
                            wpmHistory.length,
                        )
                      : 0}
                  </div>
                  <div className="text-xs text-gray-500 font-bold uppercase tracking-wide">
                    Avg WPM
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {pauseCount}
                  </div>
                  <div className="text-xs text-gray-500 font-bold uppercase tracking-wide">
                    Pauses
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {editCount}
                  </div>
                  <div className="text-xs text-gray-500 font-bold uppercase tracking-wide">
                    Edits
                  </div>
                </div>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => navigate("/dashboard")}
                className="flex-1 flex items-center justify-center gap-2 px-8 py-4 bg-black text-white rounded-xl font-bold border-2 border-black hover:bg-gray-800 hover:shadow-lg transition-all"
              >
                <Home size={20} />
                Back to Dashboard
              </button>

              {goalComplete && canPost.can_post && (
                <button
                  onClick={handleShare}
                  className="flex items-center gap-2 px-6 py-4 bg-green-600 text-white rounded-xl font-bold hover:bg-green-700 transition-all"
                >
                  <Share2 size={20} />
                  Share
                </button>
              )}

              {text.trim() && (
                <div className="relative" ref={exportMenuRef}>
                  <button
                    onClick={() => setShowExportMenu(!showExportMenu)}
                    className="px-6 py-4 bg-white text-black rounded-xl font-bold border-2 border-gray-300 hover:border-black hover:shadow-lg transition-all"
                  >
                    <Download size={20} />
                  </button>

                  {showExportMenu && (
                    <div className="absolute right-0 bottom-full mb-2 w-48 bg-white rounded-lg border-2 border-gray-300 shadow-lg overflow-hidden animate-fadeIn">
                      <button
                        onClick={exportAsTXT}
                        className="w-full px-4 py-3 text-left text-sm font-bold hover:bg-gray-50 transition-colors"
                      >
                        Export as TXT
                      </button>
                      <button
                        onClick={exportAsMarkdown}
                        className="w-full px-4 py-3 text-left text-sm font-bold hover:bg-gray-50 transition-colors border-t border-gray-200"
                      >
                        Export as Markdown
                      </button>
                      <button
                        onClick={exportAsHTML}
                        className="w-full px-4 py-3 text-left text-sm font-bold hover:bg-gray-50 transition-colors border-t border-gray-200"
                      >
                        Export as HTML
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Share Modal */}
        <CreatePostModal
          isOpen={showShareModal}
          onClose={() => setShowShareModal(false)}
          onPostCreated={handlePostCreated}
          canPost={canPost}
          initialContent={text}
          initialWordCount={wordCount}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col font-mono relative">
      {/* Goal Complete Banner */}
      {showGoalBanner && goalComplete && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 w-full max-w-2xl px-4 animate-slideUp">
          <div className="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-300 rounded-xl p-4 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-1">
                  🎉 Daily Goal Complete!
                </h3>
                <p className="text-sm text-gray-700">
                  {canPost.can_post
                    ? "Want to share your work with the community?"
                    : "Keep writing or come back tomorrow to share!"}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {canPost.can_post && (
                  <button
                    onClick={handleShare}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 transition-colors flex items-center gap-2"
                  >
                    <Share2 size={16} />
                    Share
                  </button>
                )}
                <button
                  onClick={() => setShowGoalBanner(false)}
                  className="p-2 hover:bg-white hover:bg-opacity-50 rounded-lg transition-all"
                >
                  <X className="w-4 h-4 text-gray-600" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Editor */}
      <div className="flex-1 overflow-y-auto bg-white pb-56">
        <div className="max-w-3xl mx-auto px-4 py-12">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleTextareaKeyDown}
            placeholder="Start writing..."
            className="w-full min-h-full resize-none text-gray-900 text-lg leading-relaxed placeholder-gray-400 bg-transparent"
            style={{
              fontFamily: "'Space Mono', monospace",
              outline: "none",
              border: "none",
              minHeight: "calc(100vh - 200px)",
            }}
          />
        </div>
      </div>

      {/* AI Coach Message - Floating */}
      <div className="fixed bottom-24 left-1/2 transform -translate-x-1/2 z-40 w-full max-w-2xl px-4">
        <div className="space-y-2">
          {showAICoach && coachMessage && (
            <div
              className={`border-2 rounded-xl p-4 shadow-lg animate-slideUp ${
                coachMessageType === "milestone"
                  ? "bg-green-50 border-green-300"
                  : coachMessageType === "encouragement"
                    ? "bg-blue-50 border-blue-300"
                    : coachMessageType === "stuck"
                      ? "bg-amber-50 border-amber-300"
                      : "bg-blue-50 border-blue-300"
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-8 h-8 rounded-lg border-2 flex items-center justify-center flex-shrink-0 ${
                    coachMessageType === "milestone"
                      ? "bg-green-100 border-green-300"
                      : coachMessageType === "encouragement"
                        ? "bg-blue-100 border-blue-300"
                        : coachMessageType === "stuck"
                          ? "bg-amber-100 border-amber-300"
                          : "bg-blue-100 border-blue-300"
                  }`}
                >
                  {coachMessageType === "milestone" && (
                    <Trophy className="w-4 h-4 text-green-600" />
                  )}
                  {coachMessageType === "stuck" && (
                    <Lightbulb className="w-4 h-4 text-amber-600" />
                  )}
                  {coachMessageType === "encouragement" && (
                    <Heart className="w-4 h-4 text-blue-600" />
                  )}
                  {coachMessageType === "info" && (
                    <Sparkles className="w-4 h-4 text-blue-600" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="text-xs text-gray-500 font-bold uppercase tracking-wide">
                    AI Coach
                    {wsConnected && (
                      <span className="text-green-600"> • Live</span>
                    )}
                  </div>
                  <div className="text-sm text-gray-900 font-bold">
                    {coachMessage}
                  </div>
                </div>

                <button
                  onClick={() => setCoachMessage("")}
                  className="p-1 hover:bg-white hover:bg-opacity-50 rounded-lg transition-all flex-shrink-0"
                >
                  <X className="w-4 h-4 text-gray-600" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Toolbar - Floating */}
      <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50 animate-slideUp">
        <div className="bg-white rounded-full border-2 border-gray-300 shadow-2xl px-2 py-2">
          <div className="flex items-center gap-1">
            <button
              onClick={() => navigate("/dashboard")}
              className="p-3 hover:bg-gray-100 rounded-full transition-all"
              title="Exit"
            >
              <Home className="w-5 h-5 text-gray-600" />
            </button>

            <div className="w-px h-8 bg-gray-300" />

            <div className="px-4 flex items-center gap-2">
              {mode === "sprint" ? (
                <>
                  <span className="text-xl font-bold text-gray-900">
                    {wordCount}
                  </span>
                  <span className="text-xs text-gray-500 font-bold">
                    / {goal.value}
                  </span>
                </>
              ) : (
                <span className="text-xl font-bold text-gray-900">
                  {formatTime(timeLeft)}
                </span>
              )}
            </div>

            <div className="relative w-10 h-10">
              <svg className="w-full h-full transform -rotate-90">
                <circle
                  cx="20"
                  cy="20"
                  r="16"
                  fill="none"
                  stroke="#e5e7eb"
                  strokeWidth="3"
                />
                <circle
                  cx="20"
                  cy="20"
                  r="16"
                  fill="none"
                  stroke="#3b82f6"
                  strokeWidth="3"
                  strokeDasharray={`${2 * Math.PI * 16}`}
                  strokeDashoffset={`${2 * Math.PI * 16 * (1 - getProgress() / 100)}`}
                  strokeLinecap="round"
                  className="transition-all duration-300"
                />
              </svg>
            </div>

            <div className="w-px h-8 bg-gray-300" />

            <button
              onClick={() => setIsActive(!isActive)}
              className="p-3 hover:bg-gray-100 rounded-full transition-all"
              title={isActive ? "Pause" : "Resume"}
            >
              {isActive ? (
                <Pause className="w-5 h-5 text-black" />
              ) : (
                <Play className="w-5 h-5 text-black" />
              )}
            </button>

            <div className="w-px h-8 bg-gray-300" />

            {wsConnected ? (
              <div className="px-3 py-2 bg-green-50 rounded-full border-2 border-green-300 flex items-center gap-2">
                <Zap className="w-4 h-4 text-green-600 animate-pulse-slow" />
                <span className="text-xs font-bold text-green-700">Live</span>
              </div>
            ) : (
              <div className="px-3 py-2 bg-gray-100 rounded-full border-2 border-gray-300">
                <span className="text-xs font-bold text-gray-500">Offline</span>
              </div>
            )}

            <button
              onClick={() => setShowAICoach(!showAICoach)}
              className={`p-3 hover:bg-gray-100 rounded-full transition-all ${
                showAICoach ? "bg-blue-50" : ""
              }`}
              title={showAICoach ? "Hide AI Coach" : "Show AI Coach"}
            >
              <Sparkles
                className={`w-5 h-5 ${showAICoach ? "text-blue-600" : "text-gray-600"}`}
              />
            </button>

            {text.trim() && (
              <div className="relative" ref={exportMenuRef}>
                <button
                  onClick={() => setShowExportMenu(!showExportMenu)}
                  className="p-3 hover:bg-gray-100 rounded-full transition-all"
                  title="Export"
                >
                  <Download className="w-5 h-5 text-gray-600" />
                </button>

                {showExportMenu && (
                  <div className="absolute bottom-full mb-3 left-1/2 transform -translate-x-1/2 w-48 bg-white rounded-xl border-2 border-gray-300 shadow-xl overflow-hidden animate-slideUp">
                    <button
                      onClick={exportAsTXT}
                      className="w-full px-4 py-3 text-left text-sm font-bold hover:bg-gray-50 transition-colors"
                    >
                      Export as TXT
                    </button>
                    <button
                      onClick={exportAsMarkdown}
                      className="w-full px-4 py-3 text-left text-sm font-bold hover:bg-gray-50 transition-colors border-t border-gray-200"
                    >
                      Export as Markdown
                    </button>
                    <button
                      onClick={exportAsHTML}
                      className="w-full px-4 py-3 text-left text-sm font-bold hover:bg-gray-50 transition-colors border-t border-gray-200"
                    >
                      Export as HTML
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Share Modal */}
      <CreatePostModal
        isOpen={showShareModal}
        onClose={() => setShowShareModal(false)}
        onPostCreated={handlePostCreated}
        canPost={canPost}
        initialContent={text}
        initialWordCount={wordCount}
      />
    </div>
  );
}
