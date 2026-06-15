import React, { useEffect } from "react";
import { Link } from "react-router-dom";
import { Sparkles, LogOut } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

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

export default function Header() {
  const { user, logout } = useAuth();

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
  }, []);

  return (
    <header className="bg-white border-b-2 border-gray-200 font-mono">
      <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-10 h-10 bg-yellow-400 rounded-xl border-2 border-black flex items-center justify-center transform group-hover:rotate-6 transition-transform">
            <Sparkles size={20} className="text-black" />
          </div>
          <span className="font-bold text-xl text-gray-900">WriteFlow</span>
        </Link>

        {/* Navigation */}
        <nav className="flex items-center gap-2 text-sm">
          {user ? (
            <>
              <Link
                to="/dashboard"
                className="px-4 py-2 font-bold text-gray-700 hover:text-black hover:bg-gray-100 rounded-lg transition-all"
              >
                Dashboard
              </Link>
              <Link
                to="/write"
                className="px-4 py-2 font-bold text-gray-700 hover:text-black hover:bg-gray-100 rounded-lg transition-all"
              >
                Write
              </Link>
              <Link
                to="/analytics"
                className="px-4 py-2 font-bold text-gray-700 hover:text-black hover:bg-gray-100 rounded-lg transition-all"
              >
                Analytics
              </Link>
              <Link
                to="/community"
                className="px-4 py-2 font-bold text-gray-700 hover:text-black hover:bg-gray-100 rounded-lg transition-all"
              >
                Community
              </Link>
              <button
                onClick={logout}
                className="flex items-center gap-2 px-4 py-2 font-bold text-gray-700 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
              >
                <LogOut size={16} />
                Logout
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="px-4 py-2 font-bold text-gray-700 hover:text-black hover:bg-gray-100 rounded-lg transition-all"
              >
                Login
              </Link>
              <Link
                to="/register"
                className="px-4 py-2 bg-black text-white font-bold rounded-lg border-2 border-black hover:bg-gray-800 hover:shadow-lg transition-all"
              >
                Register
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
