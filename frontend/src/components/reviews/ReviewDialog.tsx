import React, { useState } from "react";
import { Star, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { reviewService } from "@/services/reviews/reviewService";

interface ReviewDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  targetType: "hospital" | "blood_bank";
  targetId: number;
  targetName: string;
  onSubmitted?: () => void;
}

export function ReviewDialog({
  open,
  onOpenChange,
  targetType,
  targetId,
  targetName,
  onSubmitted,
}: ReviewDialogProps) {
  const [rating, setRating] = useState<number>(5);
  const [hoverRating, setHoverRating] = useState<number>(0);
  const [comment, setComment] = useState<string>("");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!comment.trim() || comment.trim().length < 3) {
      setError("Please enter a review comment of at least 3 characters.");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await reviewService.submitReview({
        hospital: targetType === "hospital" ? targetId : undefined,
        blood_bank: targetType === "blood_bank" ? targetId : undefined,
        rating,
        comment: comment.trim(),
      });

      toast.success("Your review has been submitted and is awaiting administrator approval.");
      setComment("");
      setRating(5);
      onOpenChange(false);
      onSubmitted?.();
    } catch (err: any) {
      const msg = err?.message || "Failed to submit review. Please try again.";
      setError(msg);
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Review {targetName}</DialogTitle>
            <DialogDescription>
              Share your experience with this facility. New reviews are reviewed by administrators before being published.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {error && (
              <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label>Rating</Label>
              <div className="flex items-center gap-1">
                {[1, 2, 3, 4, 5].map((star) => {
                  const active = (hoverRating || rating) >= star;
                  return (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setRating(star)}
                      onMouseEnter={() => setHoverRating(star)}
                      onMouseLeave={() => setHoverRating(0)}
                      className="p-1 focus:outline-none transition-transform hover:scale-110"
                      aria-label={`${star} star`}
                    >
                      <Star
                        className={`h-7 w-7 ${
                          active ? "fill-amber-400 text-amber-400" : "text-muted-foreground/30"
                        }`}
                      />
                    </button>
                  );
                })}
                <span className="ml-2 font-semibold text-sm text-muted-foreground">
                  {hoverRating || rating} / 5 Stars
                </span>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="review-comment">Your Feedback *</Label>
              <Textarea
                id="review-comment"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Describe your donation, reception, or clinical experience..."
                rows={4}
                required
                minLength={3}
                maxLength={2000}
              />
              <p className="text-xs text-muted-foreground">
                Minimum 3 characters, maximum 2000 characters.
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={submitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={submitting} className="bg-primary hover:bg-primary/90">
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                "Submit Review"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
