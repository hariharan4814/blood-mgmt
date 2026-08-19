import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAsync } from "@/hooks/useAsync";
import { analyticsService } from "@/services/analytics/analyticsService";

export const Route = createFileRoute("/app/blood-banks")({
  head: () => ({
    meta: [
      { title: "Blood Banks — Blood Management System" },
      { name: "description", content: "Registered blood banks, licence details and current holdings across the network." },
      { property: "og:title", content: "Blood Banks — Blood Management System" },
      { property: "og:description", content: "Registered blood banks and their current holdings." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: BloodBanksPage,
});

function BloodBanksPage() {
  const { data, loading } = useAsync(() => analyticsService.listBloodBanks());
  return (
    <DashboardLayout title="Blood Banks">
      <PageHeader title="Blood banks" description="Facilities onboarded to the network and their licence status." />
      <SectionCard bodyClassName="p-0">
        {loading || !data ? (
          <TableSkeleton cols={5} />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>City</TableHead>
                <TableHead>Licence</TableHead>
                <TableHead>Units held</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((b) => (
                <TableRow key={b.id}>
                  <TableCell className="font-medium">{b.name}</TableCell>
                  <TableCell>{b.city}</TableCell>
                  <TableCell className="font-mono text-xs">{b.license}</TableCell>
                  <TableCell>{b.units}</TableCell>
                  <TableCell><StatusBadge status={b.status} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SectionCard>
    </DashboardLayout>
  );
}
