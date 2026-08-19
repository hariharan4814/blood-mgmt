import { cn } from "@/lib/utils";

/** Animated blood-drop loader (pure SVG, no emoji). */
export function Loader({
  label = "Loading",
  className,
  size = 44,
}: {
  label?: string;
  className?: string;
  size?: number;
}) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn("flex flex-col items-center gap-3 py-10", className)}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 48 48"
        fill="none"
        aria-hidden="true"
        className="animate-heartbeat"
      >
        <path
          d="M24 4C24 4 38 19.5 38 29a14 14 0 1 1-28 0C10 19.5 24 4 24 4Z"
          stroke="var(--primary)"
          strokeWidth="2.5"
          strokeLinejoin="round"
          strokeDasharray="180"
          style={{ animation: "drop-fill 1.6s ease-in-out infinite" }}
        />
        <path
          d="M15 30h5l2.5-5 3 9 2.5-4h5"
          stroke="var(--primary)"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity="0.85"
        />
      </svg>
      <span className="text-xs font-medium tracking-wide text-muted-foreground">{label}…</span>
    </div>
  );
}

/** Shimmering placeholder block for skeleton screens. */
export function ShimmerBlock({ className }: { className?: string }) {
  return <div className={cn("shimmer rounded-md", className)} aria-hidden="true" />;
}
