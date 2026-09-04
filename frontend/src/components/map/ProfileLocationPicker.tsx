import React, { useState } from "react";
import { Compass, ExternalLink, Loader2, LocateFixed, MapPin, Save } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LeafletMap } from "./LeafletMap";
import { Link } from "@tanstack/react-router";

interface ProfileLocationPickerProps {
  initialLatitude?: number | null | undefined;
  initialLongitude?: number | null | undefined;
  initialAddress?: string | null | undefined;
  onSave: (data: { latitude: number; longitude: number; address: string }) => Promise<void>;
  isSaving?: boolean | undefined;
}

const DEFAULT_LAT = 13.0827;
const DEFAULT_LNG = 80.2707;

export function ProfileLocationPicker({
  initialLatitude,
  initialLongitude,
  initialAddress = "",
  onSave,
  isSaving = false,
}: ProfileLocationPickerProps) {
  const [position, setPosition] = useState<[number, number]>(() => {
    if (typeof initialLatitude === "number" && typeof initialLongitude === "number") {
      return [initialLatitude, initialLongitude];
    }
    return [DEFAULT_LAT, DEFAULT_LNG];
  });

  const [hasLocation, setHasLocation] = useState<boolean>(() => {
    return typeof initialLatitude === "number" && typeof initialLongitude === "number";
  });

  const [address, setAddress] = useState<string>(initialAddress || "");
  const [geolocating, setGeolocating] = useState<boolean>(false);
  const [geoError, setGeoError] = useState<string | null>(null);

  const handlePositionChange = (pos: [number, number]) => {
    setPosition(pos);
    setHasLocation(true);
    setGeoError(null);
  };

  const handleUseCurrentLocation = () => {
    if (!navigator.geolocation) {
      setGeoError("Browser geolocation is not supported on this device. Please select your location on the map.");
      toast.error("Geolocation not supported by browser.");
      return;
    }

    setGeolocating(true);
    setGeoError(null);

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const coords: [number, number] = [pos.coords.latitude, pos.coords.longitude];
        setPosition(coords);
        setHasLocation(true);
        setGeolocating(false);
        toast.success("Detected your current location!");
      },
      (err) => {
        setGeolocating(false);
        let msg = "Could not obtain location. You can select your position manually by clicking on the map.";
        if (err.code === err.PERMISSION_DENIED) {
          msg = "Location permission was denied. You can select your location manually by clicking anywhere on the map.";
        } else if (err.code === err.POSITION_UNAVAILABLE) {
          msg = "Location information is unavailable. Please click on the map to set your location.";
        }
        setGeoError(msg);
        toast.info(msg);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000,
      }
    );
  };

  const handleSaveClick = async () => {
    if (!hasLocation) {
      toast.error("Please select a location on the map first.");
      return;
    }

    await onSave({
      latitude: Number(position[0].toFixed(6)),
      longitude: Number(position[1].toFixed(6)),
      address: address.trim(),
    });
  };

  return (
    <div className="space-y-4">
      {geoError && (
        <div className="rounded-lg border border-amber-200 bg-amber-50/70 p-3 text-xs text-amber-800 dark:border-amber-900/40 dark:bg-amber-950/30 dark:text-amber-300 flex items-start gap-2">
          <Compass className="size-4 shrink-0 mt-0.5 text-amber-600" />
          <span>{geoError}</span>
        </div>
      )}

      {/* Action bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleUseCurrentLocation}
            disabled={geolocating || isSaving}
            className="text-xs"
          >
            {geolocating ? (
              <Loader2 className="mr-1.5 size-3.5 animate-spin" />
            ) : (
              <LocateFixed className="mr-1.5 size-3.5 text-primary" />
            )}
            Use My Current Location
          </Button>

          <span className="text-xs text-muted-foreground hidden sm:inline">
            Click map or drag the pin to reposition
          </span>
        </div>

        {hasLocation && (
          <Link
            to="/app/map"
            search={{
              lat: position[0],
              lng: position[1],
            } as any}
            className="inline-flex items-center gap-1.5 text-xs text-primary font-medium hover:underline"
          >
            <span>View Nearby Resources</span>
            <ExternalLink className="size-3" />
          </Link>
        )}
      </div>

      {/* Map Component */}
      <LeafletMap
        center={position}
        selectedPosition={hasLocation ? position : null}
        onPositionChange={handlePositionChange}
        isPicker={true}
        height="h-[340px]"
      />

      {/* Coordinate & Address Input */}
      <div className="grid gap-3 sm:grid-cols-3 pt-1">
        <div>
          <Label htmlFor="lat-display" className="text-xs text-muted-foreground">
            Latitude
          </Label>
          <Input
            id="lat-display"
            readOnly
            value={hasLocation ? position[0].toFixed(6) : "Not set"}
            className="font-mono text-xs bg-muted/50"
          />
        </div>

        <div>
          <Label htmlFor="lng-display" className="text-xs text-muted-foreground">
            Longitude
          </Label>
          <Input
            id="lng-display"
            readOnly
            value={hasLocation ? position[1].toFixed(6) : "Not set"}
            className="font-mono text-xs bg-muted/50"
          />
        </div>

        <div>
          <Label htmlFor="address-input" className="text-xs">
            Location Label / Area
          </Label>
          <Input
            id="address-input"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="e.g. Anna Nagar, Chennai"
            className="text-xs"
            disabled={isSaving}
          />
        </div>
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-border">
        <p className="text-xs text-muted-foreground">
          {hasLocation
            ? "Your coordinates are saved to find nearby donors, hospitals, and blood banks."
            : "No location chosen yet. Tap the map to drop a pin."}
        </p>

        <Button
          type="button"
          onClick={handleSaveClick}
          disabled={!hasLocation || isSaving}
          size="sm"
        >
          {isSaving ? (
            <Loader2 className="mr-2 size-4 animate-spin" />
          ) : (
            <Save className="mr-2 size-4" />
          )}
          Save Location
        </Button>
      </div>
    </div>
  );
}
