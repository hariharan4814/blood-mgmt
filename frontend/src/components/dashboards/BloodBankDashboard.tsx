import { Link } from "@tanstack/react-router";
import { AlertTriangle, ClipboardList, Droplets, FlaskConical, Siren } from "lucide-react";
import { DonationTrendChart, StockByGroupChart } from "@/components/charts/Charts";
import { BloodGroupTile } from "@/components/common/BloodGroupTile";
import { SectionCard } from "@/components/common/SectionCard";
import { StatCard } from "@/components/common/StatCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { CardsSkeleton, TableSkeleton } from "@/components/common/StateBlocks";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAsync } from "@/hooks/useAsync";
import { analyticsService } from "@/services/analytics/analyticsService";
import { inventoryService } from "@/services/inventory/inventoryService";
import { requestService } from "@/services/requests/requestService";
import { testingService } from "@/services/testing/testingService";

export function BloodBankDashboard() {
  const stock = useAsync(() => inventoryService.getStock());
  const requests = useAsync(() => requestService.list());
  const pending = useAsync(() => testingService.listPending());
  const trends = useAsync(() => analyticsService.getDonationTrends());

  const totalUnits = stock.data?.reduce((sum, s) => sum + s.units, 0) ?? 0;
  const lowStock = stock.data?.filter((s) => s.units < s.threshold) ?? [];
  const pendingRequests = requests.data?.filter((r) => r.status === "PENDING") ?? [];

  return (
    <div className="space-y-6">
      {stock.loading || requests.loading ? (
        <CardsSkeleton />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Units in stock" value={totalUnits} icon={Droplets} hint="Available + reserved" />
          <StatCard label="Pending requests" value={pendingRequests.length} icon={ClipboardList} tone="warning" hint="Awaiting approval" />
          <StatCard label="Units in testing" value={pending.data?.length ?? 0} icon={FlaskConical} tone="info" hint="Screening in progress" />
          <StatCard label="Low stock groups" value={lowStock.length} icon={AlertTriangle} tone="danger" hint={lowStock.map((s) => s.group).join(", ") || "All groups healthy"} />
        </div>
      )}

      <SectionCard
        title="Stock by blood group"
        description="Units currently held at your facility"
        actions={
          <Button asChild size="sm" variant="outline">
            <Link to="/app/inventory">Open inventory</Link>
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

      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard title="Stock distribution" description="Comparative units per group">
          {stock.loading || !stock.data ? (
            <TableSkeleton rows={4} cols={3} />
          ) : (
            <StockByGroupChart data={stock.data.map((s) => ({ group: s.group, units: s.units }))} />
          )}
        </SectionCard>
        <SectionCard title="Collection vs demand" description="Last 6 months">
          {trends.loading || !trends.data ? <TableSkeleton rows={4} cols={3} /> : <DonationTrendChart data={trends.data} />}
        </SectionCard>
      </div>

      <SectionCard
        title="Incoming blood requests"
        description="Latest hospital requests routed to your bank"
        bodyClassName="p-0"
        actions={
          <div className="flex gap-2">
            <Button asChild size="sm" variant="outline">
              <Link to="/app/requests">All requests</Link>
            </Button>
            <Button asChild size="sm">
              <Link to="/app/sos">
                <Siren className="size-4" /> Emergency SOS
              </Link>
            </Button>
          </div>
        }
      >
        {requests.loading || !requests.data ? (
          <TableSkeleton cols={6} />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Request</TableHead>
                <TableHead>Hospital</TableHead>
                <TableHead>Group</TableHead>
                <TableHead>Units</TableHead>
                <TableHead>Urgency</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {requests.data.slice(0, 6).map((r) => (
                <TableRow key={r.id}>
                  <TableCell className="font-mono text-xs">{r.id}</TableCell>
                  <TableCell className="font-medium">{r.hospital}</TableCell>
                  <TableCell className="font-semibold text-primary">{r.group}</TableCell>
                  <TableCell>{r.units}</TableCell>
                  <TableCell><StatusBadge status={r.urgency} /></TableCell>
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
