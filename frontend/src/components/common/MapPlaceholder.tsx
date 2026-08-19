import { MapPin } from "lucide-react";

/**
 * Placeholder for the future Leaflet + OpenStreetMap donor-radius map.
 * Keep the same props when the real map lands so callers stay unchanged.
 */
export function MapPlaceholder({
  radiusKm,
  centerLabel,
  markerCount,
  height = "h-72",
}: {
  radiusKm?: number;
  centerLabel?: string;
  markerCount?: number;
  height?: string;
}) {
  return (
    <div
      className={`relative overflow-hidden rounded-lg border border-border bg-muted/40 ${height}`}
      role="img"
      aria-label="Map placeholder for donor radius"
    >
      <div
        className="absolute inset-0 opacity-[0.35]"
        style={{
          backgroundImage:
            "linear-gradient(var(--color-border) 1px, transparent 1px), linear-gradient(90deg, var(--color-border) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
        aria-hidden
      />
      <div className="absolute inset-0 grid place-items-center">
        <div className="relative grid place-items-center">
          <span className="absolute size-40 rounded-full border border-primary/30 bg-primary/5" aria-hidden />
          <span className="absolute size-24 rounded-full border border-primary/40 bg-primary/10" aria-hidden />
          <span className="relative grid size-10 place-items-center rounded-full bg-primary text-primary-foreground">
            <MapPin className="size-5" />
          </span>
        </div>
      </div>
      <div className="absolute bottom-3 left-3 rounded-md bg-card/90 px-3 py-2 text-xs text-muted-foreground shadow-[var(--shadow-card)]">
        <p className="font-medium text-foreground">{centerLabel ?? "Broadcast centre"}</p>
        <p>
          {radiusKm ? `${radiusKm} km radius` : "Radius not set"}
          {typeof markerCount === "number" ? ` · ${markerCount} donors in range` : ""}
        </p>
        <p className="mt-1 italic">Leaflet + OpenStreetMap integration pending</p>
      </div>
    </div>
  );
}