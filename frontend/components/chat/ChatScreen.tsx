"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Send, ChevronDown } from "lucide-react";
import { Conversation, Message } from "./types";
import ChatSidebar from "./ChatSidebar";
import MessageBubble from "./MessageBubble";
import EmptyState from "./EmptyState";
import * as sdk from "@/lib/sdk";

export default function ChatScreen({ conversationId }: { conversationId?: string }) {
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loadingConvos, setLoadingConvos] = useState(true);
  const [activeId, setActiveId] = useState<string | null>(conversationId ?? null);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const activeConversation = conversations.find((c) => c.id === activeId) ?? null;

  // Fetch conversation list on mount
  const fetchConversations = useCallback(async () => {
    try {
      const data = await sdk.getConversations();
      setConversations(data.map((c) => ({
        id: c.id,
        title: c.title ?? "Untitled",
        sessionId: c.sessionId,
        preview: "",
        timestamp: new Date(c.updatedAt),
        messages: [],
      })));
    } catch {
      // If 401, sdk auto-redirects to login
    } finally {
      setLoadingConvos(false);
    }
  }, []);

  useEffect(() => { fetchConversations(); }, [fetchConversations]);

  // Load messages when switching to a conversation that has none yet
  useEffect(() => {
    if (!activeId) return;
    const convo = conversations.find((c) => c.id === activeId);
    if (!convo || convo.messages.length > 0) return;

    sdk.getMessages(activeId).then((msgs) => {
      setConversations((prev) => prev.map((c) =>
        c.id === activeId
          ? { ...c, messages: msgs.map((m) => ({ id: m.id, role: m.role, content: m.content, timestamp: new Date(m.createdAt) })) }
          : c
      ));
    }).catch(() => {});
  }, [activeId, conversations]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeConversation?.messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || sending) return;
    setErrorMsg("");

    // If no active conversation, create a local placeholder first
    let currentId = activeId;
    if (!currentId) {
      const tempId = `temp-${Date.now()}`;
      const newSessionId = crypto.randomUUID();
      const newConvo: Conversation = {
        id: tempId,
        title: text.slice(0, 60),
        sessionId: newSessionId,
        preview: text.slice(0, 50),
        timestamp: new Date(),
        messages: [],
      };
      setConversations((prev) => [newConvo, ...prev]);
      setActiveId(tempId);
      currentId = tempId;
    }

    const sessionId = conversations.find((c) => c.id === currentId)?.sessionId ?? crypto.randomUUID();

    // Optimistically add user message
    const tempUserMsg: Message = { id: `u-${Date.now()}`, role: "user", content: text, timestamp: new Date() };
    setConversations((prev) => prev.map((c) =>
      c.id === currentId ? { ...c, messages: [...c.messages, tempUserMsg] } : c
    ));
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    setSending(true);

    try {
      let responseText = "";

      for await (const event of sdk.streamAnalysis(text, sessionId)) {
        if (event.type === "status") {
          setStatusMsg(event.message);
        } else if (event.type === "result") {
          responseText = event.message;
          setStatusMsg("");
        } else if (event.type === "error") {
          throw new Error(event.message);
        }
        // "done" — nothing extra needed
      }

      if (!responseText) throw new Error("No response from ADK");

      const assistantMsg: Message = {
        id: `a-${Date.now()}`,
        role: "assistant",
        content: responseText,
        timestamp: new Date(),
      };

      setConversations((prev) => prev.map((c) =>
        c.id === currentId ? { ...c, messages: [...c.messages, assistantMsg], preview: text.slice(0, 50), timestamp: new Date() } : c
      ));

      // ADK already persisted — fetch updated list to swap temp id for real db id
      if (currentId?.startsWith("temp-")) {
        const updated = await sdk.getConversations();
        const match = updated.find((c) => c.sessionId === sessionId);
        if (match) {
          setConversations((prev) => prev.map((c) =>
            c.id === currentId
              ? { ...c, id: match.id, title: match.title ?? text.slice(0, 60) }
              : c
          ));
          setActiveId(match.id);
          router.replace(`/chat/${match.id}`);
        }
      }
    } catch (err) {
      setConversations((prev) => prev.map((c) =>
        c.id === currentId
          ? { ...c, messages: c.messages.filter((m) => m.id !== tempUserMsg.id) }
          : c
      ));
      setStatusMsg("");
      setErrorMsg(err instanceof Error ? err.message : "Something went wrong. Please try again.");
      console.error("[chat] send failed", err);
    } finally {
      setSending(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  }

  function handleTextareaChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + "px";
  }

  function newChat() {
    setActiveId(null);
    router.push("/chat");
  }

  async function handleDelete(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (activeId === id) {
      setActiveId(null);
      router.push("/chat");
    }
    try { await sdk.deleteConversation(id); } catch { await fetchConversations(); }
  }

  async function handleLogout() {
    const userId = localStorage.getItem("userId");
    if (userId) await sdk.logout(userId).catch(() => {});
    router.push("/auth/login");
  }

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {sidebarOpen && (
        <ChatSidebar
          conversations={conversations}
          loading={loadingConvos}
          activeId={activeId ?? ""}
          hoveredId={hoveredId}
          searchQuery={searchQuery}
          onSelect={(id) => { setActiveId(id); router.push(`/chat/${id}`); }}
          onHover={setHoveredId}
          onDelete={handleDelete}
          onNewChat={newChat}
          onSearchChange={setSearchQuery}
          onLogout={handleLogout}
        />
      )}

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
          <div className="flex items-center gap-3">
            <button onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors">
              <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5">
                <line x1="2" y1="4" x2="13" y2="4" />
                <line x1="2" y1="7.5" x2="13" y2="7.5" />
                <line x1="2" y1="11" x2="13" y2="11" />
              </svg>
            </button>
            <span className="text-sm font-medium text-foreground truncate max-w-xs">
              {activeConversation?.title ?? "New chat"}
            </span>
          </div>
          <button className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors px-2 py-1 rounded-md hover:bg-accent">
            <span className="text-sm font-medium">Model</span>
            <ChevronDown size={13} />
          </button>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          {!activeConversation || activeConversation.messages.length === 0 ? (
            <EmptyState onPrompt={(p) => { setInput(p); textareaRef.current?.focus(); }} />
          ) : (
            <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
              {activeConversation.messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
              {sending && (
                <div className="flex gap-2 items-start">
                  <div className="w-7 h-7 rounded-full bg-foreground flex items-center justify-center shrink-0">
                    <span className="text-[10px] text-background font-semibold">AI</span>
                  </div>
                  <div className="flex items-center gap-2 h-7">
                    {statusMsg ? (
                      <>
                        <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-pulse shrink-0" />
                        <span className="text-sm text-muted-foreground">{statusMsg}</span>
                      </>
                    ) : (
                      <>
                        <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:0ms]" />
                        <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:150ms]" />
                        <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:300ms]" />
                      </>
                    )}
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="px-4 pb-4 shrink-0">
          <div className="max-w-2xl mx-auto">
            {errorMsg && (
              <p className="text-xs text-destructive bg-destructive/5 border border-destructive/20 rounded-md px-3 py-2 mb-2">
                {errorMsg}
              </p>
            )}
            <div className="flex items-end gap-2 border border-border rounded-xl bg-input-background px-3 py-2.5 focus-within:border-ring transition-colors">
              <textarea ref={textareaRef} rows={1} value={input}
                onChange={handleTextareaChange} onKeyDown={handleKeyDown}
                placeholder="Ask about a stock or index…"
                className="flex-1 bg-transparent resize-none text-sm text-foreground placeholder:text-muted-foreground outline-none leading-relaxed max-h-48 overflow-y-auto"
              />
              <button onClick={handleSend} disabled={!input.trim() || sending}
                className="p-1.5 rounded-lg bg-primary text-primary-foreground disabled:opacity-30 hover:opacity-90 active:opacity-80 transition-opacity shrink-0">
                <Send size={14} />
              </button>
            </div>
            <p className="text-center text-xs text-muted-foreground mt-2">
              AI can make mistakes. Verify important information.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
