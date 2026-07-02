import { Router, Response } from "express";
import { authenticate } from "../middleware/requestHandler";
import { AuthRequest } from "../types";
import { runAnalysis } from "../services/adkClient";

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
    // Forward the raw JWT so ADK can call /api/conversations on our behalf
    const accessToken = req.headers.authorization!.slice(7);
    const result = await runAnalysis({ query, session_id: sessionId, user_id: userId, access_token: accessToken });

    res.json({ success: true, data: result });
  } catch (err) {
    console.error("[analysis]", err);
    res.status(502).json({ success: false, error: "ADK service unavailable" });
  }
});

export default router;
