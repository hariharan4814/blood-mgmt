import logoImg from "@/assets/logo.png";

export function Logo({
  compact = false,
  className = "",
}: {
  compact?: boolean;
  className?: string;
}) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <span className="relative flex size-9 shrink-0 items-center justify-center rounded-lg bg-card p-1 shadow-sm ring-1 ring-border/50 transition-transform hover:scale-105">
        <img
          src={logoImg}
          alt="Blood Management System Logo"
          className="size-full object-contain drop-shadow-sm"
        />
      </span>
      {!compact ? (
        <span className="leading-tight select-none">
          <span className="block text-sm font-bold tracking-tight text-foreground">
            Blood Management
          </span>
          <span className="block text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
            System
          </span>
        </span>
      ) : null}
    </span>
  );
}