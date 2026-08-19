/** Decorative ECG pulse line (SVG). */
export function PulseLine({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 480 40"
      fill="none"
      preserveAspectRatio="none"
      aria-hidden="true"
      className={className}
    >
      <path
        d="M0 20h120l14-14 12 28 14-24 16 20 12-10h60l14-12 12 24 14-20 16 16 12-8h144"
        stroke="var(--primary)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.55"
      />
    </svg>
  );
}
