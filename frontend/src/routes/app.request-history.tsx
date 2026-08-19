import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { useAsync } from "@/hooks/useAsync";
import { requestService } from "@/services/requests/requestService";

export const Route = createFileRoute("/app/request-history")({
  head: () => ({
    meta: [
      { title: "Request History — Blood Management System" },
      { name: "description", content: "Full audit trail of every blood request raised by your hospital, with status timeline." },
      { property: "og:title", content: "Request History — Blood Management System" },
      { property: "og:description", content: "Audit trail of hospital blood requests and their status timeline." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: RequestHistoryPage,
});

function RequestHistoryPage() {
  const { data, loading } = useAsync(() => requestService.list());

  return (
    <DashboardLayout title="Request History">
      <PageHeader title="Request history" description="Every request with its complete status timeline." />
      {loading || !data ? (
        <SectionCard bodyClassName="p-0"><TableSkeleton cols={4} /></SectionCard>
      ) : (
        <div className="space-y-4">
          {data.map((r) => (
            <SectionCard
              key={r.id}
              title={`${r.id} · ${r.group} × ${r.units} units`}
              description={`${r.hospital} · patient ${r.patientRef} · needed by ${new Date(r.neededBy).toLocaleDateString()}`}
              actions={<StatusBadge status={r.status} />}
            >
              <ol className="relative space-y-4 border-l border-border pl-5">
                {r.timeline.map((event, i) => (
                  <li key={`${r.id}-${i}`} className="relative">
                    <span className="absolute top-1.5 -left-[1.4rem] size-2.5 rounded-full bg-primary" aria-hidden />
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge status={event.status} />
                      <span className="text-xs text-muted-foreground">
                        {new Date(event.at).toLocaleString()} · {event.by}
                      </span>
                    </div>
                    {event.note ? <p className="mt-1 text-sm text-muted-foreground">{event.note}</p> : null}
                  </li>
                ))}
              </ol>
            </SectionCard>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
}
