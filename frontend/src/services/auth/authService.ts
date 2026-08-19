import { mockRequest } from "../api/client";
import { users } from "../mock/data";
import { ROLE_LABELS, type Role } from "@/lib/types";

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: Role;
  organization: string;
}

export interface LoginPayload {
  email: string;
  password: string;
  role: Role;
  remember?: boolean;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
  role: Extract<Role, "DONOR" | "HOSPITAL_STAFF">;
}

/**
 * MOCK AUTH. Replace with POST /api/auth/login (JWT access+refresh) later.
 * The returned shape already matches what the JWT `user` claim will hold.
 */
export const authService = {
  login: ({ email, role }: LoginPayload) => {
    const match = users.find((u) => u.email === email && u.role === role);
    const user: AuthUser = match
      ? { id: match.id, name: match.name, email: match.email, role: match.role, organization: match.organization }
      : {
          id: `DEMO-${role}`,
          name: email.split("@")[0] || ROLE_LABELS[role],
          email,
          role,
          organization: role === "DONOR" ? "Individual Donor" : "Demo Organization",
        };
    return mockRequest({ user, accessToken: "mock.jwt.token", refreshToken: "mock.refresh.token" });
  },
  register: (payload: RegisterPayload) =>
    mockRequest({
      user: {
        id: `NEW-${Date.now()}`,
        name: payload.name,
        email: payload.email,
        role: payload.role,
        organization: payload.role === "DONOR" ? "Individual Donor" : "Pending verification",
      } satisfies AuthUser,
    }),
  requestPasswordReset: (email: string) => mockRequest({ ok: true, email }),
  resetPassword: (token: string) => mockRequest({ ok: true, token }),
};