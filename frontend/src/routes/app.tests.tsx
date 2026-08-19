import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { FlaskConical } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState, TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { useAsync } from "@/hooks/useAsync";
import type { TestRecord, TestResult } from "@/lib/types";
import { testingService } from "@/services/testing/testingService";

export const Route = createFileRoute("/app/tests")({
  head: () => ({
    meta: [
      { title: "Pending Tests — Blood Management System" },
      { name: "description", content: "Record HIV, hepatitis, syphilis and malaria screening outcomes for collected blood units." },
      { property: "og:title", content: "Pending Tests — Blood Management System" },
      { property: "og:description", content: "Record screening outcomes for collected blood units." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: PendingTestsPage,
});

const PANEL = testingService.testTypes;

function PendingTestsPage() {
  const { data, loading } = useAsync(() => testingService.listPending());
  const [queue, setQueue] = useState<TestRecord[] | null>(null);
  const [active, setActive] = useState<TestRecord | null>(null);
  const [results, setResults] = useState<Record<string, TestResult>>({});

  const list = queue ?? data ?? [];

  const openForm = (record: TestRecord) => {
    setActive(record);
    setResults(Object.fromEntries(PANEL.map((t) => [t, "PASS" as TestResult])));
  };

  const submit = async () => {
    if (!active) return;
    const outcome = await testingService.submitResult(active.unitId, results);
    setQueue(list.filter((t) => t.id !== active.id));
    toast.success(`Unit ${active.unitId} recorded as ${outcome.outcome === "PASS" ? "cleared" : "rejected"}.`);
    setActive(null);
  };

  return (
    <DashboardLayout title="Pending Tests">
      <PageHeader
        title="Testing & quality control"
        description={`Screening panel: ${PANEL.join(", ")}. A single failure discards the unit.`}
      />

      <SectionCard bodyClassName="p-0">
        {loading ? (
          <TableSkeleton cols={5} />
        ) : list.length === 0 ? (
          <div className="p-5">
            <EmptyState icon={FlaskConical} title="Queue is clear" description="All collected units have been screened." />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Unit</TableHead>
                <TableHead>Group</TableHead>
                <TableHead>Collected</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {list.map((t) => (
                <TableRow key={t.id}>
                  <TableCell className="font-mono text-xs">{t.unitId}</TableCell>
                  <TableCell className="font-semibold text-primary">{t.group}</TableCell>
                  <TableCell>{new Date(t.collectedAt).toLocaleDateString()}</TableCell>
                  <TableCell><StatusBadge status={t.outcome} /></TableCell>
                  <TableCell className="text-right">
                    <Button size="sm" onClick={() => openForm(t)}>Record result</Button>
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
                  onValueChange={(v) => setResults((prev) => ({ ...prev, [test]: v as TestResult }))}
                >
                  <div className="flex items-center gap-2">
                    <RadioGroupItem id={`${test}-pass`} value="PASS" />
                    <Label htmlFor={`${test}-pass`} className="text-xs font-normal">Non-reactive</Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <RadioGroupItem id={`${test}-fail`} value="FAIL" />
                    <Label htmlFor={`${test}-fail`} className="text-xs font-normal">Reactive</Label>
                  </div>
                </RadioGroup>
              </div>
            ))}
            <div className="grid gap-2">
              <Label htmlFor="test-notes">Technician notes</Label>
              <Textarea id="test-notes" rows={3} placeholder="Sample quality, repeat test remarks..." />
            </div>
          </div>
          <DialogFooter>
            <Button onClick={submit}>Save result</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
