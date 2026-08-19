import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Search } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState, TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAsync } from "@/hooks/useAsync";
import { ROLE_LABELS } from "@/lib/types";
import { analyticsService } from "@/services/analytics/analyticsService";

export const Route = createFileRoute("/app/users")({
  head: () => ({
    meta: [
      { title: "User Management — Blood Management System" },
      { name: "description", content: "Manage platform accounts and role assignments across blood banks, hospitals, labs and donors." },
      { property: "og:title", content: "User Management — Blood Management System" },
      { property: "og:description", content: "Manage accounts and role assignments." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: UsersPage,
});

function UsersPage() {
  const { data, loading } = useAsync(() => analyticsService.listUsers());
  const [query, setQuery] = useState("");
  const [role, setRole] = useState("ALL");

  const filtered = useMemo(
    () =>
      (data ?? []).filter(
        (u) =>
          (role === "ALL" || u.role === role) &&
          (u.name.toLowerCase().includes(query.toLowerCase()) || u.email.toLowerCase().includes(query.toLowerCase())),
      ),
    [data, role, query],
  );

  return (
    <DashboardLayout title="Users">
      <PageHeader title="User management" description="Accounts and their assigned roles across the platform." />
      <SectionCard
        bodyClassName="p-0"
        title="All accounts"
        description={`${filtered.length} account${filtered.length === 1 ? "" : "s"}`}
        actions={
          <div className="flex flex-wrap gap-2">
            <div className="relative">
              <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input className="w-48 pl-9" placeholder="Search users" value={query} onChange={(e) => setQuery(e.target.value)} aria-label="Search users" />
            </div>
            <Select value={role} onValueChange={setRole}>
              <SelectTrigger className="w-44" aria-label="Filter by role"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All roles</SelectItem>
                {Object.entries(ROLE_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        }
      >
        {loading ? (
          <TableSkeleton cols={5} />
        ) : filtered.length === 0 ? (
          <div className="p-5"><EmptyState title="No matching users" /></div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Organisation</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((u) => (
                <TableRow key={u.id}>
                  <TableCell className="font-medium">{u.name}</TableCell>
                  <TableCell>{u.email}</TableCell>
                  <TableCell>{ROLE_LABELS[u.role]}</TableCell>
                  <TableCell>{u.organization}</TableCell>
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
