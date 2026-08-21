import { request } from "../api/client";
import type { Camp } from "@/lib/types";

export interface BackendCamp {
  id: number;
  blood_bank: number;
  blood_bank_id: number;
  blood_bank_name: string;
  name: string;
  location: string;
  camp_date: string;
  organizer: string;
  target_units: number;
  description: string;
  status: "PLANNED" | "ACTIVE" | "COMPLETED" | "CANCELLED";
  status_display: string;
  registrations_count: number;
  donations_count: number;
  created_by_id: number;
  created_by_username: string | null;
  created_at: string;
  updated_at: string;
}

export interface BackendCampRegistration {
  id: number;
  camp: number;
  camp_name: string;
  donor: number;
  donor_name: string;
  donor_blood_group: string;
  status: "REGISTERED" | "ATTENDED" | "CANCELLED";
  registered_at: string;
}

export interface CampCreatePayload {
  blood_bank: number;
  name: string;
  location: string;
  camp_date: string;
  organizer: string;
  target_units: number;
  description?: string;
}

function mapBackendCamp(
  c: BackendCamp,
  donorRegistrations?: BackendCampRegistration[],
): Camp {
  const matchingReg = donorRegistrations?.find(
    (r) => r.camp === c.id && r.status === "REGISTERED",
  );

  let status: Camp["status"] = "UPCOMING";
  if (c.status === "COMPLETED") {
    status = "COMPLETED";
  } else if (c.status === "ACTIVE") {
    status = "ONGOING";
  }

  return {
    id: `CMP-${c.id}`,
    name: c.name,
    organizer: c.organizer || "Blood Bank Facility",
    city: c.location.split(",")[0]?.trim() || c.location,
    address: c.location,
    date: c.camp_date,
    startTime: "09:00",
    endTime: "16:00",
    slots: c.target_units || 50,
    registered: c.registrations_count || 0,
    status,
    description: c.description || `Blood donation drive organized by ${c.organizer}.`,
  };
}

export const campService = {
  /**
   * List all scheduled and active donation camps.
   */
  list: async (): Promise<Camp[]> => {
    let registrations: BackendCampRegistration[] = [];
    try {
      const regRes = await request<
        | { results?: BackendCampRegistration[] }
        | BackendCampRegistration[]
      >("/api/donation-camp-registrations/");
      registrations = Array.isArray(regRes) ? regRes : regRes.results || [];
    } catch {
      registrations = [];
    }

    const response = await request<
      { results?: BackendCamp[] } | BackendCamp[]
    >("/api/donation-camps/");

    const camps = Array.isArray(response) ? response : response.results || [];
    return camps.map((c) => mapBackendCamp(c, registrations));
  },

  /**
   * Retrieve single camp detail.
   */
  get: async (id: string | number): Promise<Camp | null> => {
    const rawId = typeof id === "string" ? id.replace(/^CMP-/, "") : id;
    try {
      const res = await request<BackendCamp>(`/api/donation-camps/${rawId}/`);
      return mapBackendCamp(res);
    } catch {
      return null;
    }
  },

  /**
   * Register authenticated donor for a donation camp.
   */
  register: async (
    campId: string | number,
  ): Promise<BackendCampRegistration> => {
    const rawId = typeof campId === "string" ? campId.replace(/^CMP-/, "") : campId;
    return request<BackendCampRegistration>(
      `/api/donation-camps/${rawId}/register/`,
      {
        method: "POST",
        body: JSON.stringify({}),
      },
    );
  },

  /**
   * Cancel an existing camp registration.
   */
  cancelRegistration: async (
    registrationId: number,
  ): Promise<BackendCampRegistration> => {
    return request<BackendCampRegistration>(
      `/api/donation-camp-registrations/${registrationId}/cancel/`,
      {
        method: "POST",
      },
    );
  },

  /**
   * Schedule and publish a new donation camp (Blood Bank Admin / Super Admin).
   */
  create: async (payload: CampCreatePayload): Promise<Camp> => {
    const res = await request<BackendCamp>("/api/donation-camps/", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    return mapBackendCamp(res);
  },

  /**
   * Save / Create alias for UI compatibility.
   */
  save: async (payload: Partial<Camp> & { blood_bank?: number }): Promise<Camp> => {
    const backendPayload: CampCreatePayload = {
      blood_bank: payload.blood_bank || 1,
      name: payload.name || "Donation Camp",
      location: payload.address || payload.city || "Blood Bank Center",
      camp_date: payload.date || new Date().toISOString().split("T")[0] || "2026-09-01",
      organizer: payload.organizer || "Blood Bank Team",
      target_units: payload.slots || 50,
      description: payload.description || "",
    };
    return campService.create(backendPayload);
  },

  /**
   * Cancel a scheduled camp.
   */
  cancelCamp: async (campId: string | number): Promise<Camp> => {
    const rawId = typeof campId === "string" ? campId.replace(/^CMP-/, "") : campId;
    const res = await request<BackendCamp>(`/api/donation-camps/${rawId}/`, {
      method: "PATCH",
      body: JSON.stringify({ status: "CANCELLED" }),
    });
    return mapBackendCamp(res);
  },
};