import { mockRequest } from "../api/client";
import {
  auditLogs,
  bloodBanks,
  bloodStock,
  donationTrends,
  hospitals,
  sosResponseRate,
  systemActivity,
  users,
} from "../mock/data";

export const analyticsService = {
  getStockByGroup: () => mockRequest(bloodStock),
  getDonationTrends: () => mockRequest(donationTrends),
  getSosResponseRate: () => mockRequest(sosResponseRate),
  getSystemActivity: () => mockRequest(systemActivity),
  getPlatformTotals: () =>
    mockRequest({
      users: users.length * 214,
      bloodBanks: bloodBanks.length,
      hospitals: hospitals.length,
      donations: 12840,
    }),
  getAuditLogs: () => mockRequest(auditLogs),
  listUsers: () => mockRequest(users),
  listBloodBanks: () => mockRequest(bloodBanks),
  listHospitals: () => mockRequest(hospitals),
};