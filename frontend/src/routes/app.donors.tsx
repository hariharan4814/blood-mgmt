import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Search, Users } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState, TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAsync } from "@/hooks/useAsync";
import { donorService } from "@/services/donors/donorService";

export const Route = createFileRoute("/app/donors")({
  head: () => ({
    meta: [
      { title: "Donor Directory — Blood Management System" },
      {
        name: "description",
        content: "Search registered donors, review contact details and eligibility for upcoming drives.",
      },
      { property: "og:title", content: "Donor Directory — Blood Management System" },
      { property: "og:description", content: "Search registered donors and review eligibility." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: DonorsPage,
});

function DonorsPage() {
  const { data, loading, error } = useAsync(() => donorService.listDonors());
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const list = data ?? [];
    return list.filter((d) => {
      const donorName = (d.name || "").toLowerCase();
      const donorEmail = (d.email || "").toLowerCase();
      const q = query.toLowerCase();
      return !q || donorName.includes(q) || donorEmail.includes(q);
    });
  }, [data, query]);

  return (
    <DashboardLayout title="Donors">
      <PageHeader title="Donor directory" description="Registered donors linked to your blood bank network." />
      <SectionCard
        bodyClassName="p-0"
        actions={
          <div className="relative">
            <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="w-56 pl-9"
              placeholder="Search donors"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Search donors"
            />
          </div>
        }
        title="All donors"
        description={`${filtered.length} donor${filtered.length === 1 ? "" : "s"} listed`}
      >
        {loading ? (
          <TableSkeleton cols={5} />
        ) : error ? (
          <div className="p-5">
            <EmptyState
              icon={Users}
              title="Access restricted or unavailable"
              description={error.message || "Donor directory is available to Blood Bank Administrators."}
            />
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-5">
            <EmptyState
              icon={Users}
              title="No donors found"
              description="Try a different search query or invite donors to register."
            />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Donor</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Organisation / Group</TableHead>
                <TableHead>Joined</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((d) => (
                <TableRow key={d.id}>
                  <TableCell className="font-medium">{d.name || "Registered Donor"}</TableCell>
                  <TableCell>{d.email || "—"}</TableCell>
                  <TableCell>{d.organization || "—"}</TableCell>
                  <TableCell>
                    {d.joinedAt ? new Date(d.joinedAt).toLocaleDateString() : "—"}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={d.status || "ACTIVE"} />
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
