import { request } from "../api/client";
import type { BloodGroup, Role } from "@/lib/types";

export interface UserProfile {
  id: number | string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: Role;
  role_display: string;
  phone: string | null;
  blood_group?: BloodGroup | null;
  latitude: number | null;
  longitude: number | null;
  address: string | null;
  profile_image: string | null;
  profile_image_url: string | null;
  is_verified: boolean;
  is_active: boolean;
  date_joined: string;
}

export interface DonorDetails {
  id: number;
  blood_group: BloodGroup;
  date_of_birth: string | null;
  weight_kg: number | null;
  last_donation_date: string | null;
  latitude: number | null;
  longitude: number | null;
  is_eligible: boolean;
  age: number | null;
  created_at: string;
  updated_at: string;
}

export interface DonorEligibility {
  is_eligible: boolean;
  reasons: string[];
  criteria: {
    age: { passed: boolean; value: number | null; requirement: string };
    weight: { passed: boolean; value_kg: number | null; requirement: string };
    donation_interval: {
      passed: boolean;
      last_donation_date: string | null;
      days_since_last_donation: number | null;
      days_until_next_eligible: number;
      requirement: string;
    };
  };
}

export const profileService = {
  /**
   * Retrieve the authenticated user's profile metadata.
   */
  getProfile: async (): Promise<UserProfile> => {
    return request<UserProfile>("/api/profile/");
  },

  /**
   * Update personal profile fields (first_name, last_name, email, phone).
   */
  updateProfile: async (data: {
    first_name?: string;
    last_name?: string;
    email?: string;
    phone?: string | null;
    blood_group?: BloodGroup | null | undefined;
    latitude?: number | null;
    longitude?: number | null;
    address?: string | null;
  }): Promise<UserProfile> => {
    return request<UserProfile>("/api/profile/", {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  /**
   * Upload or change profile picture avatar (multipart/form-data).
   */
  uploadProfileImage: async (file: File): Promise<UserProfile> => {
    const formData = new FormData();
    formData.append("profile_image", file);

    return request<UserProfile>("/api/profile/image/", {
      method: "POST",
      body: formData,
    });
  },

  /**
   * Remove profile picture avatar.
   */
  deleteProfileImage: async (): Promise<{ detail: string }> => {
    return request<{ detail: string }>("/api/profile/image/", {
      method: "DELETE",
    });
  },

  /**
   * Retrieve donor-specific medical attributes for authenticated donor.
   */
  getDonorDetails: async (): Promise<DonorDetails | null> => {
    try {
      return await request<DonorDetails>("/api/donors/me/");
    } catch {
      return null;
    }
  },

  /**
   * Retrieve donor eligibility breakdown for authenticated donor.
   */
  getDonorEligibility: async (): Promise<DonorEligibility | null> => {
    try {
      return await request<DonorEligibility>("/api/donors/me/eligibility/");
    } catch {
      return null;
    }
  },

  /**
   * Update donor medical attributes.
   */
  updateDonorDetails: async (data: {
    blood_group?: BloodGroup;
    date_of_birth?: string | null;
    weight_kg?: number | null;
    last_donation_date?: string | null;
  }): Promise<DonorDetails> => {
    return request<DonorDetails>("/api/donors/me/", {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },
};
