import { useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { FlaskConical } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState, TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { TestRecord } from "@/lib/types";
import { testingService } from "@/services/testing/testingService";

export const Route = createFileRoute("/app/test-history")({
  head: () => ({
    meta: [
      { title: "Test History — Blood Management System" },
      {
        name: "description",
        content: "Completed screening records with per-marker outcomes and technician attribution.",
      },
      { property: "og:title", content: "Test History — Blood Management System" },
      { property: "og:description", content: "Completed screening records with per-marker outcomes." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: TestHistoryPage,
});

function TestHistoryPage() {
  const [history, setHistory] = useState<TestRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await testingService.listHistory();
        setHistory(data);
      } catch (err) {
        toast.error(err instanceof Error ? err.message : "Failed to load test history.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <DashboardLayout title="Test History">
      <PageHeader
        title="Test history"
        description="Completed laboratory screenings with infectious disease marker panels and outcomes."
      />
      <SectionCard bodyClassName="p-0">
        {loading ? (
          <TableSkeleton cols={6} />
        ) : history.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={FlaskConical}
              title="No test history records"
              description="Completed laboratory infectious disease screenings will appear here."
            />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Unit ID</TableHead>
                <TableHead>Group</TableHead>
                <TableHead>Technician</TableHead>
                <TableHead>Tested Date</TableHead>
                <TableHead>Marker Results</TableHead>
                <TableHead>Final Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {history.map((t) => (
                <TableRow key={t.id}>
                  <TableCell className="font-mono text-xs font-semibold">{t.unitId}</TableCell>
                  <TableCell className="font-semibold text-primary">{t.group}</TableCell>
                  <TableCell>{t.technician ?? "—"}</TableCell>
                  <TableCell>{t.testedAt ? new Date(t.testedAt).toLocaleDateString() : "—"}</TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1.5">
                      {t.results
                        ? Object.entries(t.results).map(([marker, result]) => (
                            <span
                              key={marker}
                              className="rounded border border-border px-1.5 py-0.5 text-[11px] text-muted-foreground"
                            >
                              {marker}: {result === "PASS" ? "Non-reactive" : "Reactive"}
                            </span>
                          ))
                        : "—"}
                    </div>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={t.outcome} />
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
