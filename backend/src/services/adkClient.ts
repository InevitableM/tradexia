import axios, { AxiosInstance } from "axios";

const ADK_BASE_URL = process.env.ADK_BASE_URL || "http://localhost:8000";

let instance: AxiosInstance | null = null;

function getAdkClient(): AxiosInstance {
  if (!instance) {
    instance = axios.create({
      baseURL: ADK_BASE_URL,
      timeout: 120_000,
      headers: {
        "Content-Type": "application/json",
        ...(process.env.ADK_API_KEY && {
          Authorization: `Bearer ${process.env.ADK_API_KEY}`,
        }),
      },
    });

    instance.interceptors.response.use(
      (res) => res,
      (err) => {
        console.error("[adk] request failed:", err.message);
        return Promise.reject(err);
      }
    );
  }
  return instance;
}

export interface AnalysisRequest {
  query: string;
  session_id: string;
  user_id: string;
  access_token: string;
}

export interface AnalysisResponse {
  response: string;
  state?: Record<string, unknown>;
  mode?: string;
  agents_executed?: string[];
}

export async function runAnalysis(payload: AnalysisRequest): Promise<AnalysisResponse> {
  const { data } = await getAdkClient().post<AnalysisResponse>("/run", payload);
  return data;
}

/** Returns the raw Node.js IncomingMessage stream from ADK's /stream endpoint. */
export async function streamAnalysis(payload: AnalysisRequest): Promise<NodeJS.ReadableStream> {
  const res = await fetch(`${ADK_BASE_URL}/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`ADK /stream error ${res.status}: ${text}`);
  }
  // Node 18+ fetch returns a Web ReadableStream on res.body
  const { Readable } = await import("stream");
  return Readable.fromWeb(res.body as import("stream/web").ReadableStream);
}

export async function healthCheck(): Promise<boolean> {
  try {
    await getAdkClient().get("/health");
    return true;
  } catch {
    return false;
  }
}
