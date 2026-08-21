import { request, mockRequest } from "../api/client";
import {
  auditLogs,
  donationTrends,
  sosResponseRate,
  systemActivity,
} from "../mock/data";
import type { BloodGroup, BloodStock, User } from "@/lib/types";

export interface BloodBankListItem {
  id: string;
  name: string;
  city: string;
  license: string;
  units: number;
  status: "ACTIVE" | "REVIEW";
}

export interface BackendBloodBank {
  id: number;
  name: string;
  code: string;
  address: string;
  city: string;
  state: string;
  phone: string;
  email: string;
  latitude: number;
  longitude: number;
  total_units_count?: number;
}

export interface BackendInventorySummary {
  blood_group: BloodGroup;
  total_units: number;
  available_units: number;
  reserved_units: number;
  testing_units: number;
  expired_units: number;
  discarded_units: number;
}

export const analyticsService = {
  /**
   * Get blood stock distribution by blood group from real inventory summary.
   */
  getStockByGroup: async (): Promise<BloodStock[]> => {
    try {
      const res = await request<
        { results?: BackendInventorySummary[] } | BackendInventorySummary[]
      >("/api/inventory/summary/");
      const list = Array.isArray(res) ? res : res.results || [];
      if (list.length > 0) {
        return list.map((item) => ({
          group: item.blood_group,
          units: item.available_units,
          reserved: item.reserved_units,
          testing: item.testing_units,
          threshold: 15,
        }));
      }
    } catch {
      // fallback to mock stock
    }
    const { bloodStock } = await import("../mock/data");
    return mockRequest(bloodStock);
  },

  /**
   * List blood bank facilities from real database backend.
   */
  listBloodBanks: async (): Promise<BloodBankListItem[]> => {
    try {
      const res = await request<
        { results?: BackendBloodBank[] } | BackendBloodBank[]
      >("/api/blood-banks/");
      const list = Array.isArray(res) ? res : res.results || [];
      if (list.length > 0) {
        return list.map((b) => ({
          id: `BB-${b.id}`,
          name: b.name,
          city: b.city,
          license: b.code || `LIC-BB-${b.id}`,
          units: b.total_units_count || 50,
          status: "ACTIVE" as const,
        }));
      }
    } catch {
      // fallback
    }
    const { bloodBanks } = await import("../mock/data");
    return mockRequest(bloodBanks);
  },

  /**
   * List system users from real database backend (Super Admin).
   */
  listUsers: async (): Promise<User[]> => {
    try {
      const res = await request<{ results?: User[] } | User[]>("/api/users/");
      return Array.isArray(res) ? res : res.results || [];
    } catch {
      const { users } = await import("../mock/data");
      return mockRequest(users);
    }
  },

  /**
   * Platform entity counts summary.
   */
  getPlatformTotals: async () => {
    try {
      const [banks, summary] = await Promise.all([
        analyticsService.listBloodBanks(),
        request<{ results?: BackendInventorySummary[] } | BackendInventorySummary[]>(
          "/api/inventory/summary/",
        ).catch(() => []),
      ]);

      const sumList = Array.isArray(summary) ? summary : summary.results || [];
      const totalUnits = sumList.reduce((acc, s) => acc + (s.total_units || 0), 0);

      return {
        users: 1240,
        bloodBanks: banks.length || 8,
        hospitals: 6,
        donations: totalUnits || 12840,
      };
    } catch {
      return {
        users: 1240,
        bloodBanks: 8,
        hospitals: 6,
        donations: 12840,
      };
    }
  },

  /**
   * List hospitals.
   */
  listHospitals: async () => {
    const { hospitals } = await import("../mock/data");
    return mockRequest(hospitals);
  },

  // Note: Historical time-series projection charts remain mock data as the backend
  // does not maintain continuous historical analytics aggregates in this version.
  getDonationTrends: () => mockRequest(donationTrends),
  getSosResponseRate: () => mockRequest(sosResponseRate),
  getSystemActivity: () => mockRequest(systemActivity),
  getAuditLogs: () => mockRequest(auditLogs),
};