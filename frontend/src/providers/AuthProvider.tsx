import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { authService, type AuthUser, type LoginPayload } from "@/services/auth/authService";

/**
 * MOCK SESSION STORE.
 * Later: keep the JWT access token here (memory) + refresh token in an
 * httpOnly cookie, and hydrate `user` from GET /api/auth/me.
 */
const STORAGE_KEY = "bms.session";

interface AuthContextValue {
  user: AuthUser | null;
  hydrated: boolean;
  loading: boolean;
  login: (payload: LoginPayload) => Promise<AuthUser>;
  logout: () => void;
  setUser: (user: AuthUser) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<AuthUser | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (raw) setUserState(JSON.parse(raw) as AuthUser);
    } catch {
      window.localStorage.removeItem(STORAGE_KEY);
    }
    setHydrated(true);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      hydrated,
      loading,
      login: async (payload) => {
        setLoading(true);
        try {
          const { user: next } = await authService.login(payload);
          window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
          setUserState(next);
          return next;
        } finally {
          setLoading(false);
        }
      },
      logout: () => {
        window.localStorage.removeItem(STORAGE_KEY);
        setUserState(null);
      },
      setUser: (next) => {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        setUserState(next);
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