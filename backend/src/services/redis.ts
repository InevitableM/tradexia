import Redis from "ioredis";

let client: Redis | null = null;

export function getRedisClient(): Redis {
  if (!client) {
    const url = process.env.REDIS_URL || "redis://localhost:6379";
    client = new Redis(url, {
      maxRetriesPerRequest: 3,
      lazyConnect: true,
    });

    client.on("connect", () => console.log("[redis] connected"));
    client.on("error", (err) => console.error("[redis] error:", err.message));
  }
  return client;
}

export async function cacheGet<T>(key: string): Promise<T | null> {
  try {
    const val = await getRedisClient().get(key);
    return val ? (JSON.parse(val) as T) : null;
  } catch {
    return null;
  }
}

export async function cacheSet(key: string, value: unknown, ttlSeconds: number): Promise<void> {
  try {
    await getRedisClient().set(key, JSON.stringify(value), "EX", ttlSeconds);
  } catch (err) {
    console.error("[redis] cache set failed:", err);
  }
}

export async function cacheDel(key: string): Promise<void> {
  try {
    await getRedisClient().del(key);
  } catch (err) {
    console.error("[redis] cache del failed:", err);
  }
}
