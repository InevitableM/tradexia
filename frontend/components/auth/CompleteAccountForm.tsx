"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { MessageSquare, Eye, EyeOff } from "lucide-react";
import * as sdk from "@/lib/sdk";

const INPUT_CLS = "w-full px-3 py-2.5 text-sm text-foreground rounded-lg border border-border bg-input-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all";

export default function CompleteAccountForm() {
  const router = useRouter();
  const [signupToken, setSignupToken] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = sessionStorage.getItem("googleSignupToken");
    if (!token) {
      router.replace("/auth/signup");
      return;
    }
    setSignupToken(token);
    setEmail(sessionStorage.getItem("googleSignupEmail") || "");
    setName(sessionStorage.getItem("googleSignupName") || "");
  }, [router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (password.length < 8) { setError("Password must be at least 8 characters."); return; }
    if (password !== confirm) { setError("Passwords do not match."); return; }
    if (!signupToken) { setError("Signup session expired. Please try again."); return; }

    setLoading(true);
    try {
      const result = await sdk.completeGoogleSignup(signupToken, password, name || undefined);
      sessionStorage.removeItem("googleSignupToken");
      sessionStorage.removeItem("googleSignupEmail");
      sessionStorage.removeItem("googleSignupName");
      localStorage.setItem("accessToken", result.accessToken);
      localStorage.setItem("userId", result.userId);
      router.push("/chat");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Could not complete signup");
    } finally {
      setLoading(false);
    }
  }

  if (!signupToken) return null;

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3">
          <div className="w-9 h-9 bg-foreground rounded-lg flex items-center justify-center">
            <MessageSquare size={18} className="text-background" />
          </div>
          <div className="text-center">
            <h1 className="text-xl font-semibold text-foreground tracking-tight">Almost there</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Set a password to finish creating your account
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground" htmlFor="ca-email">Email</label>
            <input id="ca-email" type="email" value={email} disabled
              className={`${INPUT_CLS} opacity-60`} />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground" htmlFor="ca-name">Name</label>
            <input id="ca-name" type="text" value={name} onChange={(e) => setName(e.target.value)}
              placeholder="Your name" className={INPUT_CLS} />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground" htmlFor="ca-password">Password</label>
            <div className="relative">
              <input id="ca-password" type={showPassword ? "text" : "password"} value={password}
                onChange={(e) => setPassword(e.target.value)} placeholder="Min. 8 characters" required
                className={`${INPUT_CLS} pr-10`} />
              <button type="button" onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors">
                {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground" htmlFor="ca-confirm">Confirm password</label>
            <div className="relative">
              <input id="ca-confirm" type={showConfirm ? "text" : "password"} value={confirm}
                onChange={(e) => setConfirm(e.target.value)} placeholder="Repeat your password" required
                className={`${INPUT_CLS} pr-10`} />
              <button type="button" onClick={() => setShowConfirm(!showConfirm)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors">
                {showConfirm ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>

          {error && (
            <p className="text-xs text-destructive bg-destructive/5 border border-destructive/20 rounded-md px-3 py-2">
              {error}
            </p>
          )}

          <button type="submit" disabled={loading}
            className="w-full mt-1 bg-primary text-primary-foreground rounded-lg px-4 py-2.5 text-sm font-medium hover:opacity-90 active:opacity-80 transition-opacity disabled:opacity-50">
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>
      </div>
    </div>
  );
}
