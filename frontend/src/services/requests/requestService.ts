import { mockRequest } from "../api/client";
import { bloodRequests } from "../mock/data";
import type { BloodRequest } from "@/lib/types";

export const requestService = {
  list: () => mockRequest(bloodRequests),
  get: (id: string) => mockRequest(bloodRequests.find((r) => r.id === id) ?? null),
  create: (payload: Partial<BloodRequest>) =>
    mockRequest({ id: `REQ-${Math.floor(5000 + Math.random() * 999)}`, ...payload }),
  updateStatus: (id: string, status: BloodRequest["status"]) => mockRequest({ id, status }),
};