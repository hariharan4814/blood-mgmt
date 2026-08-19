import { useState } from "react";
import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { AuthLayout } from "@/components/layout/AuthLayout";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ROLE_LABELS, type Role } from "@/lib/types";
import { useAuth } from "@/providers/AuthProvider";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Login — Blood Management System" },
      {
        name: "description",
        content: "Sign in to the Blood Management System to manage donations, inventory and requests.",
      },
      { property: "og:title", content: "Login — Blood Management System" },
      { property: "og:description", content: "Role-based sign in for the Blood Management System." },
    ],
  }),
  component: LoginPage,
});

const DEMO_ACCOUNTS: Record<Role, string> = {
  SUPER_ADMIN: "meera@bms.health",
  BLOOD_BANK_ADMIN: "arun@citybank.health",
  HOSPITAL_STAFF: "kavya@apollo.health",
  LAB_TECHNICIAN: "ravi@citybank.health",
  DONOR: "hari@donor.health",
};

function LoginPage() {
  const navigate = useNavigate();
  const { login, loading } = useAuth();
  const [role, setRole] = useState<Role>("BLOOD_BANK_ADMIN");
  const [email, setEmail] = useState(DEMO_ACCOUNTS.BLOOD_BANK_ADMIN);
  const [password, setPassword] = useState("demo1234");
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // MOCK SUBMIT — replace with POST /api/auth/login once the backend exists.
  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!email.trim() || !password.trim()) {
      setError("Enter both email and password to continue.");
      return;
    }
    const user = await login({ email: email.trim(), password, role, remember });
    toast.success(`Signed in as ${ROLE_LABELS[user.role]}`);
    navigate({ to: "/app/dashboard" });
  };

  return (
    <AuthLayout title="Sign in" description="Access your role-based dashboard.">
      <form onSubmit={onSubmit} className="space-y-5">
        <div className="space-y-2">
          <Label htmlFor="email">Email or username</Label>
          <Input
            id="email"
            type="text"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@hospital.health"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="role">Demo role (frontend only)</Label>
          <Select
            value={role}
            onValueChange={(v) => {
              const next = v as Role;
              setRole(next);
              setEmail(DEMO_ACCOUNTS[next]);
            }}
          >
            <SelectTrigger id="role">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(Object.keys(ROLE_LABELS) as Role[]).map((r) => (
                <SelectItem key={r} value={r}>
                  {ROLE_LABELS[r]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            Temporary selector for demonstration. The real role will come from the JWT claims.
          </p>
        </div>

        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm">
            <Checkbox checked={remember} onCheckedChange={(v) => setRemember(Boolean(v))} />
            Remember me
          </label>
          <Link to="/forgot-password" className="text-sm font-medium text-primary hover:underline">
            Forgot password?
          </Link>
        </div>

        {error ? (
          <p className="rounded-md border border-destructive/30 bg-destructive/8 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        ) : null}

        <Button type="submit" className="w-full" size="lg" disabled={loading}>
          {loading ? <Loader2 className="mr-2 size-4 animate-spin" /> : null}
          Sign in
        </Button>

        <p className="text-center text-sm text-muted-foreground">
          New donor or hospital?{" "}
          <Link to="/register" className="font-medium text-primary hover:underline">
            Create an account
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}