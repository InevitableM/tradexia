import { Router, Response } from "express";
import { authenticate } from "../middleware/auth";
import { AuthRequest } from "../types";
import { runAnalysis } from "../services/adkClient";
import { cacheGet, cacheSet } from "../services/redis";
import { v4 as uuidv4 } from "uuid";

const router = Router();

const ANALYSIS_CACHE_TTL = 300; // 5 minutes

// POST /api/analysis
router.post("/", authenticate, async (req: AuthRequest, res: Response) => {
  try {
    const { query, symbol } = req.body as { query?: string; symbol?: string };

    if (!query) {
      res.status(400).json({ success: false, error: "query is required" });
      return;
    }

    const userId = req.user!.userId;
    const cacheKey = `analysis:${symbol || ""}:${Buffer.from(query).toString("base64").slice(0, 32)}`;

    // const cached = await cacheGet(cacheKey);
    // if (cached) {
    //   res.json({ success: true, data: cached, cached: true });
    //   return;
    // }

    const sessionId = uuidv4();
    const result = await runAnalysis({ query, symbol, sessionId, userId });

    // await cacheSet(cacheKey, result, ANALYSIS_CACHE_TTL);
    res.json({ success: true, data: result, cached: false });
  } catch (err) {
    console.error("[analysis]", err);
    res.status(502).json({ success: false, error: "ADK service unavailable" });
  }
});

export default router;
