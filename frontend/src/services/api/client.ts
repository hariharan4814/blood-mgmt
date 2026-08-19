/**
 * Central API client placeholder.
 *
 * STEP 1 (current): every service resolves mock fixtures through `mockRequest`.
 * STEP 2 (Django REST + JWT): implement `request()` below with fetch, attach the
 * JWT from the auth store, and swap each service call from `mockRequest(...)`
 * to `request(...)`. No UI component needs to change.
 */

export const API_BASE_URL = "/api"; // e.g. https://api.bms.local/api

export const MOCK_LATENCY_MS = 400;

export class ApiError extends Error {
  status: number;
  constructor(message: string, status = 500) {
    super(message);
    this.status = status;
  }
}

/** Simulates a network round-trip so loading/error states are exercised. */
export function mockRequest<T>(data: T, latency = MOCK_LATENCY_MS): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(structuredClone(data)), latency);
  });
}

/* eslint-disable @typescript-eslint/no-unused-vars */
/** Real implementation lands here once the Django backend is available. */
export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  throw new ApiError("Backend not connected yet (frontend step 1 uses mock data).", 501);
}