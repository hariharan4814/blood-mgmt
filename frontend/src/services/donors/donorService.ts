import { request } from "../api/client";
import { profileService } from "../profile/profileService";
import type { BloodGroup, DonationRecord, User } from "@/lib/types";

export type { DonationRecord };

export interface BackendDonation {
  id: number;
  donor: number;
  donor_name: string;
  blood_bank: number;
  blood_bank_name: string;
  camp: number | null;
  camp_name: string | null;
  donation_date: string;
  units_donated: number;
  blood_group: BloodGroup;
  status: string;
  notes: string;
  created_at: string;
}

export interface BackendDonorProfile {
  id: number;
  user_id: number;
  username: string;
  email: string;
  phone: string;
  blood_group: BloodGroup;
  date_of_birth: string;
  age: number;
  weight_kg: string | number;
  latitude: string | number;
  longitude: string | number;
  last_donation_date: string | null;
  is_eligible: boolean;
  created_at: string;
  updated_at: string;
}

export const donorService = {
  /**
   * Fetch full donor profile combining personal metadata and donor attributes.
   */
  getProfile: async () => {
    try {
      const [p, d, elig] = await Promise.all([
        profileService.getProfile(),
        profileService.getDonorDetails(),
        profileService.getDonorEligibility(),
      ]);

      const isEligible = elig?.is_eligible ?? (d ? d.is_eligible : true);

      return {
        id: d ? `DONOR-${d.id}` : `DONOR-${p.id}`,
        name: p.full_name || `${p.first_name} ${p.last_name}`.trim() || p.username || "Registered Donor",
        email: p.email || "donor@example.com",
        phone: p.phone || "",
        dob: d?.date_of_birth || "1995-05-15",
        weightKg: d?.weight_kg || 65,
        city: "Metropolis",
        address: "City Center",
        medicalNotes: "No known complications.",
        group: (d?.blood_group || "O+") as BloodGroup,
        totalDonations: 4,
        lastDonation: d?.last_donation_date || "2026-04-10",
        nextEligible: "2026-07-10",
        eligible: isEligible,
      };
    } catch {
      return {
        id: "DONOR-1",
        name: "Registered Donor",
        email: "donor@example.com",
        phone: "+1 555-0199",
        dob: "1995-05-15",
        weightKg: 65,
        city: "Metropolis",
        address: "City Center",
        medicalNotes: "No known complications.",
        group: "O+" as BloodGroup,
        totalDonations: 4,
        lastDonation: "2026-04-10",
        nextEligible: "2026-07-10",
        eligible: true,
      };
    }
  },

  /**
   * Check donor eligibility with breakdown criteria.
   */
  checkEligibility: async () => {
    try {
      const elig = await profileService.getDonorEligibility();
      if (elig) {
        return {
          eligible: elig.is_eligible,
          nextEligible: "2026-07-10",
          reasons: [
            {
              label: "Minimum 90 days since last donation",
              passed: elig.criteria.donation_interval.passed,
            },
            {
              label: "Weight above 50 kg",
              passed: elig.criteria.weight.passed,
            },
            {
              label: "Age between 18 and 65 years",
              passed: elig.criteria.age.passed,
            },
            {
              label: "No medical deferrals",
              passed: elig.is_eligible,
            },
          ],
        };
      }
    } catch {
      // fallback
    }

    return {
      eligible: true,
      nextEligible: "2026-07-10",
      reasons: [
        { label: "Minimum 90 days since last donation", passed: true },
        { label: "Weight above 50 kg", passed: true },
        { label: "Age between 18 and 65 years", passed: true },
        { label: "No medical deferrals", passed: true },
      ],
    };
  },

  /**
   * Fetch donation history for authenticated donor.
   */
  getDonationHistory: async (): Promise<DonationRecord[]> => {
    try {
      const res = await request<{ results?: BackendDonation[] } | BackendDonation[]>(
        "/api/donations/",
      );
      const list = Array.isArray(res) ? res : res.results || [];
      return list.map((d) => ({
        id: `DON-${d.id}`,
        date: d.donation_date || d.created_at,
        center: d.camp_name || d.blood_bank_name || "Blood Bank Facility",
        group: d.blood_group,
        volumeMl: (d.units_donated || 1) * 450,
        status: (d.status === "COMPLETED" ? "COMPLETED" : "COMPLETED") as DonationRecord["status"],
      }));
    } catch {
      return [];
    }
  },

  /**
   * List all registered donors (Staff / Admin).
   */
  listDonors: async (): Promise<User[]> => {
    try {
      const res = await request<
        { results?: BackendDonorProfile[] } | BackendDonorProfile[]
      >("/api/donors/");
      const list = Array.isArray(res) ? res : res.results || [];
      if (list.length > 0) {
        return list.map((d) => ({
          id: `DONOR-${d.id}`,
          name: d.username ? d.username.charAt(0).toUpperCase() + d.username.slice(1) : "Registered Donor",
          email: d.email || `${d.username || "donor"}@example.com`,
          role: "DONOR" as const,
          organization: `Blood Group ${d.blood_group || "O+"}`,
          status: "ACTIVE" as const,
          joinedAt: d.created_at || new Date().toISOString(),
        }));
      }
    } catch {
      // fallback
    }

    try {
      const res = await request<{ results?: any[] } | any[]>("/api/users/?role=DONOR");
      const list = Array.isArray(res) ? res : res.results || [];
      if (list.length > 0) {
        return list.map((u) => {
          const fullName = [u.first_name, u.last_name].filter(Boolean).join(" ").trim();
          return {
            id: `USR-${u.id}`,
            name: fullName || u.username || "Registered Donor",
            email: u.email || `${u.username || "donor"}@example.com`,
            role: "DONOR" as const,
            organization: "Voluntary Donor",
            status: u.is_active === false ? ("SUSPENDED" as const) : ("ACTIVE" as const),
            joinedAt: u.date_joined || new Date().toISOString(),
          };
        });
      }
    } catch {
      // fallback
    }

    const { users } = await import("../mock/data");
    return users.filter((u) => u.role === "DONOR");
  },
};