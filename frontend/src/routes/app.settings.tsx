import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

export const Route = createFileRoute("/app/settings")({
  head: () => ({
    meta: [
      { title: "System Settings — Blood Management System" },
      { name: "description", content: "Configure stock thresholds, SOS radius defaults and notification channels." },
      { property: "og:title", content: "System Settings — Blood Management System" },
      { property: "og:description", content: "Configure thresholds, SOS defaults and notification channels." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: SettingsPage,
});

const TOGGLES = [
  { id: "sms", label: "SMS alerts", hint: "Send SOS and request updates over SMS", defaultChecked: true },
  { id: "email", label: "Email digests", hint: "Daily inventory and request summary", defaultChecked: true },
  { id: "push", label: "Push notifications", hint: "Browser push for critical events", defaultChecked: false },
  { id: "auto-expire", label: "Auto-expire units", hint: "Discard units automatically past shelf life", defaultChecked: true },
];

function SettingsPage() {
  return (
    <DashboardLayout title="System Settings">
      <PageHeader title="System settings" description="Platform defaults. Values are mocked until the backend is connected." />
      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard title="Thresholds & defaults">
          <form
            className="grid gap-4"
            onSubmit={(e) => {
              e.preventDefault();
              toast.success("Settings saved.");
            }}
          >
            <div className="grid gap-2">
              <Label htmlFor="low-stock">Low stock threshold (units per group)</Label>
              <Input id="low-stock" type="number" defaultValue={20} />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="expiry">Unit shelf life (days)</Label>
              <Input id="expiry" type="number" defaultValue={42} />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="sos-radius">Default SOS radius (km)</Label>
              <Input id="sos-radius" type="number" defaultValue={15} />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="cooldown">Donor cooldown (days)</Label>
              <Input id="cooldown" type="number" defaultValue={90} />
            </div>
            <Button type="submit" className="w-fit">Save settings</Button>
          </form>
        </SectionCard>

        <SectionCard title="Notification channels">
          <ul className="space-y-5">
            {TOGGLES.map((t) => (
              <li key={t.id} className="flex items-start justify-between gap-4">
                <div>
                  <Label htmlFor={t.id}>{t.label}</Label>
                  <p className="text-xs text-muted-foreground">{t.hint}</p>
                </div>
                <Switch id={t.id} defaultChecked={t.defaultChecked} />
              </li>
            ))}
          </ul>
        </SectionCard>
      </div>
    </DashboardLayout>
  );
}
