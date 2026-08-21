import { useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AlertCircle, Loader2, Radio, Siren, Users } from "lucide-react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { MapPlaceholder } from "@/components/common/MapPlaceholder";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatCard } from "@/components/common/StatCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState, TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import type { SosBroadcast } from "@/lib/types";
import {
  sosService,
  type CriticalRequestOption,
  type SosRecipientItem,
} from "@/services/sos/sosService";

export const Route = createFileRoute("/app/sos")({
  head: () => ({
    meta: [
      { title: "Emergency SOS — Blood Management System" },
      {
        name: "description",
        content:
          "Broadcast critical blood requirements to eligible donors within a chosen radius and track responses.",
      },
      { property: "og:title", content: "Emergency SOS — Blood Management System" },
      { property: "og:description", content: "Broadcast critical blood needs to nearby eligible donors." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: SosPage,
});

function SosPage() {
  const [broadcasts, setBroadcasts] = useState<SosBroadcast[]>([]);
  const [criticalRequests, setCriticalRequests] = useState<CriticalRequestOption[]>([]);
  const [selectedRequestId, setSelectedRequestId] = useState<string>("");
  const [radius, setRadius] = useState(25);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [selectedBroadcast, setSelectedBroadcast] = useState<string | null>(null);
  const [recipients, setRecipients] = useState<SosRecipientItem[]>([]);
  const [loadingRecipients, setLoadingRecipients] = useState(false);

  const [cancelId, setCancelId] = useState<string | null>(null);
  const [cancelReason, setCancelReason] = useState("");

  const loadData = async () => {
    setLoading(true);
    try {
      const [broadcastList, requests] = await Promise.all([
        sosService.listBroadcasts(),
        sosService.listCriticalRequests(),
      ]);
      setBroadcasts(broadcastList);
      setCriticalRequests(requests);
      if (requests.length > 0) {
        const firstReq = requests[0];
        if (firstReq) {
          setSelectedRequestId(String(firstReq.id));
        }
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load SOS data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSelectBroadcast = async (broadcastId: string) => {
    setSelectedBroadcast(broadcastId);
    setLoadingRecipients(true);
    try {
      const list = await sosService.listResponses(broadcastId);
      setRecipients(list);
    } catch {
      toast.error("Failed to load recipients for this broadcast.");
    } finally {
      setLoadingRecipients(false);
    }
  };

  const trigger = async () => {
    if (!selectedRequestId) {
      toast.error("Please select an eligible critical blood request.");
      return;
    }

    setSubmitting(true);
    try {
      const result = await sosService.triggerForRequest(parseInt(selectedRequestId, 10), radius);
      toast.success(
        `SOS broadcast ${result.id} triggered. ${result.notified} compatible donors notified within ${radius} km.`,
      );
      setConfirmOpen(false);
      await loadData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to trigger SOS broadcast.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancelBroadcast = async () => {
    if (!cancelId || !cancelReason.trim()) {
      toast.error("Please specify a reason for cancellation.");
      return;
    }

    setSubmitting(true);
    try {
      await sosService.cancelBroadcast(cancelId, cancelReason.trim());
      toast.success(`SOS broadcast ${cancelId} has been cancelled.`);
      setCancelId(null);
      setCancelReason("");
      await loadData();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to cancel broadcast.");
    } finally {
      setSubmitting(false);
    }
  };

  const active = broadcasts.filter((b) => b.status === "ACTIVE");
  const totalNotified = broadcasts.reduce((s, b) => s + b.notified, 0);

  const selectedRequestObj = criticalRequests.find((r) => String(r.id) === selectedRequestId);

  return (
    <DashboardLayout title="Emergency SOS">
      <PageHeader
        title="Emergency SOS"
        description="Broadcast emergency blood requirements to compatible, eligible donors within a geographic radius."
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label="Active broadcasts"
          value={active.length}
          icon={Siren}
          {...(active.length > 0 ? { tone: "danger" as const } : {})}
        />
        <StatCard label="Donors notified" value={totalNotified} icon={Users} tone="info" />
        <StatCard label="Critical requests" value={criticalRequests.length} icon={AlertCircle} tone="warning" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
        <SectionCard
          title="Trigger a broadcast"
          description="Eligible donors matching compatibility rules within radius receive emergency alerts"
        >
          <div className="space-y-5">
            {criticalRequests.length === 0 ? (
              <div className="rounded-md border border-border bg-muted/40 p-4 text-sm text-muted-foreground">
                <p className="font-semibold text-foreground">No pending CRITICAL blood requests.</p>
                <p className="mt-1 text-xs">
                  Emergency broadcasts require an active CRITICAL blood request with an inventory shortage.
                </p>
              </div>
            ) : (
              <div className="grid gap-2">
                <Label htmlFor="critical-request">Target Critical Request</Label>
                <Select value={selectedRequestId} onValueChange={setSelectedRequestId}>
                  <SelectTrigger id="critical-request">
                    <SelectValue placeholder="Select critical request" />
                  </SelectTrigger>
                  <SelectContent>
                    {criticalRequests.map((req) => (
                      <SelectItem key={req.id} value={String(req.id)}>
                        Request #{req.id} · {req.blood_group} ({req.units_needed} units) · {req.hospital_staff_username}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

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
                Targeting donors within {radius} km of the facility coordinates.
              </p>
            </div>

            <Button
              className="w-full"
              disabled={criticalRequests.length === 0 || submitting}
              onClick={() => setConfirmOpen(true)}
            >
              {submitting ? (
                <Loader2 className="mr-2 size-4 animate-spin" />
              ) : (
                <Radio className="size-4" />
              )}
              Broadcast SOS alert
            </Button>
          </div>
        </SectionCard>

        <SectionCard title="Donor radius map" description="Geographic radius filter representation">
          <MapPlaceholder
            radiusKm={radius}
            centerLabel="Blood Bank Facility"
            markerCount={selectedRequestObj ? selectedRequestObj.units_needed : 0}
          />
        </SectionCard>
      </div>

      <SectionCard
        title="Broadcast history"
        description="Emergency broadcasts and targeted donor notification audit logs"
        bodyClassName="p-0"
      >
        {loading ? (
          <TableSkeleton cols={7} />
        ) : broadcasts.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={Siren}
              title="No emergency broadcasts triggered"
              description="Active and past SOS broadcast notifications will appear here."
            />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Broadcast</TableHead>
                <TableHead>Group</TableHead>
                <TableHead>Units</TableHead>
                <TableHead>Hospital / Bank</TableHead>
                <TableHead>Radius</TableHead>
                <TableHead>Donors Targeted</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {broadcasts.map((b) => (
                <TableRow key={b.id}>
                  <TableCell className="font-mono text-xs font-semibold">{b.id}</TableCell>
                  <TableCell className="font-bold text-primary">{b.group}</TableCell>
                  <TableCell>{b.units}</TableCell>
                  <TableCell>{b.hospital}</TableCell>
                  <TableCell>{b.radiusKm} km</TableCell>
                  <TableCell>{b.notified}</TableCell>
                  <TableCell>
                    <StatusBadge status={b.status} />
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleSelectBroadcast(b.id)}
                      >
                        Recipients
                      </Button>
                      {b.status === "ACTIVE" ? (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-destructive hover:bg-destructive/10"
                          onClick={() => setCancelId(b.id)}
                        >
                          Cancel
                        </Button>
                      ) : null}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SectionCard>

      {selectedBroadcast ? (
        <SectionCard
          title={`Targeted Donor Recipients · ${selectedBroadcast}`}
          description="Donors alerted with blood shortage notifications"
          bodyClassName="p-0"
        >
          {loadingRecipients ? (
            <TableSkeleton cols={4} />
          ) : recipients.length === 0 ? (
            <div className="p-6">
              <EmptyState
                icon={Users}
                title="No donor recipient records found"
                description="No donors were in range or compatible for this broadcast."
              />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Donor</TableHead>
                  <TableHead>Group</TableHead>
                  <TableHead>Distance</TableHead>
                  <TableHead>Channel</TableHead>
                  <TableHead>Delivery</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recipients.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell className="font-medium">{r.donorName}</TableCell>
                    <TableCell className="font-bold text-primary">{r.group}</TableCell>
                    <TableCell>{r.distanceKm} km</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{r.phone}</TableCell>
                    <TableCell>
                      <StatusBadge status={r.answer === "DELIVERED" ? "ACTIVE" : "PENDING"} />
                    </TableCell>
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
        description={`Emergency SOS will be sent to all compatible, eligible donors within ${radius} km. Notifications will be dispatched immediately.`}
        confirmLabel="Broadcast now"
        destructive
        onConfirm={trigger}
      />

      <ConfirmDialog
        open={cancelId !== null}
        onOpenChange={(open) => {
          if (!open) {
            setCancelId(null);
            setCancelReason("");
          }
        }}
        title="Cancel active SOS broadcast?"
        description="Cancelling will mark this emergency broadcast as cancelled."
        confirmLabel="Confirm Cancellation"
        destructive
        onConfirm={handleCancelBroadcast}
      >
        <div className="mt-3 space-y-2 text-left">
          <Label htmlFor="cancel-reason">Cancellation reason *</Label>
          <Textarea
            id="cancel-reason"
            rows={2}
            placeholder="e.g. Blood units secured from regional blood bank."
            value={cancelReason}
            onChange={(e) => setCancelReason(e.target.value)}
            required
          />
        </div>
      </ConfirmDialog>
    </DashboardLayout>
  );
}
