"use client";

import { Plus, Search, LogOut, MessageSquare } from "lucide-react";
import { Conversation } from "./types";
import { groupConversations } from "./helpers";
import ConvoGroup from "./ConvoGroup";

interface Props {
  conversations: Conversation[];
  loading?: boolean;
  activeId: string;
  hoveredId: string | null;
  searchQuery: string;
  username?: string;
  onSelect: (id: string) => void;
  onHover: (id: string | null) => void;
  onDelete: (id: string, e: React.MouseEvent) => void;
  onNewChat: () => void;
  onSearchChange: (q: string) => void;
  onLogout: () => void;
}

export default function ChatSidebar({
  conversations, activeId, hoveredId, searchQuery, username, loading,
  onSelect, onHover, onDelete, onNewChat, onSearchChange, onLogout,
}: Props) {
  const filtered = conversations.filter(
    (c) =>
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.preview.toLowerCase().includes(searchQuery.toLowerCase())
  );
  const groups = groupConversations(filtered);
  const hasAny = groups.today.length + groups.yesterday.length + groups.thisWeek.length + groups.older.length > 0;

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col border-r border-border bg-sidebar h-screen">
      {/* Top */}
      <div className="flex items-center justify-between px-3 pt-3 pb-2 gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-6 h-6 bg-foreground rounded-md flex items-center justify-center flex-shrink-0">
            <MessageSquare size={13} className="text-background" />
          </div>
          <span className="text-sm font-semibold text-foreground truncate">Tradexia</span>
        </div>
        <button onClick={onNewChat}
          className="p-1.5 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors flex-shrink-0"
          title="New chat">
          <Plus size={15} />
        </button>
      </div>

      {/* Search */}
      <div className="px-3 pb-2">
        <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-md bg-accent border border-transparent focus-within:border-border transition-colors">
          <Search size={13} className="text-muted-foreground flex-shrink-0" />
          <input type="text" placeholder="Search" value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none w-full"
          />
        </div>
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto px-2 space-y-0.5">
        {loading ? (
          <div className="flex flex-col gap-2 px-2 pt-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-7 rounded-md bg-accent animate-pulse" />
            ))}
          </div>
        ) : !hasAny ? (
          <div className="flex flex-col items-center justify-center h-full gap-2 pb-8 text-center px-4">
            <MessageSquare size={22} className="text-muted-foreground/50" />
            <p className="text-xs text-muted-foreground">No conversations yet.</p>
            <p className="text-xs text-muted-foreground">Start a new chat to get started.</p>
          </div>
        ) : (
          <>
            <ConvoGroup label="Today" items={groups.today} activeId={activeId} hoveredId={hoveredId} onSelect={onSelect} onHover={onHover} onDelete={onDelete} />
            <ConvoGroup label="Yesterday" items={groups.yesterday} activeId={activeId} hoveredId={hoveredId} onSelect={onSelect} onHover={onHover} onDelete={onDelete} />
            <ConvoGroup label="This week" items={groups.thisWeek} activeId={activeId} hoveredId={hoveredId} onSelect={onSelect} onHover={onHover} onDelete={onDelete} />
            <ConvoGroup label="Older" items={groups.older} activeId={activeId} hoveredId={hoveredId} onSelect={onSelect} onHover={onHover} onDelete={onDelete} />
          </>
        )}
      </div>

      {/* Bottom */}
      <div className="border-t border-border px-3 py-2.5">
        <button onClick={onLogout}
          className="flex items-center gap-2.5 w-full px-2 py-1.5 rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-accent transition-colors">
          <div className="w-6 h-6 rounded-full bg-foreground flex items-center justify-center text-[10px] font-semibold text-background flex-shrink-0">
            {username ? username.slice(0, 2).toUpperCase() : "U"}
          </div>
          <span className="truncate text-sm text-foreground">
            {username ? `@${username}` : "user"}
          </span>
          <LogOut size={13} className="ml-auto flex-shrink-0" />
        </button>
      </div>
    </aside>
  );
}
