import { Response, NextFunction } from "express";
import { AuthRequest } from "../types";
import { verifyAccessToken } from "../services/authService";

export function authenticate(req: AuthRequest, res: Response, next: NextFunction): void {
  const header = req.headers.authorization;
  if (!header || !header.startsWith("Bearer ")) {
    res.status(401).json({ success: false, error: "Missing or malformed Authorization header" });
    return;
  }

  const token = header.slice(7);
  try {
    const payload = verifyAccessToken(token);
    req.user = payload;
    console.log(`[requestHandler] authenticated userId=${payload.userId}`);
    next();
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Unauthorized";
    const status = message.includes("expired") ? 401 : 403;
    console.warn(`[requestHandler] auth failed — ${message}`);
    res.status(status).json({ success: false, error: message });
  }
}
