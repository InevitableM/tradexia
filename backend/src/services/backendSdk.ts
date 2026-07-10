// Composition layer for logic that needs both Postgres and Redis together.
// Single-concern calls (just DB, just cache) should keep using db /
// conversationService / redis directly — this file is for things that span both.

import { redis } from "./redis";

export interface QuotaCheckResult {
  allowed: boolean;
  remaining: number;
  limit: number;
  resetsInSeconds: number;
}

class BackendSdk {
  async checkAndIncrementAnalysisQuota(
    userId: string,
  ): Promise<QuotaCheckResult> {
    const dailyLimit = Number(process.env.DAILY_ANALYSIS_LIMIT) || 20;
    const windowSeconds =
      Number(process.env.ANALYSIS_QUOTA_WINDOW_SECONDS) || 24 * 60 * 60;

    const client = redis.client;
    const key = `quota:analysis:${userId}`;

    try {
      const count = await client.incr(key);
      let ttl: number;
      if (count === 1) {
        await client.expire(key, windowSeconds);
        ttl = windowSeconds;
      } else {
        ttl = await client.ttl(key);
        if (ttl < 0) {
          // Self-heal: a key without a TTL would never reset. Only reachable if a
          // prior request incremented but crashed before its EXPIRE call landed.
          await client.expire(key, windowSeconds);
          ttl = windowSeconds;
        }
      }

      return {
        allowed: count <= dailyLimit,
        remaining: Math.max(0, dailyLimit - count),
        limit: dailyLimit,
        resetsInSeconds: ttl,
      };
    } catch (err) {
      console.error("[backendSdk] quota check failed, failing open:", err);
      // If Redis is down, don't block users from using the app — fail open.
      return {
        allowed: true,
        remaining: dailyLimit,
        limit: dailyLimit,
        resetsInSeconds: windowSeconds,
      };
    }
  }
}

// Instantiated once here; every importer of `backendSdk` shares this instance.
// Only the methods listed below are part of the public surface.
const instance = new BackendSdk();

export const backendSdk = {
  checkAndIncrementAnalysisQuota:
    instance.checkAndIncrementAnalysisQuota.bind(instance),
};
