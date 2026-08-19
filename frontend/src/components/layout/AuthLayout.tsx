import type { ReactNode } from "react";
import { Link } from "@tanstack/react-router";
import { HeartPulse, ShieldCheck, Siren } from "lucide-react";
import { Logo } from "@/components/brand/Logo";
import authImage from "@/assets/camp-community.jpg";

export function AuthLayout({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden flex-col justify-between overflow-hidden p-10 lg:flex">
        <img
          src={authImage}
          alt="Volunteers at a blood donation camp"
          className="absolute inset-0 size-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-background/92 via-background/88 to-background/95" />
        <div className="relative flex flex-1 flex-col justify-between">
        <Link to="/">
          <Logo />
        </Link>
        <div className="max-w-md space-y-6">
          <h2 className="text-3xl font-semibold tracking-tight">
            Coordinated blood care, from donor to bedside.
          </h2>
          <ul className="space-y-4 text-sm text-muted-foreground">
            <li className="flex gap-3">
              <HeartPulse className="mt-0.5 size-5 shrink-0 text-primary" />
              Track donors, inventory and testing in one auditable workflow.
            </li>
            <li className="flex gap-3">
              <Siren className="mt-0.5 size-5 shrink-0 text-primary" />
              Broadcast emergency SOS alerts to nearby eligible donors.
            </li>
            <li className="flex gap-3">
              <ShieldCheck className="mt-0.5 size-5 shrink-0 text-primary" />
              Role-based access for admins, hospitals, labs and donors.
            </li>
          </ul>
        </div>
        <p className="text-xs text-muted-foreground">Demo build · mock data only</p>
        </div>
      </div>

      <div className="flex flex-col">
        <div className="flex items-center justify-between p-4 lg:justify-end">
          <Link to="/" className="lg:hidden">
            <Logo />
          </Link>
        </div>
        <div className="flex flex-1 items-center justify-center px-4 pb-12">
          <div className="w-full max-w-md">
            <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{description}</p>
            <div className="mt-8">{children}</div>
          </div>
        </div>
      </div>
    </div>
  );
}