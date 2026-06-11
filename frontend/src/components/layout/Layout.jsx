import React from "react";
import { useLocation } from "react-router-dom";
import Header from "./Header";

export default function Layout({ children }) {
  const location = useLocation();

  // Routes where header and footer should be hidden
  const authRoutes = ["/login", "/register"];
  const isAuthPage = authRoutes.includes(location.pathname);

  // Routes that handle their own layout (no shared header)
  const customLayoutRoutes = ["/dashboard", "/analytics", "/community"]; // ✅ ADD /community
  const isCustomLayout = customLayoutRoutes.includes(location.pathname);

  return (
    <div className="min-h-screen flex flex-col">
      {!isAuthPage && !isCustomLayout && <Header />}
      <main
        className={`flex-1 w-full mx-auto ${
          !isAuthPage && !isCustomLayout ? "max-w-6xl px-4 py-8" : ""
        }`}
      >
        {children}
      </main>
      {!isAuthPage && !isCustomLayout && (
        <footer className="border-t-2 border-gray-200 py-4 text-center text-xs font-bold tracking-wider text-gray-600 font-mono">
          © 2026 ProjectWriter
        </footer>
      )}
    </div>
  );
}
