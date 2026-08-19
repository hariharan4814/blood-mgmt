import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAsync } from "@/hooks/useAsync";
import { donorService } from "@/services/donors/donorService";

export const Route = createFileRoute("/app/donation-history")({
  head: () => ({
    meta: [
      { title: "Donation History — Blood Management System" },
      { name: "description", content: "Every donation you have made, including deferred visits and collected volume." },
      { property: "og:title", content: "Donation History — Blood Management System" },
      { property: "og:description", content: "Your complete blood donation record." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: DonationHistoryPage,
});

function DonationHistoryPage() {
  const { data, loading } = useAsync(() => donorService.getDonationHistory());

  return (
    <DashboardLayout title="Donation History">
      <PageHeader title="Donation history" description="Your complete record of donations and deferrals." />
      <SectionCard bodyClassName="p-0">
        {loading || !data ? (
          <TableSkeleton cols={5} />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Reference</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Centre</TableHead>
                <TableHead>Volume</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((d) => (
                <TableRow key={d.id}>
                  <TableCell className="font-mono text-xs">{d.id}</TableCell>
                  <TableCell>{new Date(d.date).toLocaleDateString()}</TableCell>
                  <TableCell>{d.center}</TableCell>
                  <TableCell>{d.volumeMl ? `${d.volumeMl} ml` : "—"}</TableCell>
                  <TableCell><StatusBadge status={d.status === "COMPLETED" ? "COMPLETED" : "REVIEW"} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SectionCard>
    </DashboardLayout>
  );
}
