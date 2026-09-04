import { request } from "../api/client";

export type ReviewStatus = "PENDING" | "APPROVED" | "REJECTED";
export type ReviewTargetType = "HOSPITAL" | "BLOOD_BANK";

export interface ReviewItem {
  id: number;
  reviewer: {
    id: number;
    username: string;
    full_name: string;
    role: string;
  };
  target_type: ReviewTargetType | string;
  target_name: string;
  target_id: number | null;
  hospital: number | null;
  blood_bank: number | null;
  rating: number;
  comment: string;
  status: ReviewStatus;
  reviewed_by: {
    id: number;
    username: string;
    full_name: string;
    role: string;
  } | null;
  reviewed_at: string | null;
  rejection_reason: string;
  created_at: string;
  updated_at: string;
}

export interface ReviewInput {
  hospital?: number | null | undefined;
  blood_bank?: number | null | undefined;
  rating: number;
  comment: string;
}

export interface ReviewFilterParams {
  status?: string | undefined;
  target_type?: string | undefined;
  hospital?: number | undefined;
  blood_bank?: number | undefined;
  rating?: number | undefined;
  search?: string | undefined;
}

export const reviewService = {
  getReviews: async (params?: ReviewFilterParams | undefined): Promise<ReviewItem[]> => {
    const query = new URLSearchParams();
    if (params?.status && params.status !== "all") query.append("status", params.status);
    if (params?.target_type && params.target_type !== "all") query.append("target_type", params.target_type);
    if (params?.hospital) query.append("hospital", String(params.hospital));
    if (params?.blood_bank) query.append("blood_bank", String(params.blood_bank));
    if (params?.rating) query.append("rating", String(params.rating));
    if (params?.search) query.append("search", params.search);
    const qs = query.toString();
    const res = await request<any>(`/api/reviews/${qs ? `?${qs}` : ""}`);
    return Array.isArray(res) ? res : (res?.results as ReviewItem[]) || [];
  },

  submitReview: async (data: ReviewInput): Promise<ReviewItem> => {
    return request<ReviewItem>("/api/reviews/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  approveReview: async (id: number): Promise<ReviewItem> => {
    return request<ReviewItem>(`/api/reviews/${id}/approve/`, {
      method: "POST",
    });
  },

  rejectReview: async (id: number, rejectionReason?: string | undefined): Promise<ReviewItem> => {
    return request<ReviewItem>(`/api/reviews/${id}/reject/`, {
      method: "POST",
      body: JSON.stringify({ rejection_reason: rejectionReason || "" }),
    });
  },

  deleteReview: async (id: number): Promise<void> => {
    await request<void>(`/api/reviews/${id}/`, {
      method: "DELETE",
    });
  },
};
