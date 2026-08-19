import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AlertTriangle, Droplets, PackageCheck, Search } from "lucide-react";
import { BloodGroupTile } from "@/components/common/BloodGroupTile";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatCard } from "@/components/common/StatCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { CardsSkeleton, EmptyState, TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAsync } from "@/hooks/useAsync";
import { BLOOD_GROUPS } from "@/lib/types";
import { inventoryService } from "@/services/inventory/inventoryService";

export const Route = createFileRoute("/app/inventory")({
  head: () => ({
    meta: [
      { title: "Blood Inventory — Blood Management System" },
      { name: "description", content: "Track blood units by group, status and expiry across the blood bank inventory." },
      { property: "og:title", content: "Blood Inventory — Blood Management System" },
      { property: "og:description", content: "Track blood units by group, status and expiry." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: InventoryPage,
});

function InventoryPage() {
  const stock = useAsync(() => inventoryService.getStock());
  const units = useAsync(() => inventoryService.listUnits());
  const [query, setQuery] = useState("");
  const [group, setGroup] = useState("ALL");
  const [status, setStatus] = useState("ALL");

  const filtered = useMemo(
    () =>
      (units.data ?? []).filter(
        (u) =>
          (group === "ALL" || u.group === group) &&
          (status === "ALL" || u.status === status) &&
          (u.id.toLowerCase().includes(query.toLowerCase()) ||
            u.donorName.toLowerCase().includes(query.toLowerCase())),
      ),
    [units.data, group, status, query],
  );

  const totalUnits = stock.data?.reduce((s, x) => s + x.units, 0) ?? 0;
  const lowStock = stock.data?.filter((s) => s.units < s.threshold) ?? [];
  const expiringSoon = (units.data ?? []).filter(
    (u) => new Date(u.expiresAt).getTime() - Date.now() < 1000 * 60 * 60 * 24 * 10,
  );

  return (
    <DashboardLayout title="Inventory">
      <PageHeader title="Blood inventory" description="Group-wise stock levels and individual unit traceability." />

      {stock.loading ? (
        <CardsSkeleton count={3} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-3">
          <StatCard label="Total units" value={totalUnits} icon={Droplets} />
          <StatCard label="Low stock groups" value={lowStock.length} icon={AlertTriangle} tone="danger" hint={lowStock.map((s) => s.group).join(", ") || "None"} />
          <StatCard label="Expiring in 10 days" value={expiringSoon.length} icon={PackageCheck} tone="warning" />
        </div>
      )}

      <SectionCard title="Group-wise stock" description="Threshold breaches are highlighted in red">
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

      <SectionCard
        title="Blood units"
        description="Every collected unit with its current lifecycle status"
        bodyClassName="p-0"
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="w-48 pl-9"
                placeholder="Unit ID or donor"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                aria-label="Search units"
              />
            </div>
            <Select value={group} onValueChange={setGroup}>
              <SelectTrigger className="w-28" aria-label="Filter by group">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All groups</SelectItem>
                {BLOOD_GROUPS.map((g) => (
                  <SelectItem key={g} value={g}>{g}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="w-36" aria-label="Filter by status">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {["ALL", "TESTING", "AVAILABLE", "RESERVED", "DISPATCHED", "DISCARDED"].map((s) => (
                  <SelectItem key={s} value={s}>{s === "ALL" ? "All statuses" : s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        }
      >
        {units.loading ? (
          <TableSkeleton cols={6} />
        ) : filtered.length === 0 ? (
          <div className="p-5">
            <EmptyState title="No units match these filters" description="Try clearing the search or selecting a different blood group." />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Unit ID</TableHead>
                <TableHead>Group</TableHead>
                <TableHead>Donor</TableHead>
                <TableHead>Collected</TableHead>
                <TableHead>Expires</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((u) => (
                <TableRow key={u.id}>
                  <TableCell className="font-mono text-xs">{u.id}</TableCell>
                  <TableCell className="font-semibold text-primary">{u.group}</TableCell>
                  <TableCell>{u.donorName}</TableCell>
                  <TableCell>{new Date(u.collectedAt).toLocaleDateString()}</TableCell>
                  <TableCell>{new Date(u.expiresAt).toLocaleDateString()}</TableCell>
                  <TableCell><StatusBadge status={u.status} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SectionCard>
    </DashboardLayout>
  );
}
