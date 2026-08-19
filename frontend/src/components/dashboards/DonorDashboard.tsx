import { Link } from "@tanstack/react-router";
import { CalendarCheck, Droplets, HeartPulse, ShieldCheck } from "lucide-react";
import { SectionCard } from "@/components/common/SectionCard";
import { StatCard } from "@/components/common/StatCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { CardsSkeleton, TableSkeleton } from "@/components/common/StateBlocks";
import { DonorSosAlert } from "@/components/sos/DonorSosAlert";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useAsync } from "@/hooks/useAsync";
import { campService } from "@/services/camps/campService";
import { donorService } from "@/services/donors/donorService";
import { sosService } from "@/services/sos/sosService";

export function DonorDashboard() {
  const profile = useAsync(() => donorService.getProfile());
  const eligibility = useAsync(() => donorService.checkEligibility());
  const history = useAsync(() => donorService.getDonationHistory());
  const camps = useAsync(() => campService.list());
  const sos = useAsync(() => sosService.listBroadcasts());

  const activeSos = sos.data?.find((b) => b.status === "ACTIVE");
  const upcoming = camps.data?.filter((c) => c.status !== "COMPLETED") ?? [];

  return (
    <div className="space-y-6">
      {activeSos ? <DonorSosAlert broadcast={activeSos} /> : null}

      {profile.loading || !profile.data ? (
        <CardsSkeleton />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Blood group" value={profile.data.group} icon={Droplets} hint="Verified on last donation" />
          <StatCard label="Lifetime donations" value={profile.data.totalDonations} icon={HeartPulse} tone="success" hint={`Approx. ${profile.data.totalDonations * 3} lives supported`} />
          <StatCard
            label="Eligibility"
            value={profile.data.eligible ? "Eligible" : "On hold"}
            icon={ShieldCheck}
            tone={profile.data.eligible ? "success" : "warning"}
            hint={`Next eligible ${new Date(profile.data.nextEligible).toLocaleDateString()}`}
          />
          <StatCard label="Upcoming camps" value={upcoming.length} icon={CalendarCheck} tone="info" hint="Near your city" />
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard
          title="Eligibility checklist"
          description="Self-declared criteria reviewed before every donation"
          actions={
            <Button asChild size="sm" variant="outline">
              <Link to="/app/profile">Update profile</Link>
            </Button>
          }
        >
          {eligibility.loading || !eligibility.data ? (
            <TableSkeleton rows={4} cols={2} />
          ) : (
            <ul className="space-y-3">
              {eligibility.data.reasons.map((r) => (
                <li key={r.label} className="flex items-center justify-between gap-3 text-sm">
                  <span>{r.label}</span>
                  <StatusBadge status={r.passed ? "PASS" : "FAIL"} />
                </li>
              ))}
            </ul>
          )}
        </SectionCard>

        <SectionCard title="Donation history" description="Your recorded donations" bodyClassName="p-5">
          {history.loading || !history.data ? (
            <TableSkeleton rows={4} cols={3} />
          ) : (
            <ul className="divide-y divide-border">
              {history.data.map((d) => (
                <li key={d.id} className="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{d.center}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(d.date).toLocaleDateString()} · {d.volumeMl ? `${d.volumeMl} ml` : "No collection"}
                    </p>
                  </div>
                  <StatusBadge status={d.status === "COMPLETED" ? "COMPLETED" : "REVIEW"} />
                </li>
              ))}
            </ul>
          )}
        </SectionCard>
      </div>

      <SectionCard
        title="Donation camps near you"
        description="Register in advance to reserve a slot"
        actions={
          <Button asChild size="sm" variant="outline">
            <Link to="/app/camps">View all camps</Link>
          </Button>
        }
      >
        {camps.loading || !camps.data ? (
          <CardsSkeleton count={3} />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {upcoming.slice(0, 3).map((c) => (
              <article key={c.id} className="rounded-lg border border-border p-4">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="text-sm font-semibold">{c.name}</h3>
                  <StatusBadge status={c.status} />
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {new Date(c.date).toLocaleDateString()} · {c.startTime}–{c.endTime} · {c.city}
                </p>
                <div className="mt-3 space-y-1">
                  <Progress value={(c.registered / c.slots) * 100} />
                  <p className="text-xs text-muted-foreground">
                    {c.registered}/{c.slots} slots filled
                  </p>
                </div>
              </article>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}
