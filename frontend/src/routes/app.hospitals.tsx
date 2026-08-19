import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAsync } from "@/hooks/useAsync";
import { analyticsService } from "@/services/analytics/analyticsService";

export const Route = createFileRoute("/app/hospitals")({
  head: () => ({
    meta: [
      { title: "Hospitals — Blood Management System" },
      { name: "description", content: "Partner hospitals, bed capacity and monthly blood request volume." },
      { property: "og:title", content: "Hospitals — Blood Management System" },
      { property: "og:description", content: "Partner hospitals and their request volume." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: HospitalsPage,
});

function HospitalsPage() {
  const { data, loading } = useAsync(() => analyticsService.listHospitals());
  return (
    <DashboardLayout title="Hospitals">
      <PageHeader title="Hospitals" description="Partner facilities raising blood requests on the platform." />
      <SectionCard bodyClassName="p-0">
        {loading || !data ? (
          <TableSkeleton cols={5} />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>City</TableHead>
                <TableHead>Beds</TableHead>
                <TableHead>Requests this month</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((h) => (
                <TableRow key={h.id}>
                  <TableCell className="font-medium">{h.name}</TableCell>
                  <TableCell>{h.city}</TableCell>
                  <TableCell>{h.beds}</TableCell>
                  <TableCell>{h.requestsThisMonth}</TableCell>
                  <TableCell><StatusBadge status={h.status} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SectionCard>
    </DashboardLayout>
  );
}
