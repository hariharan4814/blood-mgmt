import { mockRequest } from "../api/client";
import { camps } from "../mock/data";
import type { Camp } from "@/lib/types";

export const campService = {
  list: () => mockRequest(camps),
  get: (id: string) => mockRequest(camps.find((c) => c.id === id) ?? null),
  register: (campId: string) => mockRequest({ campId, registered: true }),
  save: (payload: Partial<Camp>) => mockRequest({ id: payload.id ?? `CMP-${Date.now()}`, ...payload }),
};