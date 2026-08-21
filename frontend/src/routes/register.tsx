import { useState } from "react";
import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import { Info, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { AuthLayout } from "@/components/layout/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BLOOD_GROUPS } from "@/lib/types";
import { authService } from "@/services/auth/authService";

export const Route = createFileRoute("/register")({
  head: () => ({
    meta: [
      { title: "Register — Blood Management System" },
      {
        name: "description",
        content:
          "Create a donor or hospital staff account to donate blood, track eligibility and raise blood requests.",
      },
      { property: "og:title", content: "Register — Blood Management System" },
      { property: "og:description", content: "Donor and hospital staff registration." },
    ],
  }),
  component: RegisterPage,
});

type PublicRole = "DONOR" | "HOSPITAL_STAFF";

function RegisterPage() {
  const navigate = useNavigate();
  const [role, setRole] = useState<PublicRole>("DONOR");
  const [submitting, setSubmitting] = useState(false);
  type Errors = Partial<Record<"name" | "email" | "password" | "confirm" | "hospital" | "general", string>>;
  const [errors, setErrors] = useState<Errors>({});
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    password: "",
    confirm: "",
    group: "O+",
    city: "",
    hospital: "",
    staffId: "",
  });

  const set = (key: keyof typeof form) => (value: string) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const next: Errors = {};
    if (!form.name.trim()) next.name = "Full name is required.";
    if (!/^\S+@\S+\.\S+$/.test(form.email)) next.email = "Enter a valid email address.";
    if (form.password.length < 8) next.password = "Use at least 8 characters.";
    if (form.password !== form.confirm) next.confirm = "Passwords do not match.";
    if (role === "HOSPITAL_STAFF" && !form.hospital.trim())
      next.hospital = "Hospital name is required.";
    setErrors(next);
    if (Object.keys(next).length > 0) return;

    setSubmitting(true);
    try {
      await authService.register({
        name: form.name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim(),
        password: form.password,
        password_confirm: form.confirm,
        role,
        blood_group: form.group,
        city: form.city.trim(),
        hospital: form.hospital.trim(),
        staffId: form.staffId.trim(),
      });
      toast.success(
        role === "DONOR"
          ? "Donor account created successfully! You can sign in now."
          : "Hospital staff account registered! You can sign in now.",
      );
      navigate({ to: "/login" });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Registration failed. Please check your details.";
      setErrors({ general: msg });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout
      title="Create an account"
      description="Donors and hospital staff can self-register. Admin, blood bank and lab accounts are created by administrators."
    >
      <Tabs value={role} onValueChange={(v) => setRole(v as PublicRole)}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="DONOR">Donor</TabsTrigger>
          <TabsTrigger value="HOSPITAL_STAFF">Hospital Staff</TabsTrigger>
        </TabsList>
      </Tabs>

      <form onSubmit={onSubmit} className="mt-6 space-y-5">
        {errors.general ? (
          <p className="rounded-md border border-destructive/30 bg-destructive/8 px-3 py-2 text-sm text-destructive">
            {errors.general}
          </p>
        ) : null}

        <Field label="Full name" id="name" error={errors.name}>
          <Input
            id="name"
            value={form.name}
            onChange={(e) => set("name")(e.target.value)}
            disabled={submitting}
            required
          />
        </Field>
        <Field label="Email" id="email" error={errors.email}>
          <Input
            id="email"
            type="email"
            value={form.email}
            onChange={(e) => set("email")(e.target.value)}
            disabled={submitting}
            required
          />
        </Field>
        <Field label="Phone" id="phone">
          <Input
            id="phone"
            value={form.phone}
            onChange={(e) => set("phone")(e.target.value)}
            disabled={submitting}
          />
        </Field>

        {role === "DONOR" ? (
          <div className="grid gap-5 sm:grid-cols-2">
            <Field label="Blood group" id="group">
              <Select value={form.group} onValueChange={set("group")} disabled={submitting}>
                <SelectTrigger id="group">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {BLOOD_GROUPS.map((g) => (
                    <SelectItem key={g} value={g}>
                      {g}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
            <Field label="City" id="city">
              <Input
                id="city"
                value={form.city}
                onChange={(e) => set("city")(e.target.value)}
                disabled={submitting}
              />
            </Field>
          </div>
        ) : (
          <div className="grid gap-5 sm:grid-cols-2">
            <Field label="Hospital" id="hospital" error={errors.hospital}>
              <Input
                id="hospital"
                value={form.hospital}
                onChange={(e) => set("hospital")(e.target.value)}
                disabled={submitting}
              />
            </Field>
            <Field label="Staff ID" id="staffId">
              <Input
                id="staffId"
                value={form.staffId}
                onChange={(e) => set("staffId")(e.target.value)}
                disabled={submitting}
              />
            </Field>
          </div>
        )}

        <div className="grid gap-5 sm:grid-cols-2">
          <Field label="Password" id="password" error={errors.password}>
            <Input
              id="password"
              type="password"
              value={form.password}
              onChange={(e) => set("password")(e.target.value)}
              disabled={submitting}
              required
            />
          </Field>
          <Field label="Confirm password" id="confirm" error={errors.confirm}>
            <Input
              id="confirm"
              type="password"
              value={form.confirm}
              onChange={(e) => set("confirm")(e.target.value)}
              disabled={submitting}
              required
            />
          </Field>
        </div>

        <p className="flex gap-2 rounded-md border border-border bg-muted/50 px-3 py-2 text-xs text-muted-foreground">
          <Info className="mt-0.5 size-4 shrink-0" />
          Super Admin, Blood Bank Admin and Lab Technician accounts cannot be self-registered — they are
          provisioned by an administrator.
        </p>

        <Button type="submit" size="lg" className="w-full" disabled={submitting}>
          {submitting ? <Loader2 className="mr-2 size-4 animate-spin" /> : null}
          {role === "DONOR" ? "Create donor account" : "Request hospital access"}
        </Button>

        <p className="text-center text-sm text-muted-foreground">
          Already registered?{" "}
          <Link to="/login" className="font-medium text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}

function Field({
  label,
  id,
  error,
  children,
}: {
  label: string;
  id: string;
  error?: string | undefined;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}