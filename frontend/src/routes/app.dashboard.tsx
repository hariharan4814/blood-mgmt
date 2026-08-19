import { createFileRoute } from "@tanstack/react-router";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { PageHeader } from "@/components/common/PageHeader";
import { BloodBankDashboard } from "@/components/dashboards/BloodBankDashboard";
import { DonorDashboard } from "@/components/dashboards/DonorDashboard";
import { HospitalDashboard } from "@/components/dashboards/HospitalDashboard";
import { LabDashboard } from "@/components/dashboards/LabDashboard";
import { SuperAdminDashboard } from "@/components/dashboards/SuperAdminDashboard";
import { ROLE_LABELS } from "@/lib/types";
import { useAuth } from "@/providers/AuthProvider";

export const Route = createFileRoute("/app/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard — Blood Management System" },
      { name: "description", content: "Role-based dashboard with live blood inventory, requests, testing and emergency SOS insights." },
      { property: "og:title", content: "Dashboard — Blood Management System" },
      { property: "og:description", content: "Role-based dashboard for blood banks, hospitals, labs and donors." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: DashboardPage,
});

const DESCRIPTIONS: Record<string, string> = {
  SUPER_ADMIN: "Platform-wide health across blood banks, hospitals and users.",
  BLOOD_BANK_ADMIN: "Inventory, requests, testing and camp operations at a glance.",
  HOSPITAL_STAFF: "Track your blood requests and check network availability.",
  LAB_TECHNICIAN: "Screen collected units and publish test outcomes.",
  DONOR: "Your eligibility, donation history and nearby camps.",
};

function DashboardPage() {
  const { user } = useAuth();
  if (!user) return null;

  return (
    <DashboardLayout title="Dashboard" searchPlaceholder="Search units, requests, donors...">
      <PageHeader
        title={`Welcome back, ${user.name.split(" ")[0]}`}
        description={DESCRIPTIONS[user.role] ?? ""}
      />
      <p className="text-xs text-muted-foreground">
        Signed in as {ROLE_LABELS[user.role]} · {user.organization}
      </p>
      {user.role === "SUPER_ADMIN" ? <SuperAdminDashboard /> : null}
      {user.role === "BLOOD_BANK_ADMIN" ? <BloodBankDashboard /> : null}
      {user.role === "HOSPITAL_STAFF" ? <HospitalDashboard /> : null}
      {user.role === "LAB_TECHNICIAN" ? <LabDashboard /> : null}
      {user.role === "DONOR" ? <DonorDashboard /> : null}
    </DashboardLayout>
  );
}
