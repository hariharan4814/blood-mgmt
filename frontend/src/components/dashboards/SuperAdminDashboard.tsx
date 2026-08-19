import { Building2, Hospital, Users, Droplets } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { ActivityChart, DonationTrendChart } from "@/components/charts/Charts";
import { SectionCard } from "@/components/common/SectionCard";
import { StatCard } from "@/components/common/StatCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { CardsSkeleton, TableSkeleton } from "@/components/common/StateBlocks";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAsync } from "@/hooks/useAsync";
import { analyticsService } from "@/services/analytics/analyticsService";

export function SuperAdminDashboard() {
  const totals = useAsync(() => analyticsService.getPlatformTotals());
  const trends = useAsync(() => analyticsService.getDonationTrends());
  const activity = useAsync(() => analyticsService.getSystemActivity());
  const banks = useAsync(() => analyticsService.listBloodBanks());

  return (
    <div className="space-y-6">
      {totals.loading || !totals.data ? (
        <CardsSkeleton />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Registered users" value={totals.data.users.toLocaleString()} icon={Users} hint="Across all roles" />
          <StatCard label="Blood banks" value={totals.data.bloodBanks} icon={Building2} tone="info" hint="1 pending review" />
          <StatCard label="Hospitals" value={totals.data.hospitals} icon={Hospital} tone="success" hint="All verified" />
          <StatCard label="Total donations" value={totals.data.donations.toLocaleString()} icon={Droplets} tone="danger" hint="Lifetime collected units" />
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard title="Donations vs requests" description="Platform-wide, last 6 months">
          {trends.loading || !trends.data ? <TableSkeleton rows={4} cols={3} /> : <DonationTrendChart data={trends.data} />}
        </SectionCard>
        <SectionCard title="System activity" description="Logins and recorded actions this week">
          {activity.loading || !activity.data ? <TableSkeleton rows={4} cols={3} /> : <ActivityChart data={activity.data} />}
        </SectionCard>
      </div>

      <SectionCard
        title="Blood banks"
        description="Onboarded facilities and their current holdings"
        bodyClassName="p-0"
        actions={
          <Button asChild variant="outline" size="sm">
            <Link to="/app/blood-banks">Manage</Link>
          </Button>
        }
      >
        {banks.loading || !banks.data ? (
          <TableSkeleton cols={5} />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>City</TableHead>
                <TableHead>License</TableHead>
                <TableHead>Units</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {banks.data.map((bank) => (
                <TableRow key={bank.id}>
                  <TableCell className="font-medium">{bank.name}</TableCell>
                  <TableCell>{bank.city}</TableCell>
                  <TableCell className="font-mono text-xs">{bank.license}</TableCell>
                  <TableCell>{bank.units}</TableCell>
                  <TableCell>
                    <StatusBadge status={bank.status} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SectionCard>
    </div>
  );
}