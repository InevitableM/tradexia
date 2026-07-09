import Redis from "ioredis";

class RedisClient {
  readonly client: Redis;

  constructor() {
    const url = process.env.REDIS_URL || "redis://localhost:6379";
    this.client = new Redis(url, {
      maxRetriesPerRequest: 3,
      lazyConnect: true,
    });

    this.client.on("connect", () => console.log("[redis] connected"));
    this.client.on("error", (err) => console.error("[redis] error:", err.message));
  }

  async cacheGet<T>(key: string): Promise<T | null> {
    try {
      const val = await this.client.get(key);
      return val ? (JSON.parse(val) as T) : null;
    } catch {
      return null;
    }
  }

  async cacheSet(key: string, value: unknown, ttlSeconds: number): Promise<void> {
    try {
      await this.client.set(key, JSON.stringify(value), "EX", ttlSeconds);
    } catch (err) {
      console.error("[redis] cache set failed:", err);
    }
  }

  async cacheDel(key: string): Promise<void> {
    try {
      await this.client.del(key);
    } catch (err) {
      console.error("[redis] cache del failed:", err);
    }
  }
}

// Instantiated once here so every importer shares the single underlying
// ioredis connection. Only the methods listed below are part of the public
// surface — anything not exposed here isn't reachable as `redis.x`.
const instance = new RedisClient();

export const redis = {
  client: instance.client,
  cacheGet: instance.cacheGet.bind(instance),
  cacheSet: instance.cacheSet.bind(instance),
  cacheDel: instance.cacheDel.bind(instance),
};
