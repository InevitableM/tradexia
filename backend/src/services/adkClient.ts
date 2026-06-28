import axios, { AxiosInstance } from "axios";

let instance: AxiosInstance | null = null;

function getAdkClient(): AxiosInstance {
  if (!instance) {
    instance = axios.create({
      baseURL: process.env.ADK_BASE_URL || "http://localhost:8000",
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
  symbol?: string;
  sessionId?: string;
  userId?: string;
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

export async function healthCheck(): Promise<boolean> {
  try {
    await getAdkClient().get("/health");
    return true;
  } catch {
    return false;
  }
}
