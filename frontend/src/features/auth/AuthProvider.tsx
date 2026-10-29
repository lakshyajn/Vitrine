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
  isMockMode: isMockModeProp,
}: {
  children: React.ReactNode;
  queryClient?: QueryClient;
  initialUser?: User | null;
  isMockMode?: boolean;
}) {
  const isMockMode = isMockModeProp ?? (import.meta.env.VITE_USE_MOCK === "true");
  const defaultUser = initialUser !== undefined ? initialUser : (isMockMode ? DEMO_USER : null);
  const defaultSession = defaultUser ? (isMockMode ? DEMO_SESSION : null) : null;
  const [session, setSession] = useState<Session | null>(defaultSession);
  const [user, setUser] = useState<User | null>(defaultUser);
  const [isLoading, setIsLoading] = useState<boolean>(!isMockMode && initialUser === undefined);
  const currentUserIdRef = useRef<string | null>(defaultUser?.id ?? null);
  const currentSessionRef = useRef<Session | null>(defaultSession);
  const isRedirectingRef = useRef<boolean>(false);

  useEffect(() => {
    // 1. Wire Access Token Provider for apiRequest (prevents getSession race condition)
    setAccessTokenProvider(async () => {
      if (isMockMode) return DEMO_SESSION.access_token;
      if (currentSessionRef.current?.access_token) {
        return currentSessionRef.current.access_token;
      }
      if (!supabase) return null;
      const { data } = await supabase.auth.getSession().catch(() => ({ data: { session: null } }));
      if (data.session?.access_token) {
        currentSessionRef.current = data.session;
        return data.session.access_token;
      }
      return null;
    });

    const triggerSessionInvalidRedirect = async () => {
      if (isRedirectingRef.current) return;
      isRedirectingRef.current = true;
      try {
        if (supabase) {
          await supabase.auth.signOut().catch(() => {});
        }
      } finally {
        currentSessionRef.current = null;
        setSession(null);
        setUser(null);
        queryClient?.clear();
        const notice = "Your session could not be verified. Please sign in again.";
        try {
          sessionStorage.setItem("auth_notice", notice);
        } catch {
          // Ignore storage issues in test/restricted environments
        }
        const currentPath = window.location.pathname + window.location.search;
        const next = encodeURIComponent(currentPath.startsWith("/login") ? "/app" : currentPath);
        const loginUrl = `/login?next=${next}&message=${encodeURIComponent(notice)}`;
        window.location.href = loginUrl;
      }
    };

    // 2. Wire 401 Unauthorized Handler (attempts refresh once then signs out and redirects)
    let refreshPromise: Promise<string | null> | null = null;

    setUnauthorizedHandler(async ({ isRetry }: { isRetry: boolean }) => {
      if (isMockMode || !supabase) return null;

      if (isRetry) {
        // Request failed 401 even after token refresh: reject and redirect to login
        await triggerSessionInvalidRedirect();
        return null;
      }

      // Initial 401: attempt single refreshSession()
      if (!refreshPromise) {
        refreshPromise = (async () => {
          try {
            const { data, error } = await supabase.auth.refreshSession();
            if (error || !data.session) {
              throw error || new Error("Session refresh failed");
            }
            currentSessionRef.current = data.session;
            setSession(data.session);
            setUser(data.session.user);
            return data.session.access_token;
          } catch {
            await triggerSessionInvalidRedirect();
            return null;
          } finally {
            refreshPromise = null;
          }
        })();
      }

      return refreshPromise;
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
    const sessionPromise = supabase.auth.getSession();
    if (sessionPromise && typeof sessionPromise.then === 'function') {
      sessionPromise.then(({ data: { session: initialSession } }) => {
        currentSessionRef.current = initialSession;
        setSession(initialSession);
        setUser(initialSession?.user ?? null);
        currentUserIdRef.current = initialSession?.user?.id ?? null;
        setIsLoading(false);
      }).catch(() => {
        setIsLoading(false);
      });
    } else {
      setIsLoading(false);
    }

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, currentSession) => {
      const prevId = currentUserIdRef.current;
      const nextId = currentSession?.user?.id ?? null;
      currentUserIdRef.current = nextId;
      currentSessionRef.current = currentSession;

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
      currentSessionRef.current = DEMO_SESSION;
      setSession(DEMO_SESSION);
      setUser(DEMO_USER);
      return { error: null, session: DEMO_SESSION };
    }
    if (!supabase) {
      return { error: new Error("Supabase is not configured"), session: null };
    }
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (data.session) {
      currentSessionRef.current = data.session;
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
      currentSessionRef.current = mockSession;
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
      currentSessionRef.current = data.session;
      setSession(data.session);
      setUser(data.session.user);
    }
    return { error, session: data.session };
  };

  const signOut = async () => {
    queryClient?.clear();
    currentSessionRef.current = null;
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
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
