import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { clearTokens, hasTokens } from "@/lib/tokens";
import type { Role } from "@/lib/types";
import {
  authService,
  type AuthUser,
  type LoginPayload,
  type RegisterPayload,
} from "@/services/auth/authService";

interface AuthContextValue {
  user: AuthUser | null;
  role: Role | null;
  isAuthenticated: boolean;
  hydrated: boolean;
  loading: boolean;
  login: (payload: LoginPayload) => Promise<AuthUser>;
  register: (payload: RegisterPayload) => Promise<AuthUser>;
  logout: () => void;
  refreshUser: () => Promise<AuthUser | null>;
  setUser: (user: AuthUser | null) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<AuthUser | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [loading, setLoading] = useState(false);

  // Initialize auth state by restoring session from Django backend if tokens exist
  useEffect(() => {
    let mounted = true;

    async function initAuth() {
      if (hasTokens()) {
        try {
          const currentUser = await authService.getCurrentUser();
          if (mounted) {
            setUserState(currentUser);
          }
        } catch {
          if (mounted) {
            clearTokens();
            setUserState(null);
          }
        }
      }
      if (mounted) {
        setHydrated(true);
      }
    }

    initAuth();

    return () => {
      mounted = false;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      role: user?.role ?? null,
      isAuthenticated: Boolean(user),
      hydrated,
      loading,
      login: async (payload) => {
        setLoading(true);
        try {
          const { user: loggedInUser } = await authService.login(payload);
          setUserState(loggedInUser);
          return loggedInUser;
        } finally {
          setLoading(false);
        }
      },
      register: async (payload) => {
        setLoading(true);
        try {
          const { user: registeredUser } = await authService.register(payload);
          return registeredUser;
        } finally {
          setLoading(false);
        }
      },
      logout: () => {
        authService.logout();
        setUserState(null);
      },
      refreshUser: async () => {
        try {
          const updatedUser = await authService.getCurrentUser();
          setUserState(updatedUser);
          return updatedUser;
        } catch {
          return null;
        }
      },
      setUser: (nextUser) => {
        setUserState(nextUser);
      },
    }),
    [user, hydrated, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}