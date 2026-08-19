import { cn } from "@/lib/utils";
import type { BloodGroup } from "@/lib/types";

export function BloodGroupTile({
  group,
  units,
  level,
  className,
}: {
  group: BloodGroup;
  units: number;
  level: "HIGH" | "MODERATE" | "LOW";
  className?: string;
}) {
  const levelStyles = {
    HIGH: "border-success/30 bg-success/8 text-success",
    MODERATE: "border-warning/40 bg-warning/10 text-warning-foreground",
    LOW: "border-destructive/30 bg-destructive/8 text-destructive",
  }[level];
  const levelLabel = { HIGH: "Sufficient", MODERATE: "Moderate", LOW: "Low stock" }[level];

  return (
    <div className={cn("card-surface flex flex-col gap-2 p-4", className)}>
      <div className="flex items-center justify-between">
        <span className="text-2xl font-bold tracking-tight text-primary">{group}</span>
        <span className={cn("rounded-full border px-2 py-0.5 text-[11px] font-medium", levelStyles)}>
          {levelLabel}
        </span>
      </div>
      <p className="text-sm text-muted-foreground">
        <span className="text-base font-semibold text-foreground">{units}</span> units
      </p>
    </div>
  );
}