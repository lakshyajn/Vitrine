import { createContext, useContext } from "react";
import type { Session, User } from "@supabase/supabase-js";

export interface SignUpOptions {
  email: string;
  password: string;
  studioName?: string;
}

export interface AuthContextType {
  session: Session | null;
  user: User | null;
  isLoading: boolean;
  isMockMode: boolean;
  signIn: (email: string, password: string) => Promise<{ error: Error | null; session: Session | null }>;
  signUp: (options: SignUpOptions) => Promise<{ error: Error | null; session: Session | null }>;
  signOut: () => Promise<{ error: Error | null }>;
  resetPassword: (email: string) => Promise<{ error: Error | null }>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
