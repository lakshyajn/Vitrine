/* eslint-disable react-refresh/only-export-components */
import React, { useEffect, useRef, useState } from "react";
import type { Session, User } from "@supabase/supabase-js";
import type { QueryClient } from "@tanstack/react-query";
import { isSupabaseConfigured, supabase } from "@/lib/supabase";
import { setAccessTokenProvider, setUnauthorizedHandler } from "@/api/client";
import { AuthContext, type SignUpOptions } from "./AuthContext";

export { useAuth, type SignUpOptions, type AuthContextType } from "./AuthContext";

const DEMO_USER: User = {
  id: "00000000-0000-0000-0000-000000000001",
  app_metadata: { provider: "mock_demo" },
  user_metadata: { studio_name: "Atelier Solenne", is_demo: true },
  aud: "authenticated",
  created_at: new Date().toISOString(),
  email: "studio@ateliersolenne.com",
  role: "authenticated",
} as unknown as User;

const DEMO_SESSION: Session = {
  access_token: "mock-demo-access-token",
  token_type: "bearer",
  expires_in: 86400,
  refresh_token: "mock-demo-refresh-token",
  user: DEMO_USER,
} as unknown as Session;

function SupabaseConfigError() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas px-4 py-12 text-ink">
      <div className="w-full max-w-md rounded-2xl border border-red-200 bg-surface p-8 shadow-card text-center space-y-4">
        <span className="inline-flex items-center rounded-md bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-700 border border-red-200">
          Configuration Required
        </span>
        <h1 className="font-display text-xl font-bold text-ink">
          Supabase Credentials Missing
        </h1>
        <p className="text-xs text-muted leading-relaxed">
          <code className="rounded bg-surface-subtle px-1.5 py-0.5 font-mono text-[11px] text-ink">
            VITE_SUPABASE_URL
          </code>{" "}
          and{" "}
          <code className="rounded bg-surface-subtle px-1.5 py-0.5 font-mono text-[11px] text-ink">
            VITE_SUPABASE_ANON_KEY
          </code>{" "}
          are not configured in the frontend environment.
        </p>
        <p className="text-xs text-muted leading-relaxed">
          For offline or evaluation use without Supabase, start the frontend with{" "}
          <code className="rounded bg-surface-subtle px-1.5 py-0.5 font-mono text-[11px] text-ink">
            VITE_USE_MOCK=true
          </code>
          .
        </p>
      </div>
    </div>
  );
}

export function AuthProvider({
  children,
  queryClient,
  initialUser,
}: {
  children: React.ReactNode;
  queryClient?: QueryClient;
  initialUser?: User | null;
}) {
  const isMockMode = import.meta.env.VITE_USE_MOCK === "true";
  const defaultUser = initialUser !== undefined ? initialUser : (isMockMode ? DEMO_USER : null);
  const defaultSession = defaultUser ? (isMockMode ? DEMO_SESSION : null) : null;
  const [session, setSession] = useState<Session | null>(defaultSession);
  const [user, setUser] = useState<User | null>(defaultUser);
  const [isLoading, setIsLoading] = useState<boolean>(!isMockMode && initialUser === undefined);
  const currentUserIdRef = useRef<string | null>(defaultUser?.id ?? null);

  useEffect(() => {
    // 1. Wire Access Token Provider for apiRequest
    setAccessTokenProvider(async () => {
      if (isMockMode) return DEMO_SESSION.access_token;
      if (!supabase) return null;
      const { data } = await supabase.auth.getSession().catch(() => ({ data: { session: null } }));
      return data.session?.access_token ?? null;
    });

    // 2. Wire 401 Unauthorized Handler (attempts refresh once then signs out)
    setUnauthorizedHandler(async () => {
      if (isMockMode || !supabase) return null;
      try {
        const { data, error } = await supabase.auth.refreshSession();
        if (error || !data.session) {
          throw error || new Error("Session refresh failed");
        }
        setSession(data.session);
        setUser(data.session.user);
        return data.session.access_token;
      } catch {
        // Refresh failed: clear cache, sign out, and redirect to /login
        await supabase.auth.signOut().catch(() => {});
        queryClient?.clear();
        setSession(null);
        setUser(null);
        const currentPath = window.location.pathname + window.location.search;
        const next = encodeURIComponent(currentPath);
        window.location.href = `/login?next=${next}`;
        return null;
      }
    });

    if (isMockMode) {
      setIsLoading(false);
      return;
    }

    if (!supabase) {
      setIsLoading(false);
      return;
    }

    // Initialize real Supabase session
    supabase.auth.getSession().then(({ data: { session: initialSession } }) => {
      setSession(initialSession);
      setUser(initialSession?.user ?? null);
      currentUserIdRef.current = initialSession?.user?.id ?? null;
      setIsLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, currentSession) => {
      const prevId = currentUserIdRef.current;
      const nextId = currentSession?.user?.id ?? null;
      currentUserIdRef.current = nextId;

      setSession(currentSession);
      setUser(currentSession?.user ?? null);
      setIsLoading(false);

      if (prevId && prevId !== nextId) {
        queryClient?.clear();
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [isMockMode, queryClient]);

  const signIn = async (email: string, password: string) => {
    if (isMockMode) {
      setSession(DEMO_SESSION);
      setUser(DEMO_USER);
      return { error: null, session: DEMO_SESSION };
    }
    if (!supabase) {
      return { error: new Error("Supabase is not configured"), session: null };
    }
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (data.session) {
      setSession(data.session);
      setUser(data.session.user);
    }
    return { error, session: data.session };
  };

  const signUp = async ({ email, password, studioName }: SignUpOptions) => {
    if (isMockMode) {
      const mockUser = {
        ...DEMO_USER,
        email,
        user_metadata: { studio_name: studioName || "Demo Studio", is_demo: true },
      } as User;
      const mockSession = { ...DEMO_SESSION, user: mockUser };
      setSession(mockSession);
      setUser(mockUser);
      return { error: null, session: mockSession };
    }
    if (!supabase) {
      return { error: new Error("Supabase is not configured"), session: null };
    }
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: studioName ? { studio_name: studioName } : {},
      },
    });
    if (data.session) {
      setSession(data.session);
      setUser(data.session.user);
    }
    return { error, session: data.session };
  };

  const signOut = async () => {
    queryClient?.clear();
    if (isMockMode || !supabase) {
      setSession(null);
      setUser(null);
      return { error: null };
    }
    const { error } = await supabase.auth.signOut();
    setSession(null);
    setUser(null);
    return { error };
  };

  const resetPassword = async (email: string) => {
    if (isMockMode) {
      return { error: null };
    }
    if (!supabase) {
      return { error: new Error("Supabase is not configured") };
    }
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    });
    return { error };
  };

  const resendConfirmation = async (email: string) => {
    if (isMockMode) {
      return { error: null };
    }
    if (!supabase) {
      return { error: new Error("Supabase is not configured") };
    }
    const { error } = await supabase.auth.resend({
      type: "signup",
      email,
    });
    return { error };
  };

  if (!isMockMode && !isSupabaseConfigured) {
    return <SupabaseConfigError />;
  }

  return (
    <AuthContext.Provider
      value={{
        session,
        user,
        isLoading,
        isMockMode,
        signIn,
        signUp,
        signOut,
        resetPassword,
        resendConfirmation,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
