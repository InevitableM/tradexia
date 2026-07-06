"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { MessageSquare, Eye, EyeOff } from "lucide-react";
import * as sdk from "@/lib/sdk";
import GoogleSignInButton from "./GoogleSignInButton";

const INPUT_CLS = "w-full px-3 py-2.5 text-sm text-foreground rounded-lg border border-border bg-input-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all";

export default function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [banner, setBanner] = useState("");
  const [resending, setResending] = useState(false);
  const [resendMsg, setResendMsg] = useState("");

  useEffect(() => {
    const v = searchParams.get("verified");
    if (v === "true")    setBanner("Email verified! You can now sign in.");
    if (v === "expired") setBanner("Verification link expired. Sign in to request a new one.");
    if (v === "invalid") setBanner("Invalid verification link.");
  }, [searchParams]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setResendMsg("");
    setLoading(true);
    try {
      const result = await sdk.login(email, password);
      localStorage.setItem("accessToken", result.accessToken);
      localStorage.setItem("userId", result.userId);
      router.push("/chat");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Login failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogleToken(idToken: string) {
    setError("");
    setLoading(true);
    try {
      const result = await sdk.googleLogin(idToken);
      if (result.status === "logged_in") {
        localStorage.setItem("accessToken", result.accessToken);
        localStorage.setItem("userId", result.userId);
        router.push("/chat");
      } else {
        sessionStorage.setItem("googleSignupToken", result.signupToken);
        sessionStorage.setItem("googleSignupEmail", result.email);
        if (result.name) sessionStorage.setItem("googleSignupName", result.name);
        router.push("/auth/complete");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Google sign-in failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleResend() {
    if (!email) { setResendMsg("Enter your email above first."); return; }
    setResending(true);
    setResendMsg("");
    try {
      await sdk.resendVerification(email);
      setResendMsg("Verification email sent — check your inbox.");
    } catch (err: unknown) {
      setResendMsg(err instanceof Error ? err.message : "Could not resend email.");
    } finally {
      setResending(false);
    }
  }

  const isUnverified = error === "Email not verified";

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3">
          <div className="w-9 h-9 bg-foreground rounded-lg flex items-center justify-center">
            <MessageSquare size={18} className="text-background" />
          </div>
          <div className="text-center">
            <h1 className="text-xl font-semibold text-foreground tracking-tight">Welcome back</h1>
            <p className="text-sm text-muted-foreground mt-1">Sign in to your account</p>
          </div>
        </div>

        {banner && (
          <p className={`text-xs rounded-md px-3 py-2 mb-4 text-center ${
            banner.startsWith("Email verified")
              ? "bg-green-50 text-green-700 border border-green-200"
              : "bg-accent text-muted-foreground"
          }`}>
            {banner}
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground" htmlFor="email">Email</label>
            <input id="email" type="email" value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com" required className={INPUT_CLS} />
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-foreground" htmlFor="password">Password</label>
              <button type="button" className="text-xs text-muted-foreground hover:text-foreground transition-colors">
                Forgot password?
              </button>
            </div>
            <div className="relative">
              <input id="password" type={showPassword ? "text" : "password"} value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••" required className={`${INPUT_CLS} pr-10`} />
              <button type="button" onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors">
                {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>

          {error && (
            <div className="text-xs text-destructive bg-destructive/5 border border-destructive/20 rounded-md px-3 py-2">
              <p>{error}</p>
              {isUnverified && (
                <div className="mt-1.5 flex items-center gap-2">
                  <button type="button" onClick={handleResend} disabled={resending}
                    className="underline underline-offset-2 hover:opacity-70 disabled:opacity-50 transition-opacity">
                    {resending ? "Sending…" : "Resend verification email"}
                  </button>
                  {resendMsg && <span className="text-muted-foreground">— {resendMsg}</span>}
                </div>
              )}
            </div>
          )}

          <button type="submit" disabled={loading}
            className="w-full mt-1 bg-primary text-primary-foreground rounded-lg px-4 py-2.5 text-sm font-medium hover:opacity-90 active:opacity-80 transition-opacity disabled:opacity-50">
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <div className="flex items-center gap-3 my-5">
          <div className="h-px bg-border flex-1" />
          <span className="text-xs text-muted-foreground">or</span>
          <div className="h-px bg-border flex-1" />
        </div>

        <GoogleSignInButton onToken={handleGoogleToken} />

        <p className="text-center text-sm text-muted-foreground mt-5">
          {"Don't have an account? "}
          <Link href="/auth/signup" className="text-foreground font-medium hover:underline underline-offset-2">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
