import { createFileRoute } from "@tanstack/react-router";
import { Building2, FlaskConical, Hospital, ShieldCheck, Siren, User, Users } from "lucide-react";
import { PublicLayout } from "@/components/layout/PublicLayout";

export const Route = createFileRoute("/about")({
  head: () => ({
    meta: [
      { title: "About — Blood Management System" },
      {
        name: "description",
        content:
          "How the Blood Management System coordinates donors, blood banks, laboratories and hospitals through role-based workflows.",
      },
      { property: "og:title", content: "About the Blood Management System" },
      {
        property: "og:description",
        content: "Role-based blood donation, inventory, testing and emergency response workflows.",
      },
    ],
  }),
  component: AboutPage,
});

const ROLES = [
  { icon: ShieldCheck, name: "Super Admin", body: "Governs users, blood banks, hospitals and system-wide audit trails." },
  { icon: Building2, name: "Blood Bank Admin", body: "Manages inventory, approves requests, runs camps and triggers emergency SOS." },
  { icon: Hospital, name: "Hospital Staff", body: "Raises blood requests with urgency levels and tracks fulfilment status." },
  { icon: FlaskConical, name: "Lab Technician", body: "Screens collected units and records pass/fail results per test panel." },
  { icon: User, name: "Donor", body: "Tracks eligibility, donation history, camps and responds to SOS alerts." },
];

const MODULES = [
  "Auth & RBAC",
  "Donor Management",
  "Inventory Management",
  "Testing / Quality Control",
  "Blood Requests",
  "Donation Camps",
  "Notifications",
  "Analytics Dashboard",
  "Emergency SOS Broadcast",
];

function AboutPage() {
  return (
    <PublicLayout>
      <section className="border-b border-border" style={{ background: "var(--gradient-hero)" }}>
        <div className="mx-auto max-w-4xl px-4 py-16 text-center">
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            About the Blood Management System
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
            A role-based platform that removes phone-tree coordination from blood supply. Donors,
            laboratories, blood banks and hospitals work from a single record of truth for every unit
            collected, tested, reserved and transfused.
          </p>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16">
        <h2 className="text-2xl font-semibold tracking-tight">Who uses it</h2>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {ROLES.map((r) => (
            <div key={r.name} className="card-surface p-5">
              <span className="grid size-10 place-items-center rounded-lg bg-primary/10 text-primary">
                <r.icon className="size-5" />
              </span>
              <h3 className="mt-4 font-semibold tracking-tight">{r.name}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{r.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-y border-border bg-card">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 lg:grid-cols-2">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">Modules</h2>
            <ul className="mt-6 grid gap-2 sm:grid-cols-2">
              {MODULES.map((m) => (
                <li
                  key={m}
                  className="flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm"
                >
                  <span className="size-1.5 rounded-full bg-primary" aria-hidden />
                  {m}
                </li>
              ))}
            </ul>
          </div>
          <div className="space-y-5">
            <h2 className="text-2xl font-semibold tracking-tight">The differentiator</h2>
            <div className="rounded-lg border border-destructive/25 bg-destructive/5 p-5">
              <Siren className="size-5 text-destructive" />
              <h3 className="mt-3 font-semibold tracking-tight">Emergency SOS broadcast</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">
                For critical requests, blood bank administrators select a blood group and radius, preview
                the eligible donor count and broadcast. Donor responses stream back with distance so the
                bank can call the closest available donor first.
              </p>
            </div>
            <div className="rounded-lg border border-border p-5">
              <Users className="size-5 text-primary" />
              <h3 className="mt-3 font-semibold tracking-tight">Auditable by design</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">
                Every approval, test result and dispatch is attributed to a user and timestamped, so a
                unit's chain of custody can be reconstructed end to end.
              </p>
            </div>
          </div>
        </div>
      </section>
    </PublicLayout>
  );
}