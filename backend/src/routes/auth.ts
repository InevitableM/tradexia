import { Router, Request, Response } from "express";
import * as authService from "../services/authService";

const router = Router();

// POST /api/auth/register
router.post("/register", async (req: Request, res: Response) => {
  console.log(`[route] POST /api/auth/register body=${JSON.stringify({ ...req.body, password: "***" })}`);
  try {
    const result = await authService.register(req.body);
    res.status(201).json({ success: true, data: result });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Registration failed";
    const status = message === "Email already registered" ? 409 : 400;
    console.error(`[route] register failed — ${message}`);
    res.status(status).json({ success: false, error: message });
  }
});

// POST /api/auth/login
router.post("/login", async (req: Request, res: Response) => {
  try {
    const result = await authService.login(req.body);
    res.json({ success: true, data: {
      userId: result.userId,
      email: result.email,
      name: result.name,
      accessToken: result.accessToken,
    }});
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Login failed";
    const status = message === "Invalid credentials" ? 401
                 : message === "Email not verified"  ? 403
                 : 400;
    res.status(status).json({ success: false, error: message });
  }
});

// GET /api/auth/verify?token=xxx
// Called when user clicks the link in their email.
// Marks the user verified then redirects to login with a flag.
router.get("/verify", async (req: Request, res: Response) => {
  const token = req.query.token as string | undefined;
  const frontendUrl = process.env.FRONTEND_URL || "http://localhost:3000";

  if (!token) {
    res.redirect(`${frontendUrl}/auth/login?verified=invalid`);
    return;
  }

  try {
    await authService.verifyEmail(token);
    res.redirect(`${frontendUrl}/auth/login?verified=true`);
  } catch {
    res.redirect(`${frontendUrl}/auth/login?verified=expired`);
  }
});

// POST /api/auth/resend-verification  — body: { email }
router.post("/resend-verification", async (req: Request, res: Response) => {
  try {
    const { email } = req.body as { email?: string };
    if (!email) {
      res.status(400).json({ success: false, error: "email is required" });
      return;
    }
    await authService.resendVerification(email);
    // Always return success to avoid revealing whether the email exists
    res.json({ success: true, data: { message: "If that email is registered, a new verification link has been sent" } });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Failed to resend";
    const status = message === "Please wait before requesting another email" ? 429 : 400;
    res.status(status).json({ success: false, error: message });
  }
});

// POST /api/auth/google  — body: { idToken }
router.post("/google", async (req: Request, res: Response) => {
  try {
    const { idToken } = req.body as { idToken?: string };
    if (!idToken) {
      res.status(400).json({ success: false, error: "idToken is required" });
      return;
    }
    const outcome = await authService.googleLogin(idToken);

    if (outcome.status === "logged_in") {
      res.json({ success: true, data: {
        status: "logged_in",
        userId: outcome.result.userId,
        email: outcome.result.email,
        name: outcome.result.name,
        accessToken: outcome.result.accessToken,
      }});
    } else {
      res.json({ success: true, data: {
        status: "new_user",
        signupToken: outcome.signupToken,
        email: outcome.email,
        name: outcome.name,
      }});
    }
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Google sign-in failed";
    console.error(`[route] google login failed — ${message}`);
    res.status(401).json({ success: false, error: message });
  }
});

// POST /api/auth/google/complete  — body: { signupToken, password, name? }
router.post("/google/complete", async (req: Request, res: Response) => {
  try {
    const result = await authService.completeGoogleSignup(req.body);
    res.status(201).json({ success: true, data: {
      userId: result.userId,
      email: result.email,
      name: result.name,
      accessToken: result.accessToken,
    }});
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Could not complete signup";
    const status = message === "Email already registered" ? 409 : 400;
    res.status(status).json({ success: false, error: message });
  }
});

// POST /api/auth/refresh  — body: { userId }
router.post("/refresh", async (req: Request, res: Response) => {
  try {
    const { userId } = req.body as { userId?: string };
    if (!userId) {
      res.status(400).json({ success: false, error: "userId is required" });
      return;
    }
    const accessToken = await authService.refreshByUserId(userId);
    res.json({ success: true, data: { accessToken } });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Token refresh failed";
    res.status(401).json({ success: false, error: message });
  }
});

// POST /api/auth/logout  — body: { userId }
router.post("/logout", async (req: Request, res: Response) => {
  try {
    const { userId } = req.body as { userId?: string };
    if (!userId) {
      res.status(400).json({ success: false, error: "userId is required" });
      return;
    }
    await authService.logout(userId);
    res.json({ success: true, message: "Logged out" });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Logout failed";
    res.status(500).json({ success: false, error: message });
  }
});

export default router;
