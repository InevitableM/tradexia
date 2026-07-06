"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { MessageSquare, Eye, EyeOff, Mail } from "lucide-react";
import * as sdk from "@/lib/sdk";
import GoogleSignInButton from "./GoogleSignInButton";

const INPUT_CLS = "w-full px-3 py-2.5 text-sm text-foreground rounded-lg border border-border bg-input-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all";

export default function SignupForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [resending, setResending] = useState(false);
  const [resendMsg, setResendMsg] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (password.length < 8) { setError("Password must be at least 8 characters."); return; }
    if (password !== confirm) { setError("Passwords do not match."); return; }
    setLoading(true);
    try {
      await sdk.register(email, password, name || undefined);
      setDone(true);

    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
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
    setResending(true);
    setResendMsg("");
    try {
      await sdk.resendVerification(email);
      setResendMsg("Verification email resent — check your inbox.");
    } catch (err: unknown) {
      setResendMsg(err instanceof Error ? err.message : "Could not resend email.");
    } finally {
      setResending(false);
    }
  }

  // ── Check-your-email screen ──────────────────────────────────────────────
  if (done) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4">
        <div className="w-full max-w-sm text-center">
          <div className="w-12 h-12 rounded-full bg-accent flex items-center justify-center mx-auto mb-5">
            <Mail size={22} className="text-foreground" />
          </div>
          <h1 className="text-xl font-semibold text-foreground tracking-tight mb-2">Check your email</h1>
          <p className="text-sm text-muted-foreground leading-relaxed mb-1">
            We sent a verification link to
          </p>
          <p className="text-sm font-medium text-foreground mb-6">{email}</p>
          <p className="text-xs text-muted-foreground mb-6">
            Click the link in the email to verify your account. The link expires in 24 hours.
            <br />
            Don&apos;t see it? Check your spam or junk folder.
          </p>

          {resendMsg && (
            <p className="text-xs text-muted-foreground bg-accent rounded-md px-3 py-2 mb-4">
              {resendMsg}
            </p>
          )}

          <button onClick={handleResend} disabled={resending}
            className="text-sm text-foreground font-medium hover:underline underline-offset-2 disabled:opacity-50">
            {resending ? "Sending…" : "Resend verification email"}
          </button>

          <p className="text-center text-sm text-muted-foreground mt-6">
            <Link href="/auth/login" className="text-foreground font-medium hover:underline underline-offset-2">
              Back to sign in
            </Link>
          </p>
        </div>
      </div>
    );
  }

  // ── Sign-up form ─────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3">
          <div className="w-9 h-9 bg-foreground rounded-lg flex items-center justify-center">
            <MessageSquare size={18} className="text-background" />
          </div>
          <div className="text-center">
            <h1 className="text-xl font-semibold text-foreground tracking-tight">Create an account</h1>
            <p className="text-sm text-muted-foreground mt-1">Get started for free</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground" htmlFor="su-name">Name</label>
            <input id="su-name" type="text" value={name} onChange={(e) => setName(e.target.value)}
              placeholder="Your name" className={INPUT_CLS} />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground" htmlFor="su-email">Email</label>
            <input id="su-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com" required className={INPUT_CLS} />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground" htmlFor="su-password">Password</label>
            <div className="relative">
              <input id="su-password" type={showPassword ? "text" : "password"} value={password}
                onChange={(e) => setPassword(e.target.value)} placeholder="Min. 8 characters" required
                className={`${INPUT_CLS} pr-10`} />
              <button type="button" onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors">
                {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground" htmlFor="su-confirm">Confirm password</label>
            <div className="relative">
              <input id="su-confirm" type={showConfirm ? "text" : "password"} value={confirm}
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

        <div className="flex items-center gap-3 my-5">
          <div className="h-px bg-border flex-1" />
          <span className="text-xs text-muted-foreground">or</span>
          <div className="h-px bg-border flex-1" />
        </div>

        <GoogleSignInButton onToken={handleGoogleToken} />

        <p className="text-center text-xs text-muted-foreground mt-4 leading-relaxed">
          By creating an account you agree to our{" "}
          <button className="text-foreground hover:underline underline-offset-2">Terms</button> and{" "}
          <button className="text-foreground hover:underline underline-offset-2">Privacy Policy</button>.
        </p>

        <p className="text-center text-sm text-muted-foreground mt-5">
          Already have an account?{" "}
          <Link href="/auth/login" className="text-foreground font-medium hover:underline underline-offset-2">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
