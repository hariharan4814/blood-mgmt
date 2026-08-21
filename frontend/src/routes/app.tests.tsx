import { useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { FlaskConical, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState, TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import type { TestRecord, TestResult } from "@/lib/types";
import { testingService, TEST_TYPES } from "@/services/testing/testingService";

export const Route = createFileRoute("/app/tests")({
  head: () => ({
    meta: [
      { title: "Pending Tests — Blood Management System" },
      {
        name: "description",
        content: "Record HIV, hepatitis, syphilis and malaria screening outcomes for collected blood units.",
      },
      { property: "og:title", content: "Pending Tests — Blood Management System" },
      { property: "og:description", content: "Record screening outcomes for collected blood units." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: PendingTestsPage,
});

const PANEL = TEST_TYPES;

function PendingTestsPage() {
  const [queue, setQueue] = useState<TestRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [active, setActive] = useState<TestRecord | null>(null);
  const [results, setResults] = useState<Record<string, TestResult>>({});

  const loadQueue = async () => {
    setLoading(true);
    try {
      const data = await testingService.listPending();
      setQueue(data);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load pending test queue.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const openForm = (record: TestRecord) => {
    setActive(record);
    setResults(Object.fromEntries(PANEL.map((t) => [t, "PASS" as TestResult])));
  };

  const submit = async () => {
    if (!active) return;
    setSubmitting(true);
    try {
      const outcome = await testingService.submitResult(active.id, results);
      setQueue((prev) => prev.filter((t) => t.id !== active.id));
      toast.success(
        `Unit ${active.unitId} recorded as ${outcome.outcome === "PASS" ? "cleared (AVAILABLE)" : "rejected (DISCARDED)"}.`,
      );
      setActive(null);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to record screening test results.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <DashboardLayout title="Pending Tests">
      <PageHeader
        title="Testing & quality control"
        description={`Screening panel: ${PANEL.join(", ")}. A single reactive result discards the unit.`}
      />

      <SectionCard bodyClassName="p-0">
        {loading ? (
          <TableSkeleton cols={5} />
        ) : queue.length === 0 ? (
          <div className="p-5">
            <EmptyState
              icon={FlaskConical}
              title="Queue is clear"
              description="All collected blood units have completed laboratory disease screening."
            />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Unit ID</TableHead>
                <TableHead>Group</TableHead>
                <TableHead>Collected</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {queue.map((t) => (
                <TableRow key={t.id}>
                  <TableCell className="font-mono text-xs font-semibold">{t.unitId}</TableCell>
                  <TableCell className="font-semibold text-primary">{t.group}</TableCell>
                  <TableCell>{new Date(t.collectedAt).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <StatusBadge status={t.outcome} />
                  </TableCell>
                  <TableCell className="text-right">
                    <Button size="sm" onClick={() => openForm(t)}>
                      Record result
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SectionCard>

      <Dialog open={active !== null} onOpenChange={(open) => !open && setActive(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Screening result · {active?.unitId}</DialogTitle>
            <DialogDescription>
              Blood group {active?.group}. Mark each marker; any reactive result discards the unit.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {PANEL.map((test) => (
              <div key={test} className="flex flex-wrap items-center justify-between gap-3">
                <Label className="text-sm">{test}</Label>
                <RadioGroup
                  className="flex gap-4"
                  value={results[test] ?? "PASS"}
                  onValueChange={(v) =>
                    setResults((prev) => ({ ...prev, [test]: v as TestResult }))
                  }
                >
                  <div className="flex items-center gap-2">
                    <RadioGroupItem id={`${test}-pass`} value="PASS" />
                    <Label htmlFor={`${test}-pass`} className="text-xs font-normal">
                      Non-reactive
                    </Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <RadioGroupItem id={`${test}-fail`} value="FAIL" />
                    <Label htmlFor={`${test}-fail`} className="text-xs font-normal">
                      Reactive
                    </Label>
                  </div>
                </RadioGroup>
              </div>
            ))}
            <div className="grid gap-2">
              <Label htmlFor="test-notes">Technician notes</Label>
              <Textarea id="test-notes" rows={2} placeholder="Sample quality, repeat test remarks..." />
            </div>
          </div>
          <DialogFooter>
            <Button onClick={submit} disabled={submitting}>
              {submitting ? <Loader2 className="mr-2 size-4 animate-spin" /> : null}
              Save result
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
