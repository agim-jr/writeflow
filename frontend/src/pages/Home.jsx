import React, { useEffect } from "react";
import { Link } from "react-router-dom";
import {
  PenTool,
  TrendingUp,
  Target,
  Sparkles,
  ArrowRight,
} from "lucide-react";

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

export default function Home() {
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
    <div className="min-h-screen bg-white font-mono">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="max-w-6xl mx-auto px-4 py-20 md:py-32">
          <div className="text-center space-y-8">
            {/* Headline */}
            <div className="space-y-4">
              <h2 className="text-4xl md:text-6xl font-bold text-gray-900 leading-tight">
                WRITE.
                <br />
                EVERY.
                <br />
                DAY.
              </h2>
              <p className="text-lg md:text-xl text-gray-600 font-bold max-w-2xl mx-auto">
                Build an unbreakable writing habit with AI-powered motivation.
              </p>
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
              <Link
                to="/register"
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-4 bg-black text-white rounded-xl font-bold border-2 border-black hover:bg-gray-800 hover:shadow-lg transition-all"
              >
                Start Writing
                <ArrowRight size={20} />
              </Link>
              <Link
                to="/login"
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-4 bg-white text-black rounded-xl font-bold border-2 border-gray-300 hover:border-black hover:shadow-lg transition-all"
              >
                Login
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-6xl mx-auto px-4 py-16 md:py-24">
        <div className="grid md:grid-cols-3 gap-6">
          {/* Feature 1 */}
          <div className="bg-white rounded-xl border-2 border-gray-300 p-8 text-center space-y-4 hover:border-black hover:shadow-lg transition-all">
            <div className="w-16 h-16 bg-blue-100 rounded-xl border-2 border-blue-300 flex items-center justify-center mx-auto">
              <PenTool className="w-8 h-8 text-blue-600" />
            </div>
            <h3 className="font-bold text-xl text-gray-900">Daily Writing</h3>
            <p className="text-gray-600 font-bold text-sm">
              Distraction-free editor for daily practice and consistent growth.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="bg-white rounded-xl border-2 border-gray-300 p-8 text-center space-y-4 hover:border-black hover:shadow-lg transition-all">
            <div className="w-16 h-16 bg-green-100 rounded-xl border-2 border-green-300 flex items-center justify-center mx-auto">
              <TrendingUp className="w-8 h-8 text-green-600" />
            </div>
            <h3 className="font-bold text-xl text-gray-900">Streak Tracking</h3>
            <p className="text-gray-600 font-bold text-sm">
              Never break the chain. Build momentum with visual progress.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="bg-white rounded-xl border-2 border-gray-300 p-8 text-center space-y-4 hover:border-black hover:shadow-lg transition-all">
            <div className="w-16 h-16 bg-purple-100 rounded-xl border-2 border-purple-300 flex items-center justify-center mx-auto">
              <Target className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="font-bold text-xl text-gray-900">AI Coach</h3>
            <p className="text-gray-600 font-bold text-sm">
              Personalized motivation and insights from your AI writing coach.
            </p>
          </div>
        </div>
      </section>

      {/* Social Proof / Stats Section */}
      <section className="bg-white border-t-2 border-b-2 border-gray-300 py-16">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <p className="text-4xl font-bold text-gray-900 mb-2">10K+</p>
              <p className="text-gray-600 font-bold text-sm">Active Writers</p>
            </div>
            <div>
              <p className="text-4xl font-bold text-gray-900 mb-2">5M+</p>
              <p className="text-gray-600 font-bold text-sm">Words Written</p>
            </div>
            <div>
              <p className="text-4xl font-bold text-gray-900 mb-2">365</p>
              <p className="text-gray-600 font-bold text-sm">Day Streaks</p>
            </div>
            <div>
              <p className="text-4xl font-bold text-gray-900 mb-2">98%</p>
              <p className="text-gray-600 font-bold text-sm">Satisfaction</p>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="max-w-4xl mx-auto px-4 py-20 text-center">
        <div className="bg-black rounded-xl border-2 border-black p-12 shadow-lg transform hover:scale-105 transition-all">
          <h3 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to start your writing journey?
          </h3>
          <p className="text-white font-bold text-lg mb-8">
            Join thousands of writers building their daily habit.
          </p>
          <Link
            to="/register"
            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-black rounded-xl font-bold border-2 border-black hover:bg-gray-800 hover:shadow-lg transition-all"
          >
            Get Started Free
            <ArrowRight size={20} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t-2 border-gray-300 py-8">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <p className="text-sm text-gray-600 font-bold">
            © 2026 ProjectWriter. All rights reserved.{" "}
            <a href="#" className="text-black hover:underline">
              Terms
            </a>{" "}
            •{" "}
            <a href="#" className="text-black hover:underline">
              Privacy
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}
