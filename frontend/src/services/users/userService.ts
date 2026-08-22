import { request } from "../api/client";
import { mapBackendUser, type BackendUser } from "../analytics/analyticsService";
import type { Role, User } from "@/lib/types";

export interface CreateUserData {
  username: string;
  email: string;
  password: string;
  role: Role;
  phone?: string;
  first_name?: string;
  last_name?: string;
  is_active?: boolean;
}

export interface UpdateUserData {
  role?: Role;
  phone?: string;
  first_name?: string;
  last_name?: string;
  is_active?: boolean;
  email?: string;
  username?: string;
}

export const userService = {
  /**
   * List all system users (Super Admin).
   */
  listUsers: async (): Promise<User[]> => {
    try {
      const res = await request<{ results?: BackendUser[] } | BackendUser[]>("/api/users/");
      const list = Array.isArray(res) ? res : res.results || [];
      return list.map(mapBackendUser);
    } catch {
      const { users } = await import("../mock/data");
      return users.map(mapBackendUser);
    }
  },

  /**
   * Provision a new user account (Super Admin).
   */
  createUser: async (data: CreateUserData): Promise<User> => {
    const raw = await request<BackendUser>("/api/users/", {
      method: "POST",
      body: JSON.stringify(data),
    });
    return mapBackendUser(raw);
  },

  /**
   * Update safe user fields (Super Admin).
   */
  updateUser: async (id: number | string, data: UpdateUserData): Promise<User> => {
    const numericId = typeof id === "string" ? id.replace(/^USR-/, "") : id;
    const raw = await request<BackendUser>(`/api/users/${numericId}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
    return mapBackendUser(raw);
  },

  /**
   * Delete a user account (Super Admin).
   */
  deleteUser: async (id: number | string): Promise<void> => {
    const numericId = typeof id === "string" ? id.replace(/^USR-/, "") : id;
    await request<void>(`/api/users/${numericId}/`, {
      method: "DELETE",
    });
  },

  /**
   * Toggle account activation state (Super Admin).
   */
  toggleActive: async (id: number | string, currentStatus: "ACTIVE" | "SUSPENDED"): Promise<User> => {
    const is_active = currentStatus !== "ACTIVE";
    return await userService.updateUser(id, { is_active });
  },
};
