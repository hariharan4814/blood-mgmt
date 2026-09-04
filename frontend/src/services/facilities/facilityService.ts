import { request } from "../api/client";

export interface HospitalFacility {
  id: number;
  name: string;
  address: string;
  city: string;
  state: string;
  contact_number: string;
  email: string;
  beds: number;
  latitude: number | null;
  longitude: number | null;
  is_active: boolean;
  average_rating: number | null;
  review_count: number;
  created_at: string;
  updated_at: string;
}

export interface HospitalInput {
  name: string;
  address?: string | undefined;
  city: string;
  state?: string | undefined;
  contact_number?: string | undefined;
  email?: string | undefined;
  beds?: number | undefined;
  latitude?: number | null | undefined;
  longitude?: number | null | undefined;
  is_active?: boolean | undefined;
}

export interface BloodBankFacility {
  id: number;
  name: string;
  address: string;
  city: string;
  state: string;
  contact_number: string;
  email: string;
  capacity: number;
  latitude: number | null;
  longitude: number | null;
  is_active: boolean;
  admin: number | null;
  admin_id: number | null;
  admin_username: string | null;
  admin_email: string | null;
  total_units_count: number;
  average_rating: number | null;
  review_count: number;
  created_at: string;
  updated_at: string;
}

export interface BloodBankInput {
  name: string;
  address?: string | undefined;
  city: string;
  state?: string | undefined;
  contact_number?: string | undefined;
  email?: string | undefined;
  capacity?: number | undefined;
  latitude?: number | null | undefined;
  longitude?: number | null | undefined;
  is_active?: boolean | undefined;
  admin?: number | null | undefined;
}

export const facilityService = {
  // Hospital APIs
  getHospitals: async (params?: { search?: string | undefined; status?: string | undefined } | undefined): Promise<HospitalFacility[]> => {
    const query = new URLSearchParams();
    if (params?.search) query.append("search", params.search);
    if (params?.status && params.status !== "all") query.append("status", params.status);
    const qs = query.toString();
    const res = await request<any>(`/api/hospitals/${qs ? `?${qs}` : ""}`);
    return Array.isArray(res) ? res : (res?.results as HospitalFacility[]) || [];
  },

  getHospital: async (id: number): Promise<HospitalFacility> => {
    return request<HospitalFacility>(`/api/hospitals/${id}/`);
  },

  createHospital: async (data: HospitalInput): Promise<HospitalFacility> => {
    return request<HospitalFacility>("/api/hospitals/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  updateHospital: async (id: number, data: Partial<HospitalInput>): Promise<HospitalFacility> => {
    return request<HospitalFacility>(`/api/hospitals/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  deleteHospital: async (id: number): Promise<void> => {
    await request<void>(`/api/hospitals/${id}/`, {
      method: "DELETE",
    });
  },

  // Blood Bank APIs
  getBloodBanks: async (params?: { search?: string | undefined; status?: string | undefined } | undefined): Promise<BloodBankFacility[]> => {
    const query = new URLSearchParams();
    if (params?.search) query.append("search", params.search);
    if (params?.status && params.status !== "all") query.append("status", params.status);
    const qs = query.toString();
    const res = await request<any>(`/api/blood-banks/${qs ? `?${qs}` : ""}`);
    return Array.isArray(res) ? res : (res?.results as BloodBankFacility[]) || [];
  },

  getBloodBank: async (id: number): Promise<BloodBankFacility> => {
    return request<BloodBankFacility>(`/api/blood-banks/${id}/`);
  },

  createBloodBank: async (data: BloodBankInput): Promise<BloodBankFacility> => {
    return request<BloodBankFacility>("/api/blood-banks/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  updateBloodBank: async (id: number, data: Partial<BloodBankInput>): Promise<BloodBankFacility> => {
    return request<BloodBankFacility>(`/api/blood-banks/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  deleteBloodBank: async (id: number): Promise<void> => {
    await request<void>(`/api/blood-banks/${id}/`, {
      method: "DELETE",
    });
  },
};
