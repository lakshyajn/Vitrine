const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");
type ErrorBody = { error?: { code?: string; message?: string; details?: unknown; request_id?: string } };
type AccessTokenProvider = () => Promise<string | null>;
let accessTokenProvider: AccessTokenProvider | undefined;
export function setAccessTokenProvider(provider: AccessTokenProvider | undefined) { accessTokenProvider = provider; }

// Vitrine dev/test JWT for local testing against APP_ENV=dev backend (owner_id: 00000000-0000-0000-0000-000000000001)
const DEV_DEFAULT_TOKEN =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ2aXRyaW5lLWRldiIsInN1YiI6IjAwMDAwMDAwLTAwMDAtMDAwMC0wMDAwLTAwMDAwMDAwMDAwMSIsImVtYWlsIjoiYXJ0aXNhbkBzYW1wbGVzZWxsZXIudGVzdCIsInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImV4cCI6NDEwMjQ0NDgwMH0.cgbjgLbCuFgPEq55-qbzpCx02__jln1Olibvby614-g";

export class ApiError extends Error {
  readonly code: string; readonly status: number; readonly requestId?: string; readonly details?: unknown;
  constructor(args: { message: string; code: string; status: number; requestId?: string; details?: unknown }) {
    super(args.message); this.name = "ApiError"; this.code = args.code; this.status = args.status; this.requestId = args.requestId; this.details = args.details;
  }
  get isRetryable() { return ["upstream_timeout", "upstream_unavailable", "rate_limited"].includes(this.code); }
}
export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  let token = await accessTokenProvider?.();
  if (!token && (import.meta.env.DEV || import.meta.env.VITE_USE_MOCK !== "true")) {
    token = DEV_DEFAULT_TOKEN;
  }
  if (token) headers.set("Authorization", "Bearer " + token);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  let response: Response;
  try { response = await fetch(API_BASE_URL + (path.startsWith("/") ? path : "/" + path), { ...init, headers }); }
  catch { throw new ApiError({ message: "Could not reach the application server. Check your connection and try again.", code: "network_error", status: 0 }); }
  if (response.status === 204) return undefined as T;
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const error = (body && typeof body === "object" ? body : {}) as ErrorBody;
    throw new ApiError({ message: error.error?.message || "Request failed (" + response.status + ").", code: error.error?.code || "unknown_error", status: response.status, requestId: error.error?.request_id, details: error.error?.details });
  }
  return body as T;
}
