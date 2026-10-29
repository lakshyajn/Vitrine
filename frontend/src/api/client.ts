const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");
type ErrorBody = { error?: { code?: string; message?: string; details?: unknown; request_id?: string } };

type AccessTokenProvider = () => Promise<string | null>;
type UnauthorizedHandler = (options: { isRetry: boolean }) => Promise<string | null>;

let accessTokenProvider: AccessTokenProvider | undefined;
let unauthorizedHandler: UnauthorizedHandler | undefined;

export function setAccessTokenProvider(provider: AccessTokenProvider | undefined) {
  accessTokenProvider = provider;
}

export function setUnauthorizedHandler(handler: UnauthorizedHandler | undefined) {
  unauthorizedHandler = handler;
}

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly requestId?: string;
  readonly details?: unknown;
  constructor(args: { message: string; code: string; status: number; requestId?: string; details?: unknown }) {
    super(args.message);
    this.name = "ApiError";
    this.code = args.code;
    this.status = args.status;
    this.requestId = args.requestId;
    this.details = args.details;
  }
  get isRetryable() {
    return ["upstream_timeout", "upstream_unavailable", "rate_limited"].includes(this.code);
  }
}

export async function apiRequest<T>(path: string, init: RequestInit = {}, isRetry: boolean = false): Promise<T> {
  const headers = new Headers(init.headers);
  let token = await accessTokenProvider?.();

  // Explicit dev bypass only when VITE_DEV_AUTH_BYPASS === "true"
  if (!token && import.meta.env.VITE_DEV_AUTH_BYPASS === "true") {
    token = "dev-token";
  }

  if (token) headers.set("Authorization", "Bearer " + token);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(API_BASE_URL + (path.startsWith("/") ? path : "/" + path), { ...init, headers });
  } catch {
    throw new ApiError({
      message: "Could not reach the application server. Check your connection and try again.",
      code: "network_error",
      status: 0,
    });
  }

  // Handle 401 unauthorized: attempt single token refresh and retry
  if (response.status === 401 && unauthorizedHandler) {
    if (!isRetry) {
      const refreshedToken = await unauthorizedHandler({ isRetry: false }).catch(() => null);
      if (refreshedToken) {
        const retryHeaders = new Headers(init.headers);
        retryHeaders.set("Authorization", "Bearer " + refreshedToken);
        return apiRequest<T>(path, { ...init, headers: retryHeaders }, true);
      }
    } else {
      // Retry request was still 401: trigger sign out and redirect once
      await unauthorizedHandler({ isRetry: true }).catch(() => null);
    }
  }

  if (response.status === 204) return undefined as T;
  const body: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    const error = (body && typeof body === "object" ? body : {}) as ErrorBody;
    throw new ApiError({
      message: error.error?.message || "Request failed (" + response.status + ").",
      code: error.error?.code || (response.status === 401 ? "unauthorized" : "unknown_error"),
      status: response.status,
      requestId: error.error?.request_id,
      details: error.error?.details,
    });
  }

  return body as T;
}
