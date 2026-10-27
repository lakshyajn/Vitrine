import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { User } from "@supabase/supabase-js";
import { AuthProvider } from "../AuthProvider";
import { LoginPage } from "../LoginPage";
import { SignupPage } from "../SignupPage";
import { ResetPasswordPage } from "../ResetPasswordPage";
import { OnboardingModal } from "../OnboardingModal";
import { Sidebar } from "@/components/layout/Sidebar";
import { LandingNav } from "@/features/landing/LandingNav";
import { ProductListPage } from "@/features/products/ProductListPage";

// Mock demo API
const mockSeedMutateAsync = vi.fn().mockResolvedValue({
  products_seeded: 4,
  leads_seeded: 3,
  runs_seeded: 1,
  drafts_seeded: 1,
});

vi.mock("@/api/demo", () => ({
  seedDemoWorkspace: vi.fn(),
  useSeedDemo: () => ({
    mutateAsync: mockSeedMutateAsync,
    isPending: false,
  }),
  PRODUCTS_QUERY_KEY: ["products"],
}));

// Mock products API
vi.mock("@/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api")>();
  return {
    ...actual,
    getProducts: vi.fn().mockResolvedValue([]),
    deleteProduct: vi.fn().mockResolvedValue({}),
  };
});

vi.mock("@/lib/supabase", () => {
  return {
    isSupabaseConfigured: true,
    supabase: {
      auth: {
        getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
        onAuthStateChange: vi.fn(() => ({
          data: { subscription: { unsubscribe: vi.fn() } },
        })),
        signInWithPassword: vi.fn(),
        signUp: vi.fn(),
        signOut: vi.fn().mockResolvedValue({ error: null }),
        refreshSession: vi.fn(),
        resetPasswordForEmail: vi.fn().mockResolvedValue({ error: null }),
        resend: vi.fn().mockResolvedValue({ error: null }),
        updateUser: vi.fn().mockResolvedValue({ data: { user: null }, error: null }),
      },
    },
  };
});

// Mock profile module
vi.mock("@/api/profile", () => {
  return {
    getProfile: vi.fn(),
    updateProfile: vi.fn().mockResolvedValue({
      id: "p-1",
      user_id: "u-1",
      business_name: "Test Atelier",
      country: "UK",
      website: "https://test.com",
      contact_email: "test@atelier.com",
      about: "Craft studio",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    }),
    useProfile: vi.fn(() => ({
      data: {
        id: "p-1",
        user_id: "u-1",
        business_name: "Atelier Solenne",
        country: "UK",
        website: "https://test.com",
        contact_email: "studio@ateliersolenne.com",
        about: "Textile studio",
      },
      isLoading: false,
    })),
    useUpdateProfile: vi.fn(() => ({
      mutateAsync: vi.fn().mockResolvedValue({}),
      isPending: false,
    })),
  };
});

import { useProfile } from "@/api/profile";

describe("Milestone C: Auth Pages, Onboarding, Layout & Landing", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useProfile).mockReturnValue({
      data: {
        id: "p-1",
        user_id: "u-1",
        business_name: "Atelier Solenne",
        country: "UK",
        website: "https://test.com",
        contact_email: "studio@ateliersolenne.com",
        about: "Textile studio",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      },
      isLoading: false,
    } as unknown as ReturnType<typeof useProfile>);
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
  });

  it("LoginPage enforces valid email, password >= 6, and enables submission", async () => {
    const user = userEvent.setup();

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AuthProvider queryClient={queryClient} initialUser={null}>
            <LoginPage />
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    const submitBtn = screen.getByRole("button", { name: /^sign in$/i });
    expect(submitBtn).toBeDisabled();

    const emailInput = screen.getByLabelText(/studio email address/i);
    const pwdInput = screen.getByLabelText(/password/i);

    await user.type(emailInput, "not-an-email");
    expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument();
    expect(submitBtn).toBeDisabled();

    await user.clear(emailInput);
    await user.type(emailInput, "maker@craft.com");

    await user.type(pwdInput, "123");
    expect(screen.getByText(/password must be at least 6 characters/i)).toBeInTheDocument();
    expect(submitBtn).toBeDisabled();

    await user.type(pwdInput, "456");
    expect(screen.queryByText(/password must be at least 6 characters/i)).toBeNull();
    expect(submitBtn).not.toBeDisabled();
  });

  it("SignupPage validates studio name 2-80 chars, email and password", async () => {
    const user = userEvent.setup();

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AuthProvider queryClient={queryClient} initialUser={null}>
            <SignupPage />
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    const submitBtn = screen.getByRole("button", { name: /create account/i });
    expect(submitBtn).toBeDisabled();

    const studioInput = screen.getByLabelText(/studio or brand name/i);
    const emailInput = screen.getByLabelText(/studio email address/i);
    const pwdInput = screen.getByLabelText(/password/i);

    await user.type(studioInput, "A");
    expect(screen.getByText(/studio name must be between 2 and 80 characters/i)).toBeInTheDocument();

    await user.type(studioInput, "telier Bloom");
    await user.type(emailInput, "bloom@studio.co");
    await user.type(pwdInput, "secret123");

    expect(submitBtn).not.toBeDisabled();
  });

  it("ResetPasswordPage toggles between request form and update password form", async () => {
    const user = userEvent.setup();

    // 1. Request form view
    const { unmount } = render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/reset-password"]}>
          <AuthProvider queryClient={queryClient} initialUser={null}>
            <ResetPasswordPage />
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByRole("heading", { name: /reset your password/i })).toBeInTheDocument();
    const sendBtn = screen.getByRole("button", { name: /send reset link/i });
    expect(sendBtn).toBeDisabled();

    const emailInput = screen.getByLabelText(/studio email address/i);
    await user.type(emailInput, "maker@studio.com");
    expect(sendBtn).not.toBeDisabled();

    await user.click(sendBtn);

    await waitFor(() => {
      expect(screen.getByText(/reset link dispatched/i)).toBeInTheDocument();
    });

    unmount();

    // 2. Recovery hash simulation view
    window.location.hash = "#type=recovery&access_token=test-recovery-token";

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/reset-password"]}>
          <AuthProvider queryClient={queryClient} initialUser={null}>
            <ResetPasswordPage />
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByRole("heading", { name: /set new password/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/^new password$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm new password/i)).toBeInTheDocument();

    window.location.hash = "";
  });

  it("OnboardingModal shows when profile business_name is empty", () => {
    vi.mocked(useProfile).mockReturnValue({
      data: {
        id: "p-empty",
        user_id: "u-empty",
        business_name: "",
        country: null,
        website: null,
        contact_email: "artisan@fresh.com",
        about: null,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      },
      isLoading: false,
    } as unknown as ReturnType<typeof useProfile>);

    const mockUser: User = {
      id: "u-empty",
      email: "artisan@fresh.com",
      user_metadata: { studio_name: "Fresh Craft Studio" },
    } as unknown as User;

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AuthProvider queryClient={queryClient} initialUser={mockUser}>
            <OnboardingModal />
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /set up your maker studio/i })).toBeInTheDocument();
    const studioInput = screen.getByLabelText(/studio or business name/i) as HTMLInputElement;
    expect(studioInput.value).toBe("Fresh Craft Studio");
  });

  it("Sidebar displays signed-in studio name, email, and sign out button", () => {
    const mockUser: User = {
      id: "u-123",
      email: "artisan@atelier.com",
      user_metadata: { studio_name: "Atelier Solenne", is_demo: true },
    } as unknown as User;

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AuthProvider queryClient={queryClient} initialUser={mockUser}>
            <Sidebar />
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByText("Atelier Solenne")).toBeInTheDocument();
    expect(screen.getByText("artisan@atelier.com")).toBeInTheDocument();
    expect(screen.getByText("Demo data")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign out/i })).toBeInTheDocument();
  });

  it("LandingNav displays 'Open workspace' when signed in and 'Sign in' when signed out", () => {
    // 1. Signed out
    const { unmount } = render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AuthProvider queryClient={queryClient} initialUser={null}>
            <LandingNav />
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByRole("link", { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /explore workspace/i })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /open workspace/i })).toBeNull();

    unmount();

    // 2. Signed in
    const mockUser: User = {
      id: "u-signed-in",
      email: "signedin@craft.com",
    } as unknown as User;

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AuthProvider queryClient={queryClient} initialUser={mockUser}>
            <LandingNav />
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByRole("link", { name: /open workspace/i })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /sign in/i })).toBeNull();
  });

  it("ProductListPage empty state renders 'Load demo catalogue' button and triggers demo seed", async () => {
    const user = userEvent.setup();

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AuthProvider queryClient={queryClient}>
            <ProductListPage />
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText(/no products in your catalog yet/i)).toBeInTheDocument();
    });

    const seedBtn = screen.getByRole("button", { name: /load demo catalogue/i });
    expect(seedBtn).toBeInTheDocument();

    await user.click(seedBtn);

    expect(mockSeedMutateAsync).toHaveBeenCalledTimes(1);
    await waitFor(() => {
      expect(screen.getByText(/demo catalogue loaded: 4 products, 3 leads/i)).toBeInTheDocument();
    });
  });
});
