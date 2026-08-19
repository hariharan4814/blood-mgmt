import { mockRequest } from "../api/client";
import { sosBroadcasts, sosResponses } from "../mock/data";
import type { BloodGroup } from "@/lib/types";

export const sosService = {
  listBroadcasts: () => mockRequest(sosBroadcasts),
  listResponses: (broadcastId: string) => mockRequest(sosResponses.map((r) => ({ ...r, broadcastId }))),
  previewEligibleDonors: (group: BloodGroup, radiusKm: number) =>
    mockRequest({ group, radiusKm, eligibleDonors: Math.round(radiusKm * 14 + group.length * 3) }, 250),
  trigger: (payload: { group: BloodGroup; units: number; radiusKm: number }) =>
    mockRequest({ id: `SOS-${Math.floor(2200 + Math.random() * 99)}`, ...payload, status: "ACTIVE" as const }),
  respond: (broadcastId: string, answer: "AVAILABLE" | "UNAVAILABLE") =>
    mockRequest({ broadcastId, answer }),
};