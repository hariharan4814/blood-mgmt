import { mockRequest } from "../api/client";
import { notifications } from "../mock/data";

export const notificationService = {
  list: () => mockRequest(notifications),
  markRead: (id: string) => mockRequest({ id, read: true }),
  markAllRead: () => mockRequest({ ok: true }),
};