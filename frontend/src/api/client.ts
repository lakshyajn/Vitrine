let activeBaseUrl = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8080/api/v1").replace(/\/$/, "");

function getAlternativeUrl(url: string): string | null {
  if (url.includes(":8000")) return url.replace(":8000", ":8080");
  if (url.includes(":8080")) return url.replace(":8080", ":8000");
  return null;
}
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
  const targetPath = path.startsWith("/") ? path : "/" + path;
  try {
    response = await fetch(activeBaseUrl + targetPath, { ...init, headers });
  } catch {
    // If connection failed, check alternative dev port (8000 <-> 8080)
    const altBase = getAlternativeUrl(activeBaseUrl);
    if (altBase) {
      try {
        response = await fetch(altBase + targetPath, { ...init, headers });
        activeBaseUrl = altBase; // Switch active base URL for subsequent calls
      } catch {
        throw new ApiError({
          message: "Could not reach the application server. Check your connection and try again.",
          code: "network_error",
          status: 0,
        });
      }
    } else {
      throw new ApiError({
        message: "Could not reach the application server. Check your connection and try again.",
        code: "network_error",
        status: 0,
      });
    }
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
