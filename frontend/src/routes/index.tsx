import { Link, createFileRoute } from "@tanstack/react-router";
import {
  ArrowRight,
  CalendarHeart,
  ClipboardCheck,
  Droplet,
  HeartPulse,
  Hospital,
  Siren,
  Timer,
  UserPlus,
} from "lucide-react";
import { PublicLayout } from "@/components/layout/PublicLayout";
import { PulseLine } from "@/components/brand/PulseLine";
import heroImage from "@/assets/hero-donation.jpg";
import campImage from "@/assets/camp-community.jpg";
import { BloodGroupTile } from "@/components/common/BloodGroupTile";
import { Button } from "@/components/ui/button";
import { publicAvailability } from "@/services/mock/data";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Blood Management System — Donate Blood, Save Lives" },
      {
        name: "description",
        content:
          "Check live blood availability, register as a donor and coordinate hospital blood requests through one role-based platform.",
      },
      { property: "og:title", content: "Blood Management System — Donate Blood, Save Lives" },
      {
        property: "og:description",
        content: "Live blood availability, donor registration and emergency SOS coordination.",
      },
    ],
  }),
  component: LandingPage,
});

const STEPS = [
  {
    icon: UserPlus,
    title: "Register & screen",
    body: "Create a donor profile, record your blood group and complete the eligibility checklist.",
  },
  {
    icon: CalendarHeart,
    title: "Donate at a camp or bank",
    body: "Book a slot at an upcoming donation camp or walk into a partnered blood bank.",
  },
  {
    icon: ClipboardCheck,
    title: "Testing & quality control",
    body: "Each unit is screened for HIV, Hepatitis B & C, Syphilis and Malaria before release.",
  },
  {
    icon: Hospital,
    title: "Reaches a patient",
    body: "Hospitals raise requests, blood banks approve and dispatch, and every step is logged.",
  },
];

const REASONS = [
  { icon: HeartPulse, title: "One donation, three lives", body: "A single unit is separated into red cells, plasma and platelets for up to three patients." },
  { icon: Timer, title: "Blood cannot be manufactured", body: "Red cells last only 35–42 days, so inventory depends entirely on regular donors." },
  { icon: Droplet, title: "Free health screening", body: "Every donation includes haemoglobin, blood pressure and infectious disease screening." },
];

const QUOTES = [
  {
    text: "The gift of blood is the gift of life. There is no substitute for human kindness.",
    author: "Dr. Meera Raghavan",
    role: "Transfusion Medicine, City Blood Bank",
  },
  {
    text: "I donate because someone I love once needed a stranger to show up. Now I am that stranger.",
    author: "Arjun Kale",
    role: "Regular donor, 14 donations",
  },
  {
    text: "It takes twenty minutes of your day to give someone the rest of their life.",
    author: "Sister Anita George",
    role: "Camp coordinator",
  },
];

function LandingPage() {
  const lowGroups = publicAvailability.filter((g) => g.level === "LOW").map((g) => g.group);

  return (
    <PublicLayout>
      <section className="relative overflow-hidden border-b border-border">
        <img
          src={heroImage}
          alt="A nurse comforting a young blood donor at a donation centre"
          width={1600}
          height={1104}
          className="absolute inset-0 size-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-background via-background/86 to-background/10" />
        <div className="relative mx-auto grid max-w-6xl gap-10 px-4 py-16 lg:grid-cols-[1.1fr_0.9fr] lg:items-center lg:py-24">
          <div className="rise-in">
            <span className="inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/8 px-3 py-1 text-xs font-medium text-primary">
              <Siren className="size-3.5" /> Live emergency coordination platform
            </span>
            <h1 className="mt-5 text-4xl font-semibold tracking-tight sm:text-5xl">
              Donate Blood, <span className="text-primary">Save Lives</span>
            </h1>
            <p className="mt-4 max-w-xl text-base text-muted-foreground sm:text-lg">
              A single system connecting donors, blood banks, laboratories and hospitals — with
              real-time inventory, verified testing and emergency SOS broadcasts to nearby donors.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button asChild size="xl" variant="cta">
                <Link to="/register">
                  Become a Donor <ArrowRight className="ml-1 size-4 transition-transform group-hover:translate-x-1" />
                </Link>
              </Button>
              <Button
                asChild
                size="xl"
                variant="outline"
                className="rounded-full bg-card/80 backdrop-blur transition-colors hover:border-primary/40 hover:text-primary"
              >
                <Link to="/availability">Check Blood Availability</Link>
              </Button>
            </div>
            <dl className="mt-10 grid max-w-lg grid-cols-3 gap-6">
              {[
                { k: "12,840", v: "Units donated" },
                { k: "48", v: "Partner hospitals" },
                { k: "< 20 min", v: "Avg. SOS response" },
              ].map((s) => (
                <div key={s.v}>
                  <dt className="text-2xl font-semibold tracking-tight">{s.k}</dt>
                  <dd className="text-xs text-muted-foreground">{s.v}</dd>
                </div>
              ))}
            </dl>
          </div>

          <div className="card-surface bg-card/95 p-6 backdrop-blur animate-float-soft">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold tracking-tight">Blood availability</h2>
              <span className="text-xs text-muted-foreground">Regional snapshot</span>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-2">
              {publicAvailability.map((g) => (
                <BloodGroupTile key={g.group} group={g.group} units={g.units} level={g.level} />
              ))}
            </div>
            <p className="mt-4 text-xs text-muted-foreground">
              Indicative levels from demo data. Contact your blood bank to confirm before travelling.
            </p>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16">
        <h2 className="text-2xl font-semibold tracking-tight">How it works</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          From registration to transfusion, every unit is traceable.
        </p>
        <ol className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((s, i) => (
            <li key={s.title} className="card-surface hover-lift p-5">
              <span className="grid size-10 place-items-center rounded-lg bg-primary/10 text-primary">
                <s.icon className="size-5" />
              </span>
              <p className="mt-4 text-xs font-medium text-muted-foreground">Step {i + 1}</p>
              <h3 className="font-semibold tracking-tight">{s.title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{s.body}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="border-y border-border bg-card">
        <div className="mx-auto max-w-6xl px-4 py-16">
          <h2 className="text-2xl font-semibold tracking-tight">Why donate blood</h2>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {REASONS.map((r) => (
              <div key={r.title} className="hover-lift rounded-xl border border-border bg-background p-5">
                <r.icon className="size-5 text-primary" />
                <h3 className="mt-4 font-semibold tracking-tight">{r.title}</h3>
                <p className="mt-1.5 text-sm text-muted-foreground">{r.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16">
        <div className="text-center">
          <h2 className="text-2xl font-semibold tracking-tight">Words from our community</h2>
          <PulseLine className="mx-auto mt-3 h-6 w-56" />
        </div>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {QUOTES.map((q) => (
            <blockquote key={q.author} className="card-surface hover-lift p-6">
              <span className="quote-mark block" aria-hidden="true" />
              <p className="text-[0.95rem] leading-relaxed text-foreground/90 italic">{q.text}</p>
              <footer className="mt-4">
                <p className="text-sm font-semibold">{q.author}</p>
                <p className="text-xs text-muted-foreground">{q.role}</p>
              </footer>
            </blockquote>
          ))}
        </div>
      </section>

      <section className="relative overflow-hidden border-y border-border">
        <img
          src={campImage}
          alt="Volunteers welcoming donors at a community blood donation camp"
          loading="lazy"
          width={1600}
          height={912}
          className="absolute inset-0 size-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-background/96 via-background/78 to-background/15" />
        <div className="relative mx-auto max-w-6xl px-4 py-20">
          <div className="max-w-xl">
            <h2 className="text-3xl font-semibold tracking-tight">
              Every camp is a room full of neighbours saying yes.
            </h2>
            <p className="mt-3 text-sm text-muted-foreground sm:text-base">
              Find a donation camp near you, register in a minute, and walk in knowing exactly what to
              expect — the checklist, the screening and the cup of tea afterwards.
            </p>
            <Button asChild size="lg" variant="cta" className="mt-7">
              <Link to="/availability">Find a camp near me</Link>
            </Button>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16">
        <div className="card-surface flex flex-col gap-6 border-destructive/25 bg-destructive/5 p-8 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-2 rounded-full bg-destructive/12 px-3 py-1 text-xs font-medium text-destructive">
              <Siren className="size-3.5" /> Emergency awareness
            </span>
            <h2 className="mt-4 text-2xl font-semibold tracking-tight">
              {lowGroups.length > 0
                ? `Critical shortage: ${lowGroups.join(", ")}`
                : "Emergency SOS keeps critical patients covered"}
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              When stock falls below a safe threshold, verified blood bank administrators broadcast an
              SOS to eligible donors within a chosen radius. Donors respond in one tap and the bank sees
              live availability counts.
            </p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row lg:flex-col">
            <Button asChild size="lg" variant="cta">
              <Link to="/register">Join the donor network</Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="rounded-full">
              <Link to="/about">Learn about the system</Link>
            </Button>
          </div>
        </div>
      </section>
    </PublicLayout>
  );
}
