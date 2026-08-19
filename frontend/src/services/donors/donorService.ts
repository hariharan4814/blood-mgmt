import { mockRequest } from "../api/client";
import { donationHistory, donorProfile, users } from "../mock/data";

export const donorService = {
  getProfile: () => mockRequest(donorProfile),
  updateProfile: (patch: Partial<typeof donorProfile>) => mockRequest({ ...donorProfile, ...patch }),
  getDonationHistory: () => mockRequest(donationHistory),
  listDonors: () => mockRequest(users.filter((u) => u.role === "DONOR")),
  checkEligibility: () =>
    mockRequest({
      eligible: donorProfile.eligible,
      nextEligible: donorProfile.nextEligible,
      reasons: [
        { label: "Minimum 90 days since last donation", passed: true },
        { label: "Weight above 50 kg", passed: true },
        { label: "Haemoglobin above 12.5 g/dL", passed: true },
        { label: "No recent illness or medication", passed: true },
      ],
    }),
};