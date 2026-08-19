import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAsync } from "@/hooks/useAsync";
import { analyticsService } from "@/services/analytics/analyticsService";

export const Route = createFileRoute("/app/audit-logs")({
  head: () => ({
    meta: [
      { title: "Audit Logs — Blood Management System" },
      { name: "description", content: "Immutable trail of privileged actions taken across the blood management platform." },
      { property: "og:title", content: "Audit Logs — Blood Management System" },
      { property: "og:description", content: "Trail of privileged actions across the platform." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: AuditLogsPage,
});

function AuditLogsPage() {
  const { data, loading } = useAsync(() => analyticsService.getAuditLogs());
  return (
    <DashboardLayout title="Audit Logs">
      <PageHeader title="Audit logs" description="Who did what, when and from where." />
      <SectionCard bodyClassName="p-0">
        {loading || !data ? (
          <TableSkeleton cols={5} />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Log</TableHead>
                <TableHead>Actor</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Target</TableHead>
                <TableHead>When</TableHead>
                <TableHead>IP</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((l) => (
                <TableRow key={l.id}>
                  <TableCell className="font-mono text-xs">{l.id}</TableCell>
                  <TableCell className="font-medium">{l.actor}</TableCell>
                  <TableCell>{l.action}</TableCell>
                  <TableCell className="font-mono text-xs">{l.target}</TableCell>
                  <TableCell>{new Date(l.at).toLocaleString()}</TableCell>
                  <TableCell className="font-mono text-xs">{l.ip}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SectionCard>
    </DashboardLayout>
  );
}
