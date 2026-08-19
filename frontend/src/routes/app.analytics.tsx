import { createFileRoute } from "@tanstack/react-router";
import { ActivityChart, DonationTrendChart, SosResponseChart, StockByGroupChart } from "@/components/charts/Charts";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { useAsync } from "@/hooks/useAsync";
import { analyticsService } from "@/services/analytics/analyticsService";

export const Route = createFileRoute("/app/analytics")({
  head: () => ({
    meta: [
      { title: "Analytics — Blood Management System" },
      { name: "description", content: "Stock distribution, donation trends, SOS response rates and platform activity reports." },
      { property: "og:title", content: "Analytics — Blood Management System" },
      { property: "og:description", content: "Stock, donation and SOS response analytics." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: AnalyticsPage,
});

function AnalyticsPage() {
  const stock = useAsync(() => analyticsService.getStockByGroup());
  const trends = useAsync(() => analyticsService.getDonationTrends());
  const sos = useAsync(() => analyticsService.getSosResponseRate());
  const activity = useAsync(() => analyticsService.getSystemActivity());

  return (
    <DashboardLayout title="Analytics">
      <PageHeader
        title="Analytics & reports"
        description="Operational insight across inventory, demand and emergency response."
        actions={<Button variant="outline" disabled>Export PDF (coming with backend)</Button>}
      />
      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard title="Stock by blood group" description="Current units per group">
          {stock.loading || !stock.data ? <TableSkeleton rows={4} cols={3} /> : <StockByGroupChart data={stock.data.map((s) => ({ group: s.group, units: s.units }))} />}
        </SectionCard>
        <SectionCard title="Donations vs requests" description="Last 6 months">
          {trends.loading || !trends.data ? <TableSkeleton rows={4} cols={3} /> : <DonationTrendChart data={trends.data} />}
        </SectionCard>
        <SectionCard title="SOS response rate" description="Donors notified vs responded">
          {sos.loading || !sos.data ? <TableSkeleton rows={4} cols={3} /> : <SosResponseChart data={sos.data} />}
        </SectionCard>
        <SectionCard title="Platform activity" description="Logins and actions this week">
          {activity.loading || !activity.data ? <TableSkeleton rows={4} cols={3} /> : <ActivityChart data={activity.data} />}
        </SectionCard>
      </div>
    </DashboardLayout>
  );
}
