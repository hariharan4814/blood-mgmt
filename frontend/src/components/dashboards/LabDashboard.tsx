import { Link } from "@tanstack/react-router";
import { CheckCircle2, FlaskConical, XCircle } from "lucide-react";
import { SectionCard } from "@/components/common/SectionCard";
import { StatCard } from "@/components/common/StatCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { CardsSkeleton, TableSkeleton } from "@/components/common/StateBlocks";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAsync } from "@/hooks/useAsync";
import { testingService } from "@/services/testing/testingService";

export function LabDashboard() {
  const pending = useAsync(() => testingService.listPending());
  const history = useAsync(() => testingService.listHistory());

  const passed = history.data?.filter((t) => t.outcome === "PASS") ?? [];
  const failed = history.data?.filter((t) => t.outcome === "FAIL") ?? [];

  return (
    <div className="space-y-6">
      {pending.loading || history.loading ? (
        <CardsSkeleton count={3} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-3">
          <StatCard label="Pending screenings" value={pending.data?.length ?? 0} icon={FlaskConical} tone="warning" hint="Units awaiting results" />
          <StatCard label="Cleared units" value={passed.length} icon={CheckCircle2} tone="success" hint="Released to inventory" />
          <StatCard label="Rejected units" value={failed.length} icon={XCircle} tone="danger" hint="Discarded after screening" />
        </div>
      )}

      <SectionCard
        title="Testing queue"
        description={`Screening panel: ${testingService.testTypes.join(", ")}`}
        bodyClassName="p-0"
        actions={
          <Button asChild size="sm">
            <Link to="/app/tests">Record results</Link>
          </Button>
        }
      >
        {pending.loading || !pending.data ? (
          <TableSkeleton cols={4} />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Unit</TableHead>
                <TableHead>Group</TableHead>
                <TableHead>Collected</TableHead>
                <TableHead>Outcome</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pending.data.map((t) => (
                <TableRow key={t.id}>
                  <TableCell className="font-mono text-xs">{t.unitId}</TableCell>
                  <TableCell className="font-semibold text-primary">{t.group}</TableCell>
                  <TableCell>{new Date(t.collectedAt).toLocaleDateString()}</TableCell>
                  <TableCell><StatusBadge status={t.outcome} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SectionCard>

      <SectionCard title="Recently completed tests" description="Your last recorded screenings" bodyClassName="p-0">
        {history.loading || !history.data ? (
          <TableSkeleton cols={5} />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Unit</TableHead>
                <TableHead>Group</TableHead>
                <TableHead>Technician</TableHead>
                <TableHead>Tested</TableHead>
                <TableHead>Outcome</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {history.data.slice(0, 6).map((t) => (
                <TableRow key={t.id}>
                  <TableCell className="font-mono text-xs">{t.unitId}</TableCell>
                  <TableCell className="font-semibold text-primary">{t.group}</TableCell>
                  <TableCell>{t.technician ?? "—"}</TableCell>
                  <TableCell>{t.testedAt ? new Date(t.testedAt).toLocaleDateString() : "—"}</TableCell>
                  <TableCell><StatusBadge status={t.outcome} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SectionCard>
    </div>
  );
}
