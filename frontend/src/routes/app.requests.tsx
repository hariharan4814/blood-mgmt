import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState, TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { useAsync } from "@/hooks/useAsync";
import { BLOOD_GROUPS, type BloodRequest } from "@/lib/types";
import { requestService } from "@/services/requests/requestService";
import { useAuth } from "@/providers/AuthProvider";

export const Route = createFileRoute("/app/requests")({
  head: () => ({
    meta: [
      { title: "Blood Requests — Blood Management System" },
      { name: "description", content: "Raise, review and approve hospital blood requests with urgency-based prioritisation." },
      { property: "og:title", content: "Blood Requests — Blood Management System" },
      { property: "og:description", content: "Raise, review and approve hospital blood requests." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: RequestsPage,
});

function RequestsPage() {
  const { user } = useAuth();
  const { data, loading } = useAsync(() => requestService.list());
  const [tab, setTab] = useState("ALL");
  const [rows, setRows] = useState<BloodRequest[] | null>(null);
  const [decision, setDecision] = useState<{ id: string; status: BloodRequest["status"] } | null>(null);
  const [createOpen, setCreateOpen] = useState(false);

  const list = rows ?? data ?? [];
  const filtered = useMemo(() => (tab === "ALL" ? list : list.filter((r) => r.status === tab)), [list, tab]);
  const isHospital = user?.role === "HOSPITAL_STAFF";

  const applyDecision = async () => {
    if (!decision) return;
    await requestService.updateStatus(decision.id, decision.status);
    setRows(list.map((r) => (r.id === decision.id ? { ...r, status: decision.status } : r)));
    toast.success(`Request ${decision.id} marked as ${decision.status.toLowerCase()}.`);
    setDecision(null);
  };

  return (
    <DashboardLayout title="Blood Requests">
      <PageHeader
        title={isHospital ? "My blood requests" : "Incoming blood requests"}
        description={
          isHospital
            ? "Raise new requests and follow their approval and dispatch status."
            : "Review hospital demand and approve or reject against available stock."
        }
        actions={
          isHospital ? (
            <Dialog open={createOpen} onOpenChange={setCreateOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="size-4" /> New request
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Raise a blood request</DialogTitle>
                  <DialogDescription>
                    The request is routed to blood banks in your city. Mock submission only.
                  </DialogDescription>
                </DialogHeader>
                <form
                  className="grid gap-4"
                  onSubmit={(e) => {
                    e.preventDefault();
                    setCreateOpen(false);
                    toast.success("Request submitted for blood bank approval.");
                  }}
                >
                  <div className="grid gap-2">
                    <Label htmlFor="patient">Patient reference</Label>
                    <Input id="patient" required placeholder="PT-2026-0142" />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="grid gap-2">
                      <Label htmlFor="group">Blood group</Label>
                      <Select defaultValue="O+">
                        <SelectTrigger id="group"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          {BLOOD_GROUPS.map((g) => (
                            <SelectItem key={g} value={g}>{g}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="units">Units</Label>
                      <Input id="units" type="number" min={1} defaultValue={2} required />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="grid gap-2">
                      <Label htmlFor="urgency">Urgency</Label>
                      <Select defaultValue="HIGH">
                        <SelectTrigger id="urgency"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="NORMAL">Normal</SelectItem>
                          <SelectItem value="HIGH">High</SelectItem>
                          <SelectItem value="CRITICAL">Critical</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="needed">Needed by</Label>
                      <Input id="needed" type="date" required />
                    </div>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="notes">Clinical notes</Label>
                    <Textarea id="notes" rows={3} placeholder="Scheduled surgery, cross-match required." />
                  </div>
                  <DialogFooter>
                    <Button type="submit">Submit request</Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          ) : undefined
        }
      />

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          {["ALL", "PENDING", "APPROVED", "DISPATCHED", "COMPLETED", "REJECTED"].map((t) => (
            <TabsTrigger key={t} value={t}>
              {t === "ALL" ? "All" : t.charAt(0) + t.slice(1).toLowerCase()}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <SectionCard bodyClassName="p-0">
        {loading ? (
          <TableSkeleton cols={7} />
        ) : filtered.length === 0 ? (
          <div className="p-5">
            <EmptyState title="No requests in this state" description="Requests will appear here as hospitals raise them." />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Request</TableHead>
                <TableHead>Hospital</TableHead>
                <TableHead>Patient</TableHead>
                <TableHead>Group</TableHead>
                <TableHead>Units</TableHead>
                <TableHead>Urgency</TableHead>
                <TableHead>Status</TableHead>
                {!isHospital ? <TableHead className="text-right">Action</TableHead> : null}
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((r) => (
                <TableRow key={r.id}>
                  <TableCell className="font-mono text-xs">{r.id}</TableCell>
                  <TableCell className="font-medium">{r.hospital}</TableCell>
                  <TableCell>{r.patientRef}</TableCell>
                  <TableCell className="font-semibold text-primary">{r.group}</TableCell>
                  <TableCell>{r.units}</TableCell>
                  <TableCell><StatusBadge status={r.urgency} /></TableCell>
                  <TableCell><StatusBadge status={r.status} /></TableCell>
                  {!isHospital ? (
                    <TableCell className="text-right">
                      {r.status === "PENDING" ? (
                        <div className="flex justify-end gap-2">
                          <Button size="sm" onClick={() => setDecision({ id: r.id, status: "APPROVED" })}>
                            Approve
                          </Button>
                          <Button size="sm" variant="outline" onClick={() => setDecision({ id: r.id, status: "REJECTED" })}>
                            Reject
                          </Button>
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">No action needed</span>
                      )}
                    </TableCell>
                  ) : null}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SectionCard>

      <ConfirmDialog
        open={decision !== null}
        onOpenChange={(open) => !open && setDecision(null)}
        title={decision?.status === "APPROVED" ? "Approve this request?" : "Reject this request?"}
        description={
          decision?.status === "APPROVED"
            ? "Matching units will be reserved from inventory and the hospital notified."
            : "The hospital will be notified with your rejection reason."
        }
        confirmLabel={decision?.status === "APPROVED" ? "Approve" : "Reject"}
        destructive={decision?.status === "REJECTED"}
        onConfirm={applyDecision}
      />
    </DashboardLayout>
  );
}
