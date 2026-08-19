import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { CalendarHeart, MapPin, Plus, Users } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { CardsSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { useAsync } from "@/hooks/useAsync";
import { campService } from "@/services/camps/campService";
import { useAuth } from "@/providers/AuthProvider";

export const Route = createFileRoute("/app/camps")({
  head: () => ({
    meta: [
      { title: "Donation Camps — Blood Management System" },
      { name: "description", content: "Plan blood donation camps, publish slots and track donor registrations." },
      { property: "og:title", content: "Donation Camps — Blood Management System" },
      { property: "og:description", content: "Plan donation camps and track donor registrations." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: CampsPage,
});

function CampsPage() {
  const { user } = useAuth();
  const { data, loading } = useAsync(() => campService.list());
  const [registered, setRegistered] = useState<string[]>([]);
  const [createOpen, setCreateOpen] = useState(false);
  const isDonor = user?.role === "DONOR";

  const register = async (campId: string, name: string) => {
    await campService.register(campId);
    setRegistered((prev) => [...prev, campId]);
    toast.success(`Slot reserved for ${name}. Bring a photo ID.`);
  };

  return (
    <DashboardLayout title="Donation Camps">
      <PageHeader
        title={isDonor ? "Donation camps near you" : "Donation camp management"}
        description={
          isDonor
            ? "Reserve a slot at an upcoming camp in your city."
            : "Schedule camps, publish slots and monitor registrations."
        }
        actions={
          !isDonor ? (
            <Dialog open={createOpen} onOpenChange={setCreateOpen}>
              <DialogTrigger asChild>
                <Button><Plus className="size-4" /> Schedule camp</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Schedule a donation camp</DialogTitle>
                  <DialogDescription>Published camps appear to donors in the selected city.</DialogDescription>
                </DialogHeader>
                <form
                  className="grid gap-4"
                  onSubmit={(e) => {
                    e.preventDefault();
                    setCreateOpen(false);
                    toast.success("Camp scheduled and published to donors.");
                  }}
                >
                  <div className="grid gap-2">
                    <Label htmlFor="camp-name">Camp name</Label>
                    <Input id="camp-name" required placeholder="Campus Mega Blood Drive" />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="grid gap-2">
                      <Label htmlFor="camp-city">City</Label>
                      <Input id="camp-city" required placeholder="Chennai" />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="camp-slots">Slots</Label>
                      <Input id="camp-slots" type="number" min={10} defaultValue={120} required />
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="grid gap-2">
                      <Label htmlFor="camp-date">Date</Label>
                      <Input id="camp-date" type="date" required />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="camp-start">Start</Label>
                      <Input id="camp-start" type="time" defaultValue="09:00" required />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="camp-end">End</Label>
                      <Input id="camp-end" type="time" defaultValue="16:00" required />
                    </div>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="camp-desc">Description</Label>
                    <Textarea id="camp-desc" rows={3} placeholder="Venue details, partner organisation, refreshments." />
                  </div>
                  <DialogFooter>
                    <Button type="submit">Publish camp</Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          ) : undefined
        }
      />

      {loading || !data ? (
        <CardsSkeleton count={4} />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {data.map((camp) => (
            <SectionCard key={camp.id} bodyClassName="p-5">
              <div className="flex items-start justify-between gap-2">
                <h2 className="font-semibold tracking-tight">{camp.name}</h2>
                <StatusBadge status={camp.status} />
              </div>
              <p className="mt-2 flex items-center gap-1.5 text-sm text-muted-foreground">
                <CalendarHeart className="size-4" />
                {new Date(camp.date).toLocaleDateString()} · {camp.startTime}–{camp.endTime}
              </p>
              <p className="mt-1 flex items-center gap-1.5 text-sm text-muted-foreground">
                <MapPin className="size-4" /> {camp.address}
              </p>
              <p className="mt-3 text-sm">{camp.description}</p>
              <div className="mt-4 space-y-1">
                <Progress value={(camp.registered / camp.slots) * 100} />
                <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Users className="size-3.5" /> {camp.registered}/{camp.slots} slots filled · organised by {camp.organizer}
                </p>
              </div>
              {isDonor && camp.status !== "COMPLETED" ? (
                <Button
                  className="mt-4 w-full"
                  variant={registered.includes(camp.id) ? "outline" : "default"}
                  disabled={registered.includes(camp.id)}
                  onClick={() => register(camp.id, camp.name)}
                >
                  {registered.includes(camp.id) ? "Slot reserved" : "Register"}
                </Button>
              ) : null}
            </SectionCard>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
}
