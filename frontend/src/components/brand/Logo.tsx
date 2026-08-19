import { Droplet } from "lucide-react";

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <span className="flex items-center gap-2.5">
      <span
        className="grid size-9 shrink-0 place-items-center rounded-lg text-primary-foreground"
        style={{ background: "var(--gradient-primary)" }}
      >
        <Droplet className="size-5" />
      </span>
      {!compact ? (
        <span className="leading-tight">
          <span className="block text-sm font-semibold tracking-tight">Blood Management</span>
          <span className="block text-[11px] tracking-wide text-muted-foreground uppercase">
            System
          </span>
        </span>
      ) : null}
    </span>
  );
}