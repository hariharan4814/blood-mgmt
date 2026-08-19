import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAsync } from "@/hooks/useAsync";
import { donorService } from "@/services/donors/donorService";

export const Route = createFileRoute("/app/profile")({
  head: () => ({
    meta: [
      { title: "My Donor Profile — Blood Management System" },
      { name: "description", content: "Maintain your donor details, blood group, contact information and medical notes." },
      { property: "og:title", content: "My Donor Profile — Blood Management System" },
      { property: "og:description", content: "Maintain your donor details and eligibility information." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: ProfilePage,
});

function ProfilePage() {
  const { data, loading } = useAsync(() => donorService.getProfile());

  return (
    <DashboardLayout title="My Profile">
      <PageHeader title="Donor profile" description="Keep your details current so blood banks can reach you quickly." />
      {loading || !data ? (
        <SectionCard><TableSkeleton rows={6} cols={2} /></SectionCard>
      ) : (
        <div className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
          <SectionCard title="Personal details" description="Mock form — submissions are not persisted yet">
            <form
              className="grid gap-4 sm:grid-cols-2"
              onSubmit={(e) => {
                e.preventDefault();
                toast.success("Profile updated.");
              }}
            >
              <div className="grid gap-2">
                <Label htmlFor="name">Full name</Label>
                <Input id="name" defaultValue={data.name} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" defaultValue={data.email} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="phone">Phone</Label>
                <Input id="phone" defaultValue={data.phone} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="dob">Date of birth</Label>
                <Input id="dob" type="date" defaultValue={data.dob} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="weight">Weight (kg)</Label>
                <Input id="weight" type="number" defaultValue={data.weightKg} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="city">City</Label>
                <Input id="city" defaultValue={data.city} />
              </div>
              <div className="grid gap-2 sm:col-span-2">
                <Label htmlFor="address">Address</Label>
                <Textarea id="address" rows={2} defaultValue={data.address} />
              </div>
              <div className="grid gap-2 sm:col-span-2">
                <Label htmlFor="medical">Medical notes</Label>
                <Textarea id="medical" rows={3} defaultValue={data.medicalNotes} />
              </div>
              <div className="sm:col-span-2">
                <Button type="submit">Save changes</Button>
              </div>
            </form>
          </SectionCard>

          <SectionCard title="Donation summary">
            <dl className="space-y-4 text-sm">
              <div className="flex items-center justify-between">
                <dt className="text-muted-foreground">Donor ID</dt>
                <dd className="font-mono text-xs">{data.id}</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-muted-foreground">Blood group</dt>
                <dd className="text-lg font-bold text-primary">{data.group}</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-muted-foreground">Total donations</dt>
                <dd className="font-semibold">{data.totalDonations}</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-muted-foreground">Last donation</dt>
                <dd>{new Date(data.lastDonation).toLocaleDateString()}</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-muted-foreground">Next eligible</dt>
                <dd>{new Date(data.nextEligible).toLocaleDateString()}</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-muted-foreground">Eligibility</dt>
                <dd><StatusBadge status={data.eligible ? "ACTIVE" : "REVIEW"} /></dd>
              </div>
            </dl>
          </SectionCard>
        </div>
      )}
    </DashboardLayout>
  );
}
