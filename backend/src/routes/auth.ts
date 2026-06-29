import { Router, Request, Response } from "express";
import * as authService from "../services/authService";

const router = Router();

// POST /api/auth/register
router.post("/register", async (req: Request, res: Response) => {
  console.log(`[route] POST /api/auth/register body=${JSON.stringify({ ...req.body, password: "***" })}`);
  try {
    const result = await authService.register(req.body);
    console.log(`[route] register success userId=${result.userId}`);
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
    res.json({ success: true, data: result });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Login failed";
    const status = message === "Invalid credentials" ? 401 : 400;
    res.status(status).json({ success: false, error: message });
  }
});

// POST /api/auth/refresh
router.post("/refresh", async (req: Request, res: Response) => {
  try {
    const { refreshToken } = req.body as { refreshToken?: string };
    if (!refreshToken) {
      res.status(400).json({ success: false, error: "refreshToken is required" });
      return;
    }
    const result = await authService.refreshTokens(refreshToken);
    res.json({ success: true, data: result });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Token refresh failed";
    res.status(401).json({ success: false, error: message });
  }
});

// POST /api/auth/logout
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
