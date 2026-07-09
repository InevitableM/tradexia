import { Router, Response } from "express";
import { authenticate } from "../middleware/requestHandler";
import { AuthRequest } from "../types";
import { runAnalysis, streamAnalysis } from "../services/adkClient";
import { backendSdk } from "../services/backendSdk";

const router = Router();

// POST /api/analysis
// Body: { query, sessionId }
router.post("/", authenticate, async (req: AuthRequest, res: Response) => {
  try {
    const { query, sessionId } = req.body as { query?: string; sessionId?: string };

    if (!query) {
      res.status(400).json({ success: false, error: "query is required" });
      return;
    }
    if (!sessionId) {
      res.status(400).json({ success: false, error: "sessionId is required" });
      return;
    }

    const userId = req.user!.userId;

    const quota = await backendSdk.checkAndIncrementAnalysisQuota(userId);
    if (!quota.allowed) {
      res.status(429).json({
        success: false,
        error: "Daily analysis limit reached. Try again after 24 hours.",
        data: { limit: quota.limit, remaining: 0, resetsInSeconds: quota.resetsInSeconds },
      });
      return;
    }

    const accessToken = req.headers.authorization!.slice(7);
    const result = await runAnalysis({ query, session_id: sessionId, user_id: userId, access_token: accessToken });

    res.json({ success: true, data: { ...result, quota: { limit: quota.limit, remaining: quota.remaining } } });
  } catch (err) {
    console.error("[analysis]", err);
    res.status(502).json({ success: false, error: "ADK service unavailable" });
  }
});

// POST /api/analysis/stream
// Pipes ADK's SSE stream directly to the browser.
// Body: { query, sessionId }
router.post("/stream", authenticate, async (req: AuthRequest, res: Response) => {
  const { query, sessionId } = req.body as { query?: string; sessionId?: string };

  if (!query) { res.status(400).json({ success: false, error: "query is required" }); return; }
  if (!sessionId) { res.status(400).json({ success: false, error: "sessionId is required" }); return; }

  const userId = req.user!.userId;
  const accessToken = req.headers.authorization!.slice(7);

  const quota = await backendSdk.checkAndIncrementAnalysisQuota(userId);
  if (!quota.allowed) {
    res.status(429).json({
      success: false,
      error: "Daily analysis limit reached. Try again later.",
      data: { limit: quota.limit, remaining: 0, resetsInSeconds: quota.resetsInSeconds },
    });
    return;
  }

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders();

  try {
    const stream = await streamAnalysis({ query, session_id: sessionId, user_id: userId, access_token: accessToken });
    const nodeStream = stream as import("stream").Readable;
    nodeStream.pipe(res);
    nodeStream.on("error", (err) => {
      console.error("[analysis/stream] ADK stream error:", err);
      res.write(`data: ${JSON.stringify({ type: "error", message: "ADK stream error" })}\n\n`);
      res.end();
    });
    req.on("close", () => nodeStream.destroy());
  } catch (err) {
    console.error("[analysis/stream]", err);
    res.write(`data: ${JSON.stringify({ type: "error", message: "ADK service unavailable" })}\n\n`);
    res.end();
  }
});

export default router;
