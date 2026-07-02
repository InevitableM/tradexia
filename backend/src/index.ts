import "dotenv/config";
import express from "express";
import cors from "cors";
import helmet from "helmet";
import rateLimit from "express-rate-limit";

import authRouter from "./routes/auth";
import analysisRouter from "./routes/analysis";
import conversationsRouter from "./routes/conversations";

const app = express();
const PORT = process.env.PORT || 4000;

// Security & parsing
app.use(helmet());
app.use(cors({ origin: process.env.FRONTEND_URL || "http://localhost:3000", credentials: true }));
app.use(express.json());

// Global rate limit
app.use(
  rateLimit({
    windowMs: Number(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000,
    max: Number(process.env.RATE_LIMIT_MAX) || 100,
    standardHeaders: true,
    legacyHeaders: false,
  })
);

// Routes
app.use("/api/auth", authRouter);
app.use("/api/analysis", analysisRouter);
app.use("/api/conversations", conversationsRouter);

// 404
app.use((_req, res) => {
  res.status(404).json({ success: false, error: "Route not found" });
});

app.listen(PORT, () => {
  console.log(`[backend] running on http://localhost:${PORT}`);
});

export default app;
