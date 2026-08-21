import { request } from "../api/client";
import type { Notification } from "@/lib/types";

export interface BackendNotification {
  id: number;
  recipient: number;
  title: string;
  message: string;
  notification_type:
    | "EMERGENCY_SOS"
    | "BLOOD_REQUEST"
    | "INVENTORY_ALERT"
    | "CAMP_UPDATE"
    | "SYSTEM";
  notification_type_display: string;
  is_read: boolean;
  created_at: string;
  updated_at: string;
}

function mapNotificationCategory(
  backendType: BackendNotification["notification_type"],
): Notification["category"] {
  switch (backendType) {
    case "EMERGENCY_SOS":
      return "EMERGENCY";
    case "BLOOD_REQUEST":
      return "REQUEST";
    case "INVENTORY_ALERT":
      return "INVENTORY";
    case "CAMP_UPDATE":
      return "CAMP";
    default:
      return "SYSTEM";
  }
}

function mapNotification(n: BackendNotification): Notification {
  return {
    id: String(n.id),
    title: n.title,
    body: n.message,
    category: mapNotificationCategory(n.notification_type),
    read: Boolean(n.is_read),
    createdAt: n.created_at,
  };
}

export const notificationService = {
  /**
   * List all in-app notifications for authenticated user.
   */
  list: async (params?: { is_read?: boolean; notification_type?: string }): Promise<Notification[]> => {
    const query = new URLSearchParams();
    if (params?.is_read !== undefined) query.set("is_read", String(params.is_read));
    if (params?.notification_type) query.set("notification_type", params.notification_type);

    const queryString = query.toString() ? `?${query.toString()}` : "";
    const response = await request<
      { results?: BackendNotification[] } | BackendNotification[]
    >(`/api/notifications/${queryString}`);

    const rawList = Array.isArray(response) ? response : response.results || [];
    return rawList.map(mapNotification);
  },

  /**
   * Get unread notifications count for badge display.
   */
  getUnreadCount: async (): Promise<number> => {
    try {
      const res = await request<{ unread_count: number }>("/api/notifications/unread-count/");
      return res.unread_count || 0;
    } catch {
      return 0;
    }
  },

  /**
   * Mark a single notification as read.
   */
  markRead: async (id: string | number): Promise<Notification> => {
    const res = await request<BackendNotification>(`/api/notifications/${id}/mark-read/`, {
      method: "POST",
    });
    return mapNotification(res);
  },

  /**
   * Mark all unread notifications for authenticated user as read.
   */
  markAllRead: async (): Promise<{ detail: string; marked_count?: number }> => {
    return request<{ detail: string; marked_count?: number }>("/api/notifications/mark-all-read/", {
      method: "POST",
    });
  },
};