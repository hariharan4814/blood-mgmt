import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAsync } from "@/hooks/useAsync";
import { testingService } from "@/services/testing/testingService";

export const Route = createFileRoute("/app/test-history")({
  head: () => ({
    meta: [
      { title: "Test History — Blood Management System" },
      { name: "description", content: "Completed screening records with per-marker outcomes and technician attribution." },
      { property: "og:title", content: "Test History — Blood Management System" },
      { property: "og:description", content: "Completed screening records with per-marker outcomes." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: TestHistoryPage,
});

function TestHistoryPage() {
  const { data, loading } = useAsync(() => testingService.listHistory());

  return (
    <DashboardLayout title="Test History">
      <PageHeader title="Test history" description="Completed screenings with the full marker panel result." />
      <SectionCard bodyClassName="p-0">
        {loading || !data ? (
          <TableSkeleton cols={6} />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Unit</TableHead>
                <TableHead>Group</TableHead>
                <TableHead>Technician</TableHead>
                <TableHead>Tested</TableHead>
                <TableHead>Markers</TableHead>
                <TableHead>Outcome</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((t) => (
                <TableRow key={t.id}>
                  <TableCell className="font-mono text-xs">{t.unitId}</TableCell>
                  <TableCell className="font-semibold text-primary">{t.group}</TableCell>
                  <TableCell>{t.technician ?? "—"}</TableCell>
                  <TableCell>{t.testedAt ? new Date(t.testedAt).toLocaleDateString() : "—"}</TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1.5">
                      {Object.entries(t.results).map(([marker, result]) => (
                        <span
                          key={marker}
                          className="rounded border border-border px-1.5 py-0.5 text-[11px] text-muted-foreground"
                        >
                          {marker}: {result === "PASS" ? "NR" : "R"}
                        </span>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell><StatusBadge status={t.outcome} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SectionCard>
    </DashboardLayout>
  );
}
