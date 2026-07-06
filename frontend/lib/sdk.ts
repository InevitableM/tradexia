const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:4000";

function getHeaders(): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("accessToken");
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function request<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { ...getHeaders(), ...(options.headers ?? {}) },
  });

  // Auto-refresh on 401 — but not for auth endpoints themselves
  const isAuthRoute = path.startsWith("/api/auth/");
  if (res.status === 401 && retry && !isAuthRoute && typeof window !== "undefined") {
    const userId = localStorage.getItem("userId");
    if (userId) {
      try {
        const refreshRes = await fetch(`${BASE_URL}/api/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ userId }),
        });
        if (refreshRes.ok) {
          const { data } = await refreshRes.json();
          localStorage.setItem("accessToken", data.accessToken);
          return request<T>(path, options, false);
        }
      } catch {
        // fall through to clear session
      }
    }
    localStorage.removeItem("accessToken");
    localStorage.removeItem("userId");
    window.location.href = "/auth/login";
    throw new Error("Session expired");
  }

  const data = await res.json();
  if (!res.ok) throw new Error(data.error || `Request failed with status ${res.status}`);
  return data;
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface AuthResult {
  userId: string;
  email: string;
  name?: string;
  accessToken: string;
}

export async function register(email: string, password: string, name?: string): Promise<{ message: string }> {
  const res = await request<{ success: boolean; data: { message: string } }>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, name }),
  });
  return res.data;
}

export async function resendVerification(email: string): Promise<void> {
  await request("/api/auth/resend-verification", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function login(email: string, password: string): Promise<AuthResult> {
  const res = await request<{ success: boolean; data: AuthResult }>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  return res.data;
}

export type GoogleLoginResult =
  | ({ status: "logged_in" } & AuthResult)
  | { status: "new_user"; signupToken: string; email: string; name?: string };

export async function googleLogin(idToken: string): Promise<GoogleLoginResult> {
  const res = await request<{ success: boolean; data: GoogleLoginResult }>("/api/auth/google", {
    method: "POST",
    body: JSON.stringify({ idToken }),
  });
  return res.data;
}

export async function completeGoogleSignup(
  signupToken: string,
  password: string,
  name?: string
): Promise<AuthResult> {
  const res = await request<{ success: boolean; data: AuthResult }>("/api/auth/google/complete", {
    method: "POST",
    body: JSON.stringify({ signupToken, password, name }),
  });
  return res.data;
}

export async function logout(userId: string): Promise<void> {
  await request("/api/auth/logout", {
    method: "POST",
    body: JSON.stringify({ userId }),
  });
  if (typeof window !== "undefined") {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("userId");
  }
}

// ─── Conversations ────────────────────────────────────────────────────────────

export interface ConversationSummary {
  id: string;
  userId: string;
  title: string | null;
  sessionId: string;
  createdAt: string;
  updatedAt: string;
}

export interface MessageRecord {
  id: string;
  conversationId: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
}

export async function getConversations(): Promise<ConversationSummary[]> {
  const res = await request<{ success: boolean; data: ConversationSummary[] }>("/api/conversations");
  return res.data;
}

export async function getMessages(conversationId: string): Promise<MessageRecord[]> {
  const res = await request<{ success: boolean; data: MessageRecord[] }>(`/api/conversations/${conversationId}/messages`);
  return res.data;
}

export async function saveConversation(
  sessionId: string,
  userMessage: string,
  assistantMessage: string
): Promise<{ conversation: ConversationSummary; messages: MessageRecord[] }> {
  const res = await request<{ success: boolean; data: { conversation: ConversationSummary; messages: MessageRecord[] } }>("/api/conversations", {
    method: "POST",
    body: JSON.stringify({ sessionId, userMessage, assistantMessage }),
  });
  return res.data;
}

export async function deleteConversation(id: string): Promise<void> {
  await request(`/api/conversations/${id}`, { method: "DELETE" });
}

// ─── Analysis ─────────────────────────────────────────────────────────────────

export type StreamEvent =
  | { type: "status"; message: string }
  | { type: "result"; message: string }
  | { type: "error"; message: string }
  | { type: "done" };

export async function* streamAnalysis(
  query: string,
  sessionId: string
): AsyncGenerator<StreamEvent> {
  const token = typeof window !== "undefined" ? localStorage.getItem("accessToken") : null;
  const res = await fetch(`${BASE_URL}/api/analysis/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ query, sessionId }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: "Stream failed" }));
    yield { type: "error", message: err.error ?? "Stream failed" };
    return;
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const raw = line.slice(6).trim();
      if (!raw) continue;
      try {
        yield JSON.parse(raw) as StreamEvent;
      } catch {
        // malformed line — skip
      }
    }
  }
}
