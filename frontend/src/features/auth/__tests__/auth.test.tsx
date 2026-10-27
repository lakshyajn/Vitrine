import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "../AuthProvider";
import { RequireAuth, RedirectIfAuthenticated } from "../AuthGuards";
import { apiRequest, setUnauthorizedHandler } from "@/api/client";

// Mock Supabase module
vi.mock("@/lib/supabase", () => {
  const mockAuth = {
    getSession: vi.fn(),
    onAuthStateChange: vi.fn(() => ({
      data: { subscription: { unsubscribe: vi.fn() } },
    })),
    signInWithPassword: vi.fn(),
    signUp: vi.fn(),
    signOut: vi.fn(),
    refreshSession: vi.fn(),
    resetPasswordForEmail: vi.fn(),
  };
  return {
    isSupabaseConfigured: true,
    supabase: {
      auth: mockAuth,
    },
  };
});

import { supabase } from "@/lib/supabase";

function TestConsumer() {
  const { user, session, signOut, isLoading, isMockMode } = useAuth();
  return (
    <div>
      <div data-testid="auth-loading">{String(isLoading)}</div>
      <div data-testid="auth-user">{user?.email || "anonymous"}</div>
      <div data-testid="auth-token">{session?.access_token || "no-token"}</div>
      <div data-testid="auth-mock">{String(isMockMode)}</div>
      <button onClick={() => signOut()}>Sign Out</button>
    </div>
  );
}

describe("Frontend Auth Core (Milestone B)", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
  });

  it("mock mode yields the demo user without calling Supabase", async () => {
    // VITE_USE_MOCK is "true" by default in vitest config
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AuthProvider queryClient={queryClient}>
            <TestConsumer />
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByTestId("auth-mock")).toHaveTextContent("true");
    expect(screen.getByTestId("auth-user")).toHaveTextContent("studio@ateliersolenne.com");
    expect(screen.getByTestId("auth-token")).toHaveTextContent("mock-demo-access-token");
    // Ensure supabase was not called in mock mode
    expect(supabase?.auth.getSession).not.toHaveBeenCalled();
  });

  it("guard redirects to /login?next=... when signed out", async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/app/leads?tier=qualified"]}>
          <AuthProvider queryClient={queryClient} initialUser={null}>
            <Routes>
              <Route path="/login" element={<div data-testid="login-page">Login Page</div>} />
              <Route
                path="/app/*"
                element={
                  <RequireAuth>
                    <div data-testid="protected-content">Protected Content</div>
                  </RequireAuth>
                }
              />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
      expect(screen.queryByTestId("protected-content")).toBeNull();
    });
  });

  it("RedirectIfAuthenticated redirects signed-in user and rejects open-redirects", async () => {
    // Test with malicious next target: https://attacker.com
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/login?next=https%3A%2F%2Fattacker.com"]}>
          <AuthProvider queryClient={queryClient}>
            <Routes>
              <Route
                path="/login"
                element={
                  <RedirectIfAuthenticated>
                    <div data-testid="login-view">Login View</div>
                  </RedirectIfAuthenticated>
                }
              />
              <Route path="/app" element={<div data-testid="workspace-view">Workspace Home</div>} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    // Because mock user is signed in, RedirectIfAuthenticated redirects to /app (NOT to attacker.com)
    await waitFor(() => {
      expect(screen.getByTestId("workspace-view")).toBeInTheDocument();
      expect(screen.queryByTestId("login-view")).toBeNull();
    });
  });

  it("RedirectIfAuthenticated honors safe same-origin /app targets", async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/login?next=%2Fapp%2Fproducts%2Fnew"]}>
          <AuthProvider queryClient={queryClient}>
            <Routes>
              <Route
                path="/login"
                element={
                  <RedirectIfAuthenticated>
                    <div data-testid="login-view">Login View</div>
                  </RedirectIfAuthenticated>
                }
              />
              <Route path="/app/products/new" element={<div data-testid="new-product-view">New Product</div>} />
              <Route path="/app" element={<div data-testid="workspace-view">Workspace Home</div>} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("new-product-view")).toBeInTheDocument();
    });
  });

  it("sign-out clears the TanStack query cache", async () => {
    const user = userEvent.setup();
    const clearSpy = vi.spyOn(queryClient, "clear");

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AuthProvider queryClient={queryClient}>
            <TestConsumer />
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    const signOutBtn = screen.getByRole("button", { name: /sign out/i });
    await user.click(signOutBtn);

    expect(clearSpy).toHaveBeenCalled();
  });

  it("401 triggers one refresh then retries request successfully", async () => {
    let callCount = 0;
    const originalFetch = globalThis.fetch;

    globalThis.fetch = vi.fn().mockImplementation(async () => {
      callCount++;
      if (callCount === 1) {
        return new Response(JSON.stringify({ error: { code: "unauthorized", message: "Token expired" } }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify({ status: "success", retried: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });

    const refreshHandler = vi.fn().mockResolvedValue("new-refreshed-token-123");
    setUnauthorizedHandler(refreshHandler);

    const result = await apiRequest<{ status: string; retried: boolean }>("/test-refresh-retry");

    expect(refreshHandler).toHaveBeenCalledTimes(1);
    expect(callCount).toBe(2);
    expect(result.retried).toBe(true);

    globalThis.fetch = originalFetch;
  });

  it("failed 401 refresh does not retry and throws 401 ApiError", async () => {
    const originalFetch = globalThis.fetch;
    let callCount = 0;

    globalThis.fetch = vi.fn().mockImplementation(async () => {
      callCount++;
      return new Response(JSON.stringify({ error: { code: "unauthorized", message: "Expired" } }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });
    });

    const refreshHandler = vi.fn().mockResolvedValue(null); // refresh fails
    setUnauthorizedHandler(refreshHandler);

    await expect(apiRequest("/test-failed-refresh")).rejects.toThrow("Expired");
    expect(refreshHandler).toHaveBeenCalledTimes(1);
    expect(callCount).toBe(1); // not retried

    globalThis.fetch = originalFetch;
  });
});
