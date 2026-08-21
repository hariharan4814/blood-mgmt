import { useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { CalendarHeart, Loader2, MapPin, Plus, Users } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { CardsSkeleton, EmptyState } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import type { Camp } from "@/lib/types";
import { useAuth } from "@/providers/AuthProvider";
import { campService } from "@/services/camps/campService";

export const Route = createFileRoute("/app/camps")({
  head: () => ({
    meta: [
      { title: "Donation Camps — Blood Management System" },
      {
        name: "description",
        content: "Plan blood donation camps, publish slots and track donor registrations.",
      },
      { property: "og:title", content: "Donation Camps — Blood Management System" },
      { property: "og:description", content: "Plan donation camps and track donor registrations." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: CampsPage,
});

function CampsPage() {
  const { user } = useAuth();
  const [camps, setCamps] = useState<Camp[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [registeringId, setRegisteringId] = useState<string | null>(null);
  const [registered, setRegistered] = useState<string[]>([]);
  const [createOpen, setCreateOpen] = useState(false);

  const [form, setForm] = useState({
    name: "",
    city: "",
    slots: 100,
    date: "",
    startTime: "09:00",
    endTime: "16:00",
    description: "",
  });

  const isDonor = user?.role === "DONOR";
  const isStaff = user?.role === "BLOOD_BANK_ADMIN" || user?.role === "SUPER_ADMIN";

  const loadCamps = async () => {
    setLoading(true);
    try {
      const data = await campService.list();
      setCamps(data);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load donation camps.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCamps();
  }, []);

  const register = async (campId: string, name: string) => {
    setRegisteringId(campId);
    try {
      await campService.register(campId);
      setRegistered((prev) => [...prev, campId]);
      toast.success(`Slot reserved for ${name}. Bring a photo ID on the camp day.`);
      await loadCamps();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to register for camp.");
    } finally {
      setRegisteringId(null);
    }
  };

  const handleCreateCamp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim() || !form.city.trim() || !form.date) {
      toast.error("Please fill in all required camp details.");
      return;
    }

    setSubmitting(true);
    try {
      await campService.save({
        name: form.name.trim(),
        city: form.city.trim(),
        address: `${form.city.trim()} Blood Bank Center`,
        date: form.date,
        slots: form.slots,
        description: form.description.trim(),
        organizer: user?.organization || "Blood Bank Team",
        blood_bank: 1,
      });

      toast.success("Donation camp scheduled and published.");
      setCreateOpen(false);
      setForm({
        name: "",
        city: "",
        slots: 100,
        date: "",
        startTime: "09:00",
        endTime: "16:00",
        description: "",
      });
      await loadCamps();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to schedule camp.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <DashboardLayout title="Donation Camps">
      <PageHeader
        title={isDonor ? "Donation camps near you" : "Donation camp management"}
        description={
          isDonor
            ? "Reserve a voluntary blood donation slot at an upcoming camp in your city."
            : "Schedule camps, publish target collection slots, and monitor donor registrations."
        }
        actions={
          isStaff ? (
            <Dialog open={createOpen} onOpenChange={setCreateOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="size-4" /> Schedule camp
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Schedule a donation camp</DialogTitle>
                  <DialogDescription>
                    Published donation camps appear live to donors across the selected city.
                  </DialogDescription>
                </DialogHeader>
                <form className="grid gap-4" onSubmit={handleCreateCamp}>
                  <div className="grid gap-2">
                    <Label htmlFor="camp-name">Camp name *</Label>
                    <Input
                      id="camp-name"
                      required
                      placeholder="Campus Mega Blood Drive"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="grid gap-2">
                      <Label htmlFor="camp-city">City / Venue Location *</Label>
                      <Input
                        id="camp-city"
                        required
                        placeholder="Chennai"
                        value={form.city}
                        onChange={(e) => setForm({ ...form, city: e.target.value })}
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="camp-slots">Target Collection Slots *</Label>
                      <Input
                        id="camp-slots"
                        type="number"
                        min={10}
                        max={1000}
                        value={form.slots}
                        onChange={(e) =>
                          setForm({ ...form, slots: Math.max(10, parseInt(e.target.value, 10) || 10) })
                        }
                        required
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="grid gap-2">
                      <Label htmlFor="camp-date">Date *</Label>
                      <Input
                        id="camp-date"
                        type="date"
                        required
                        value={form.date}
                        onChange={(e) => setForm({ ...form, date: e.target.value })}
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="camp-start">Start</Label>
                      <Input
                        id="camp-start"
                        type="time"
                        value={form.startTime}
                        onChange={(e) => setForm({ ...form, startTime: e.target.value })}
                        required
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="camp-end">End</Label>
                      <Input
                        id="camp-end"
                        type="time"
                        value={form.endTime}
                        onChange={(e) => setForm({ ...form, endTime: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="camp-desc">Description</Label>
                    <Textarea
                      id="camp-desc"
                      rows={3}
                      placeholder="Venue details, partner organisation, refreshments, contact helpline."
                      value={form.description}
                      onChange={(e) => setForm({ ...form, description: e.target.value })}
                    />
                  </div>
                  <DialogFooter>
                    <Button type="submit" disabled={submitting}>
                      {submitting ? <Loader2 className="mr-2 size-4 animate-spin" /> : null}
                      Publish camp
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          ) : undefined
        }
      />

      {loading ? (
        <CardsSkeleton count={4} />
      ) : camps.length === 0 ? (
        <SectionCard>
          <EmptyState
            icon={CalendarHeart}
            title="No donation camps scheduled"
            description="Upcoming blood drives and mobile collection camps will appear here."
          />
        </SectionCard>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {camps.map((camp) => (
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
                <Progress value={Math.min(100, (camp.registered / (camp.slots || 1)) * 100)} />
                <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Users className="size-3.5" /> {camp.registered}/{camp.slots} slots filled · organised by{" "}
                  {camp.organizer}
                </p>
              </div>
              {isDonor && camp.status !== "COMPLETED" ? (
                <Button
                  className="mt-4 w-full"
                  variant={registered.includes(camp.id) ? "outline" : "default"}
                  disabled={registered.includes(camp.id) || registeringId === camp.id}
                  onClick={() => register(camp.id, camp.name)}
                >
                  {registeringId === camp.id ? (
                    <Loader2 className="mr-2 size-4 animate-spin" />
                  ) : null}
                  {registered.includes(camp.id) ? "Slot reserved" : "Register for camp"}
                </Button>
              ) : null}
            </SectionCard>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
}
