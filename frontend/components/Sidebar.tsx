"use client";

import Link from "next/link";

const mockConversations = [
  { id: "1", title: "TCS Analysis", symbol: "TCS" },
  { id: "2", title: "RELIANCE Analysis", symbol: "RELIANCE" },
  { id: "3", title: "NIFTY50 Overview", symbol: "NIFTY50" },
];

export default function Sidebar() {
  return (
    <aside className="w-56 shrink-0 bg-gray-900 border-r border-gray-800 flex flex-col h-screen">
      {/* Logo */}
      <div className="px-4 py-4 border-b border-gray-800">
        <span className="text-lg font-bold text-white">Tradexia</span>
      </div>

      {/* New chat button */}
      <div className="px-3 pt-3">
        <Link
          href="/chat"
          className="block w-full text-center py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-sm font-medium transition-colors"
        >
          + New Chat
        </Link>
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-1">
        <p className="text-xs text-gray-500 px-2 mb-2 uppercase tracking-wider">Recent</p>
        {mockConversations.map((c) => (
          <Link
            key={c.id}
            href={`/chat/${c.id}`}
            className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors group"
          >
            <span className="text-xs font-mono bg-gray-700 text-blue-400 px-1.5 py-0.5 rounded">
              {c.symbol}
            </span>
            <span className="text-sm text-gray-300 truncate group-hover:text-white">
              {c.title}
            </span>
          </Link>
        ))}
      </div>

      {/* Profile at bottom */}
      <div className="border-t border-gray-800 px-3 py-3">
        <Link
          href="/profile"
          className="flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-gray-800 transition-colors"
        >
          <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold">
            U
          </div>
          <span className="text-sm text-gray-300">Profile</span>
        </Link>
      </div>
    </aside>
  );
}
