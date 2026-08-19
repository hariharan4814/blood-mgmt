import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Radio, Siren, UserCheck, Users } from "lucide-react";
import { toast } from "sonner";
import { SosResponseChart } from "@/components/charts/Charts";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { MapPlaceholder } from "@/components/common/MapPlaceholder";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatCard } from "@/components/common/StatCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAsync } from "@/hooks/useAsync";
import { BLOOD_GROUPS, type BloodGroup } from "@/lib/types";
import { analyticsService } from "@/services/analytics/analyticsService";
import { sosService } from "@/services/sos/sosService";

export const Route = createFileRoute("/app/sos")({
  head: () => ({
    meta: [
      { title: "Emergency SOS — Blood Management System" },
      { name: "description", content: "Broadcast critical blood requirements to eligible donors within a chosen radius and track responses." },
      { property: "og:title", content: "Emergency SOS — Blood Management System" },
      { property: "og:description", content: "Broadcast critical blood needs to nearby eligible donors." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: SosPage,
});

function SosPage() {
  const broadcasts = useAsync(() => sosService.listBroadcasts());
  const responseRate = useAsync(() => analyticsService.getSosResponseRate());
  const [group, setGroup] = useState<BloodGroup>("O-");
  const [units, setUnits] = useState(3);
  const [radius, setRadius] = useState(15);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const responses = useAsync(() => (selected ? sosService.listResponses(selected) : Promise.resolve([])), [selected]);

  const preview = useAsync(() => sosService.previewEligibleDonors(group, radius), [group, radius]);

  const trigger = async () => {
    const result = await sosService.trigger({ group, units, radiusKm: radius });
    toast.success(`SOS ${result.id} broadcast to donors within ${radius} km.`);
    setConfirmOpen(false);
  };

  const active = broadcasts.data?.filter((b) => b.status === "ACTIVE") ?? [];

  return (
    <DashboardLayout title="Emergency SOS">
      <PageHeader
        title="Emergency SOS"
        description="Broadcast a critical requirement to eligible donors in a geographic radius."
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Active broadcasts" value={active.length} icon={Siren} tone="danger" />
        <StatCard label="Donors notified" value={broadcasts.data?.reduce((s, b) => s + b.notified, 0) ?? 0} icon={Users} tone="info" />
        <StatCard label="Donors accepted" value={broadcasts.data?.reduce((s, b) => s + b.accepted, 0) ?? 0} icon={UserCheck} tone="success" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
        <SectionCard title="Trigger a broadcast" description="Donors matching the group and radius receive an instant alert">
          <div className="space-y-5">
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="sos-group">Blood group</Label>
                <Select value={group} onValueChange={(v) => setGroup(v as BloodGroup)}>
                  <SelectTrigger id="sos-group"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {BLOOD_GROUPS.map((g) => (
                      <SelectItem key={g} value={g}>{g}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="sos-units">Units required</Label>
                <Input
                  id="sos-units"
                  type="number"
                  min={1}
                  value={units}
                  onChange={(e) => setUnits(Number(e.target.value))}
                />
              </div>
            </div>

            <div className="grid gap-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="sos-radius">Search radius</Label>
                <span className="text-sm font-medium">{radius} km</span>
              </div>
              <Slider
                id="sos-radius"
                min={5}
                max={50}
                step={5}
                value={[radius]}
                onValueChange={([v]) => setRadius(v ?? radius)}
              />
              <p className="text-xs text-muted-foreground">
                {preview.data ? `${preview.data.eligibleDonors} eligible donors in range` : "Estimating donors in range..."}
              </p>
            </div>

            <Button className="w-full" onClick={() => setConfirmOpen(true)}>
              <Radio className="size-4" /> Broadcast SOS alert
            </Button>
          </div>
        </SectionCard>

        <SectionCard title="Donor radius map" description="Placeholder until the map layer is connected">
          <MapPlaceholder radiusKm={radius} centerLabel="Your blood bank" markerCount={preview.data?.eligibleDonors ?? 0} />
        </SectionCard>
      </div>

      <SectionCard title="Response rate" description="Notified vs responded donors per month">
        {responseRate.loading || !responseRate.data ? <TableSkeleton rows={4} cols={3} /> : <SosResponseChart data={responseRate.data} />}
      </SectionCard>

      <SectionCard title="Broadcast history" description="Select a broadcast to view individual donor responses" bodyClassName="p-0">
        {broadcasts.loading || !broadcasts.data ? (
          <TableSkeleton cols={7} />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Group</TableHead>
                <TableHead>Units</TableHead>
                <TableHead>Hospital</TableHead>
                <TableHead>Radius</TableHead>
                <TableHead>Notified / Accepted</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Responses</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {broadcasts.data.map((b) => (
                <TableRow key={b.id}>
                  <TableCell className="font-mono text-xs">{b.id}</TableCell>
                  <TableCell className="font-semibold text-primary">{b.group}</TableCell>
                  <TableCell>{b.units}</TableCell>
                  <TableCell>{b.hospital}</TableCell>
                  <TableCell>{b.radiusKm} km</TableCell>
                  <TableCell>{b.notified} / {b.accepted}</TableCell>
                  <TableCell><StatusBadge status={b.status} /></TableCell>
                  <TableCell className="text-right">
                    <Button size="sm" variant="outline" onClick={() => setSelected(b.id)}>View</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SectionCard>

      {selected ? (
        <SectionCard title={`Donor responses · ${selected}`} description="Contact accepted donors directly" bodyClassName="p-0">
          {responses.loading || !responses.data ? (
            <TableSkeleton cols={5} />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Donor</TableHead>
                  <TableHead>Group</TableHead>
                  <TableHead>Distance</TableHead>
                  <TableHead>Phone</TableHead>
                  <TableHead>Response</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {responses.data.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell className="font-medium">{r.donorName}</TableCell>
                    <TableCell className="font-semibold text-primary">{r.group}</TableCell>
                    <TableCell>{r.distanceKm} km</TableCell>
                    <TableCell className="font-mono text-xs">{r.phone}</TableCell>
                    <TableCell><StatusBadge status={r.answer} /></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </SectionCard>
      ) : null}

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="Broadcast emergency SOS?"
        description={`${preview.data?.eligibleDonors ?? 0} donors with ${group} blood within ${radius} km will be alerted immediately. Use only for genuine emergencies.`}
        confirmLabel="Broadcast now"
        destructive
        onConfirm={trigger}
      />
    </DashboardLayout>
  );
}
