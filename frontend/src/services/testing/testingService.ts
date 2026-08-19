import { mockRequest } from "../api/client";
import { TEST_TYPES, pendingTests, testHistory } from "../mock/data";
import type { TestResult } from "@/lib/types";

export const testingService = {
  testTypes: TEST_TYPES,
  listPending: () => mockRequest(pendingTests),
  listHistory: () => mockRequest(testHistory),
  submitResult: (unitId: string, results: Record<string, TestResult>) =>
    mockRequest({ unitId, results, outcome: Object.values(results).includes("FAIL") ? "FAIL" : "PASS" }),
};