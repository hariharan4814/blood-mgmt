import { cn } from "@/lib/utils";

type Tone = "success" | "warning" | "danger" | "info" | "neutral";

const TONE_CLASSES: Record<Tone, string> = {
  success: "bg-success/12 text-success border-success/25",
  warning: "bg-warning/15 text-warning-foreground border-warning/40",
  danger: "bg-destructive/12 text-destructive border-destructive/25",
  info: "bg-info/12 text-info border-info/25",
  neutral: "bg-muted text-muted-foreground border-border",
};

const MAP: Record<string, { label: string; tone: Tone }> = {
  // unit status
  TESTING: { label: "Testing", tone: "info" },
  AVAILABLE: { label: "Available", tone: "success" },
  RESERVED: { label: "Reserved", tone: "warning" },
  DISPATCHED: { label: "Dispatched", tone: "info" },
  DISCARDED: { label: "Discarded", tone: "danger" },
  // requests
  PENDING: { label: "Pending", tone: "warning" },
  APPROVED: { label: "Approved", tone: "success" },
  REJECTED: { label: "Rejected", tone: "danger" },
  COMPLETED: { label: "Completed", tone: "success" },
  CREATED: { label: "Created", tone: "neutral" },
  // urgency
  NORMAL: { label: "Normal", tone: "neutral" },
  HIGH: { label: "High", tone: "warning" },
  CRITICAL: { label: "Critical", tone: "danger" },
  // tests
  PASS: { label: "Passed", tone: "success" },
  FAIL: { label: "Failed", tone: "danger" },
  // generic
  ACTIVE: { label: "Active", tone: "success" },
  SUSPENDED: { label: "Suspended", tone: "danger" },
  REVIEW: { label: "Under review", tone: "warning" },
  UPCOMING: { label: "Upcoming", tone: "info" },
  ONGOING: { label: "Ongoing", tone: "success" },
  FULFILLED: { label: "Fulfilled", tone: "success" },
  EXPIRED: { label: "Expired", tone: "neutral" },
  LOW: { label: "Low", tone: "danger" },
  MODERATE: { label: "Moderate", tone: "warning" },
  UNAVAILABLE: { label: "Not available", tone: "danger" },
  NO_RESPONSE: { label: "No response", tone: "neutral" },
};

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  const entry = MAP[status] ?? { label: status, tone: "neutral" as Tone };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
        TONE_CLASSES[entry.tone],
        className,
      )}
    >
      <span className="size-1.5 rounded-full bg-current" aria-hidden />
      {entry.label}
    </span>
  );
}