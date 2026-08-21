import { useEffect, useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AlertTriangle, Droplets, PackageCheck, Search } from "lucide-react";
import { toast } from "sonner";
import { BloodGroupTile } from "@/components/common/BloodGroupTile";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatCard } from "@/components/common/StatCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { CardsSkeleton, EmptyState, TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { BLOOD_GROUPS } from "@/lib/types";
import {
  inventoryService,
  type BloodStock,
  type BloodUnitItem,
} from "@/services/inventory/inventoryService";

export const Route = createFileRoute("/app/inventory")({
  head: () => ({
    meta: [
      { title: "Blood Inventory — Blood Management System" },
      {
        name: "description",
        content: "Track blood units by group, status and expiry across the blood bank inventory.",
      },
      { property: "og:title", content: "Blood Inventory — Blood Management System" },
      { property: "og:description", content: "Track blood units by group, status and expiry." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: InventoryPage,
});

function InventoryPage() {
  const [stock, setStock] = useState<BloodStock[]>([]);
  const [units, setUnits] = useState<BloodUnitItem[]>([]);
  const [loadingStock, setLoadingStock] = useState(true);
  const [loadingUnits, setLoadingUnits] = useState(true);

  const [query, setQuery] = useState("");
  const [group, setGroup] = useState("ALL");
  const [status, setStatus] = useState("ALL");

  const loadData = async () => {
    setLoadingStock(true);
    setLoadingUnits(true);
    try {
      const [stockData, unitData] = await Promise.all([
        inventoryService.getStock(),
        inventoryService.listUnits(),
      ]);
      setStock(stockData);
      setUnits(unitData);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load inventory data.");
    } finally {
      setLoadingStock(false);
      setLoadingUnits(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filtered = useMemo(
    () =>
      units.filter(
        (u) =>
          (group === "ALL" || u.group === group) &&
          (status === "ALL" || u.status === status) &&
          (u.id.toLowerCase().includes(query.toLowerCase()) ||
            u.bank.toLowerCase().includes(query.toLowerCase()) ||
            u.donorName.toLowerCase().includes(query.toLowerCase())),
      ),
    [units, group, status, query],
  );

  const totalUnits = stock.reduce((s, x) => s + x.units, 0);
  const lowStock = stock.filter((s) => s.units < s.threshold);
  const expiringSoon = units.filter(
    (u) =>
      u.status === "AVAILABLE" &&
      new Date(u.expiresAt).getTime() - Date.now() < 1000 * 60 * 60 * 24 * 10 &&
      new Date(u.expiresAt).getTime() > Date.now(),
  );

  return (
    <DashboardLayout title="Inventory">
      <PageHeader
        title="Blood inventory"
        description="Group-wise stock levels, safety thresholds, and individual unit traceability."
      />

      {loadingStock ? (
        <CardsSkeleton count={3} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-3">
          <StatCard label="Total available units" value={totalUnits} icon={Droplets} />
          <StatCard
            label="Low stock groups"
            value={lowStock.length}
            icon={AlertTriangle}
            {...(lowStock.length > 0 ? { tone: "danger" as const } : {})}
            hint={lowStock.map((s) => s.group).join(", ") || "All groups adequate"}
          />
          <StatCard
            label="Expiring in 10 days"
            value={expiringSoon.length}
            icon={PackageCheck}
            {...(expiringSoon.length > 0 ? { tone: "warning" as const } : {})}
          />
        </div>
      )}

      <SectionCard
        title="Group-wise stock"
        description="Live available inventory count per blood group across blood bank facilities"
      >
        {loadingStock ? (
          <CardsSkeleton count={8} />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {stock.map((s) => (
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
        description="Traceability record of every collected unit with lifecycle status"
        bodyClassName="p-0"
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="w-48 pl-9"
                placeholder="Unit ID or facility"
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
                  <SelectItem key={g} value={g}>
                    {g}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="w-36" aria-label="Filter by status">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {["ALL", "TESTING", "AVAILABLE", "RESERVED", "DISPATCHED", "DISCARDED"].map((s) => (
                  <SelectItem key={s} value={s}>
                    {s === "ALL" ? "All statuses" : s}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        }
      >
        {loadingUnits ? (
          <TableSkeleton cols={6} />
        ) : filtered.length === 0 ? (
          <div className="p-5">
            <EmptyState
              title="No units match these filters"
              description="Try clearing the search query or selecting a different blood group / status."
            />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Unit ID</TableHead>
                <TableHead>Group</TableHead>
                <TableHead>Facility</TableHead>
                <TableHead>Collected</TableHead>
                <TableHead>Expires</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((u) => (
                <TableRow key={u.id}>
                  <TableCell className="font-mono text-xs">{u.id}</TableCell>
                  <TableCell className="font-bold text-primary">{u.group}</TableCell>
                  <TableCell className="font-medium">{u.bank}</TableCell>
                  <TableCell>{u.collectedAt ? new Date(u.collectedAt).toLocaleDateString() : "-"}</TableCell>
                  <TableCell>
                    {u.expiresAt ? (
                      <span className={u.isExpired ? "text-destructive font-semibold" : ""}>
                        {new Date(u.expiresAt).toLocaleDateString()}
                        {u.isExpired ? " (Expired)" : ""}
                      </span>
                    ) : (
                      "-"
                    )}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={u.status} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SectionCard>
    </DashboardLayout>
  );
}
