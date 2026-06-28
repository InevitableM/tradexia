/**
 * Auth routes — register / login / refresh / logout
 *
 * NOTE: User persistence (DB lookup/insert) is stubbed out with TODOs.
 * Drop in your chosen DB client (Prisma, Mongoose, etc.) when ready.
 */

import { Router, Request, Response } from "express";
import bcrypt from "bcryptjs";
import { generateTokens, verifyRefreshToken } from "../middleware/auth";
import { cacheDel, cacheGet, cacheSet } from "../services/redis";

const router = Router();

const REFRESH_TTL = 30 * 24 * 60 * 60; // 30 days in seconds

// ---------------------------------------------------------------------------
// POST /api/auth/register
// ---------------------------------------------------------------------------
router.post("/register", async (req: Request, res: Response) => {
  try {
    const { email, password, name } = req.body as {
      email?: string;
      password?: string;
      name?: string;
    };

    if (!email || !password) {
      res.status(400).json({ success: false, error: "email and password are required" });
      return;
    }

    // TODO: check if user already exists in DB
    // const existing = await db.user.findUnique({ where: { email } });
    // if (existing) { res.status(409).json(...); return; }

    const passwordHash = await bcrypt.hash(password, 12);

    // TODO: insert user into DB and get back a real userId
    // const user = await db.user.create({ data: { email, name, passwordHash } });
    const userId = `stub_${Date.now()}`; // remove once DB is wired

    const { accessToken, refreshToken } = generateTokens(userId, email);

    // Store refresh token in Redis so we can invalidate it on logout
    await cacheSet(`refresh:${userId}`, refreshToken, REFRESH_TTL);

    res.status(201).json({
      success: true,
      data: { userId, email, name, accessToken, refreshToken },
    });
  } catch (err) {
    console.error("[auth/register]", err);
    res.status(500).json({ success: false, error: "Registration failed" });
  }
});

// ---------------------------------------------------------------------------
// POST /api/auth/login
// ---------------------------------------------------------------------------
router.post("/login", async (req: Request, res: Response) => {
  try {
    const { email, password } = req.body as { email?: string; password?: string };

    if (!email || !password) {
      res.status(400).json({ success: false, error: "email and password are required" });
      return;
    }

    // TODO: look up user in DB
    // const user = await db.user.findUnique({ where: { email } });
    // if (!user) { res.status(401).json({ success: false, error: "Invalid credentials" }); return; }
    //
    // const valid = await bcrypt.compare(password, user.passwordHash);
    // if (!valid) { res.status(401).json({ success: false, error: "Invalid credentials" }); return; }

    // STUB — remove once DB is wired
    const userId = `stub_user`;
    const passwordHash = await bcrypt.hash("stubpassword", 12);
    const valid = await bcrypt.compare(password, passwordHash);
    if (!valid && password !== "stubpassword") {
      res.status(401).json({ success: false, error: "Invalid credentials" });
      return;
    }

    const { accessToken, refreshToken } = generateTokens(userId, email);
    await cacheSet(`refresh:${userId}`, refreshToken, REFRESH_TTL);

    res.json({ success: true, data: { userId, email, accessToken, refreshToken } });
  } catch (err) {
    console.error("[auth/login]", err);
    res.status(500).json({ success: false, error: "Login failed" });
  }
});

// ---------------------------------------------------------------------------
// POST /api/auth/refresh
// ---------------------------------------------------------------------------
router.post("/refresh", async (req: Request, res: Response) => {
  try {
    const { refreshToken } = req.body as { refreshToken?: string };

    if (!refreshToken) {
      res.status(400).json({ success: false, error: "refreshToken is required" });
      return;
    }

    const payload = verifyRefreshToken(refreshToken);

    // Verify the token in Redis matches (guards against reuse after logout)
    const stored = await cacheGet<string>(`refresh:${payload.userId}`);
    if (stored !== refreshToken) {
      res.status(401).json({ success: false, error: "Refresh token invalid or revoked" });
      return;
    }

    const { accessToken, refreshToken: newRefreshToken } = generateTokens(
      payload.userId,
      payload.email
    );

    // Rotate refresh token
    await cacheSet(`refresh:${payload.userId}`, newRefreshToken, REFRESH_TTL);

    res.json({ success: true, data: { accessToken, refreshToken: newRefreshToken } });
  } catch {
    res.status(401).json({ success: false, error: "Invalid or expired refresh token" });
  }
});

// ---------------------------------------------------------------------------
// POST /api/auth/logout
// ---------------------------------------------------------------------------
router.post("/logout", async (req: Request, res: Response) => {
  try {
    const { userId } = req.body as { userId?: string };
    if (userId) {
      await cacheDel(`refresh:${userId}`);
    }
    res.json({ success: true, message: "Logged out" });
  } catch (err) {
    console.error("[auth/logout]", err);
    res.status(500).json({ success: false, error: "Logout failed" });
  }
});

export default router;
