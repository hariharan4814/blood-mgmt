import { Link } from "@tanstack/react-router";
import { CheckCircle2, ClipboardList, Clock, Droplets } from "lucide-react";
import { BloodGroupTile } from "@/components/common/BloodGroupTile";
import { SectionCard } from "@/components/common/SectionCard";
import { StatCard } from "@/components/common/StatCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { CardsSkeleton, TableSkeleton } from "@/components/common/StateBlocks";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAsync } from "@/hooks/useAsync";
import { inventoryService } from "@/services/inventory/inventoryService";
import { requestService } from "@/services/requests/requestService";

export function HospitalDashboard() {
  const requests = useAsync(() => requestService.list());
  const stock = useAsync(() => inventoryService.getStock());

  const pending = requests.data?.filter((r) => r.status === "PENDING") ?? [];
  const approved = requests.data?.filter((r) => r.status === "APPROVED" || r.status === "DISPATCHED") ?? [];
  const completed = requests.data?.filter((r) => r.status === "COMPLETED") ?? [];

  return (
    <div className="space-y-6">
      {requests.loading ? (
        <CardsSkeleton />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Open requests" value={pending.length} icon={ClipboardList} tone="warning" hint="Awaiting blood bank approval" />
          <StatCard label="In transit" value={approved.length} icon={Clock} tone="info" hint="Approved or dispatched" />
          <StatCard label="Fulfilled" value={completed.length} icon={CheckCircle2} tone="success" hint="This month" />
          <StatCard label="Units received" value={completed.reduce((s, r) => s + r.units, 0)} icon={Droplets} hint="Transfused or stored" />
        </div>
      )}

      <SectionCard
        title="Nearby blood bank availability"
        description="Live snapshot from the connected blood bank network"
        actions={
          <Button asChild size="sm">
            <Link to="/app/requests">Raise a request</Link>
          </Button>
        }
      >
        {stock.loading || !stock.data ? (
          <CardsSkeleton count={8} />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {stock.data.map((s) => (
              <BloodGroupTile
                key={s.group}
                group={s.group}
                units={s.units}
                level={s.units >= s.threshold * 2 ? "HIGH" : s.units >= s.threshold ? "MODERATE" : "LOW"}
              />
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard title="My recent requests" description="Track status and fulfilment" bodyClassName="p-0"
        actions={
          <Button asChild size="sm" variant="outline">
            <Link to="/app/request-history">Full history</Link>
          </Button>
        }
      >
        {requests.loading || !requests.data ? (
          <TableSkeleton cols={6} />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Request</TableHead>
                <TableHead>Patient ref</TableHead>
                <TableHead>Group</TableHead>
                <TableHead>Units</TableHead>
                <TableHead>Needed by</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {requests.data.slice(0, 6).map((r) => (
                <TableRow key={r.id}>
                  <TableCell className="font-mono text-xs">{r.id}</TableCell>
                  <TableCell>{r.patientRef}</TableCell>
                  <TableCell className="font-semibold text-primary">{r.group}</TableCell>
                  <TableCell>{r.units}</TableCell>
                  <TableCell>{new Date(r.neededBy).toLocaleDateString()}</TableCell>
                  <TableCell><StatusBadge status={r.status} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SectionCard>
    </div>
  );
}
