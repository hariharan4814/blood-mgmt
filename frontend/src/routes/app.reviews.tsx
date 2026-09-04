import { useState, useEffect } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  Building2,
  CheckCircle2,
  Filter,
  Hospital,
  Loader2,
  MessageSquare,
  Search,
  ShieldAlert,
  Star,
  ThumbsDown,
  ThumbsUp,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/providers/AuthProvider";
import { reviewService, type ReviewItem, type ReviewStatus } from "@/services/reviews/reviewService";

export const Route = createFileRoute("/app/reviews")({
  head: () => ({
    meta: [
      { title: "Review Moderation — Blood Management System" },
      { name: "description", content: "Super Administrator moderation console for facility ratings and reviews." },
      { property: "og:title", content: "Review Moderation — Blood Management System" },
      { property: "og:description", content: "Moderate facility reviews and ratings." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: ReviewsModerationPage,
});

function ReviewsModerationPage() {
  const { user: currentUser } = useAuth();
  const isSuperAdmin = currentUser?.role === "SUPER_ADMIN";

  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [targetTypeFilter, setTargetTypeFilter] = useState<string>("all");
  const [ratingFilter, setRatingFilter] = useState<string>("all");
  const [search, setSearch] = useState<string>("");

  // Reject modal state
  const [rejectModalOpen, setRejectModalOpen] = useState<boolean>(false);
  const [targetReview, setTargetReview] = useState<ReviewItem | null>(null);
  const [rejectionReason, setRejectionReason] = useState<string>("");
  const [moderating, setModerating] = useState<boolean>(false);

  const fetchReviews = async () => {
    try {
      setLoading(true);
      const data = await reviewService.getReviews({
        status: statusFilter !== "all" ? statusFilter : undefined,
        target_type: targetTypeFilter !== "all" ? targetTypeFilter : undefined,
        rating: ratingFilter !== "all" ? parseInt(ratingFilter, 10) : undefined,
        search: search.trim() || undefined,
      });
      setReviews(data);
    } catch (err: any) {
      toast.error(err?.message || "Failed to load reviews.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isSuperAdmin) {
      fetchReviews();
    }
  }, [statusFilter, targetTypeFilter, ratingFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchReviews();
  };

  const handleApprove = async (review: ReviewItem) => {
    setModerating(true);
    try {
      await reviewService.approveReview(review.id);
      toast.success(`Review for "${review.target_name}" approved successfully.`);
      fetchReviews();
    } catch (err: any) {
      toast.error(err?.message || "Failed to approve review.");
    } finally {
      setModerating(false);
    }
  };

  const openRejectModal = (review: ReviewItem) => {
    setTargetReview(review);
    setRejectionReason("");
    setRejectModalOpen(true);
  };

  const handleConfirmReject = async () => {
    if (!targetReview) return;
    setModerating(true);
    try {
      await reviewService.rejectReview(targetReview.id, rejectionReason.trim());
      toast.success(`Review for "${targetReview.target_name}" rejected.`);
      setRejectModalOpen(false);
      fetchReviews();
    } catch (err: any) {
      toast.error(err?.message || "Failed to reject review.");
    } finally {
      setModerating(false);
    }
  };

  if (!isSuperAdmin) {
    return (
      <DashboardLayout title="Review Moderation">
        <div className="py-16 text-center max-w-md mx-auto space-y-4">
          <ShieldAlert className="h-12 w-12 text-destructive mx-auto opacity-70" />
          <h2 className="text-xl font-bold">Access Restricted</h2>
          <p className="text-sm text-muted-foreground">
            Review moderation is restricted to Super Administrators only. Please log in with administrative privileges.
          </p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Review Moderation">
      <div className="mb-6">
        <PageHeader
          title="Review Moderation"
          description="Evaluate and approve or reject user-submitted ratings and reviews for partner Hospitals and Blood Banks."
        />
      </div>

      {/* Multi-criteria filter bar */}
      <div className="mb-6 bg-card p-4 rounded-lg border space-y-3">
        <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
          <form onSubmit={handleSearchSubmit} className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search reviewer, facility name, or review comment..."
              className="pl-9"
            />
          </form>

          <div className="flex flex-wrap items-center gap-2">
            {/* Status Filter */}
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[125px] h-9">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="PENDING">Pending</SelectItem>
                <SelectItem value="APPROVED">Approved</SelectItem>
                <SelectItem value="REJECTED">Rejected</SelectItem>
              </SelectContent>
            </Select>

            {/* Target Type Filter */}
            <Select value={targetTypeFilter} onValueChange={setTargetTypeFilter}>
              <SelectTrigger className="w-[135px] h-9">
                <SelectValue placeholder="Target" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Targets</SelectItem>
                <SelectItem value="HOSPITAL">Hospitals</SelectItem>
                <SelectItem value="BLOOD_BANK">Blood Banks</SelectItem>
              </SelectContent>
            </Select>

            {/* Rating Filter */}
            <Select value={ratingFilter} onValueChange={setRatingFilter}>
              <SelectTrigger className="w-[115px] h-9">
                <SelectValue placeholder="Rating" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Stars</SelectItem>
                <SelectItem value="5">5 Stars</SelectItem>
                <SelectItem value="4">4 Stars</SelectItem>
                <SelectItem value="3">3 Stars</SelectItem>
                <SelectItem value="2">2 Stars</SelectItem>
                <SelectItem value="1">1 Star</SelectItem>
              </SelectContent>
            </Select>

            <Button type="button" variant="secondary" size="sm" onClick={fetchReviews}>
              Apply
            </Button>
          </div>
        </div>
      </div>

      {/* Moderation Table */}
      <SectionCard bodyClassName="p-0">
        {loading ? (
          <TableSkeleton cols={6} />
        ) : reviews.length === 0 ? (
          <div className="py-12 text-center text-muted-foreground">
            <MessageSquare className="mx-auto h-12 w-12 opacity-30 mb-2" />
            <p className="text-base font-medium">No reviews found</p>
            <p className="text-sm mt-1">There are no reviews matching the current filters.</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Reviewer</TableHead>
                <TableHead>Target Facility</TableHead>
                <TableHead>Rating</TableHead>
                <TableHead className="w-[30%]">Feedback</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {reviews.map((r) => {
                const isHospital = r.target_type === "HOSPITAL";

                return (
                  <TableRow key={r.id}>
                    <TableCell className="align-top">
                      <div className="font-medium text-sm">
                        {r.reviewer.full_name || r.reviewer.username}
                      </div>
                      <div className="text-xs text-muted-foreground mt-0.5">
                        <span className="font-mono">{r.reviewer.role}</span> • {new Date(r.created_at).toLocaleDateString()}
                      </div>
                    </TableCell>

                    <TableCell className="align-top">
                      <div className="flex items-center gap-1.5">
                        {isHospital ? (
                          <Hospital className="h-4 w-4 text-blue-500 shrink-0" />
                        ) : (
                          <Building2 className="h-4 w-4 text-emerald-500 shrink-0" />
                        )}
                        <span className="font-semibold text-sm">{r.target_name}</span>
                      </div>
                      <span className="text-[10px] text-muted-foreground ml-5 block uppercase tracking-wide">
                        {isHospital ? "Hospital" : "Blood Bank"}
                      </span>
                    </TableCell>

                    <TableCell className="align-top">
                      <div className="flex items-center gap-1">
                        <div className="flex text-amber-400">
                          {Array.from({ length: r.rating }).map((_, i) => (
                            <Star key={i} className="h-3.5 w-3.5 fill-current" />
                          ))}
                        </div>
                        <span className="font-semibold text-xs ml-1">{r.rating} / 5</span>
                      </div>
                    </TableCell>

                    <TableCell className="align-top">
                      <p className="text-xs leading-relaxed text-foreground/90 whitespace-pre-line">
                        {r.comment}
                      </p>
                      {r.rejection_reason && (
                        <div className="mt-1.5 text-xs text-destructive bg-destructive/10 p-1.5 rounded">
                          <span className="font-semibold">Rejection reason: </span>
                          {r.rejection_reason}
                        </div>
                      )}
                      {r.reviewed_by && (
                        <div className="text-[10px] text-muted-foreground mt-1">
                          Moderated by {r.reviewed_by.username} on{" "}
                          {r.reviewed_at ? new Date(r.reviewed_at).toLocaleDateString() : ""}
                        </div>
                      )}
                    </TableCell>

                    <TableCell className="align-top">
                      <StatusBadge
                        status={
                          r.status === "APPROVED"
                            ? "APPROVED"
                            : r.status === "REJECTED"
                            ? "REJECTED"
                            : "PENDING"
                        }
                      />
                    </TableCell>

                    <TableCell className="align-top text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {r.status !== "APPROVED" && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleApprove(r)}
                            disabled={moderating}
                            className="text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 h-8 gap-1"
                          >
                            <ThumbsUp className="h-3.5 w-3.5" />
                            Approve
                          </Button>
                        )}
                        {r.status !== "REJECTED" && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => openRejectModal(r)}
                            disabled={moderating}
                            className="text-destructive hover:text-destructive hover:bg-destructive/10 h-8 gap-1"
                          >
                            <ThumbsDown className="h-3.5 w-3.5" />
                            Reject
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </SectionCard>

      {/* Rejection Reason Modal */}
      <Dialog open={rejectModalOpen} onOpenChange={setRejectModalOpen}>
        <DialogContent className="sm:max-w-[420px]">
          <DialogHeader>
            <DialogTitle>Reject Review</DialogTitle>
            <DialogDescription>
              Provide an optional reason for rejecting this review. Rejected reviews will not appear publicly.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="reject-reason">Rejection Explanation (Optional)</Label>
              <Textarea
                id="reject-reason"
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="e.g. Inappropriate language, commercial solicitation, off-topic..."
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setRejectModalOpen(false)}
              disabled={moderating}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              onClick={handleConfirmReject}
              disabled={moderating}
            >
              {moderating ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Confirm Rejection
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
