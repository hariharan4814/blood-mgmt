import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  Edit,
  Lock,
  Plus,
  Search,
  Trash2,
  UserCheck,
  UserX,
  Users,
} from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState, TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAsync } from "@/hooks/useAsync";
import { ROLE_LABELS, type Role, type User } from "@/lib/types";
import { userService } from "@/services/users/userService";

export const Route = createFileRoute("/app/users")({
  head: () => ({
    meta: [
      { title: "User Management — Blood Management System" },
      {
        name: "description",
        content:
          "Manage platform accounts and role assignments across blood banks, hospitals, labs and donors.",
      },
      { property: "og:title", content: "User Management — Blood Management System" },
      { property: "og:description", content: "Manage accounts and role assignments." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: UsersPage,
});

function UsersPage() {
  const { data, loading, error, reload } = useAsync(() => userService.listUsers());
  const [query, setQuery] = useState("");
  const [role, setRole] = useState("ALL");

  // Create User Modal State
  const [createOpen, setCreateOpen] = useState(false);
  const [createUsername, setCreateUsername] = useState("");
  const [createEmail, setCreateEmail] = useState("");
  const [createPassword, setCreatePassword] = useState("");
  const [createRole, setCreateRole] = useState<Role>("DONOR");
  const [createFirstName, setCreateFirstName] = useState("");
  const [createLastName, setCreateLastName] = useState("");
  const [createPhone, setCreatePhone] = useState("");
  const [creating, setCreating] = useState(false);

  // Edit User Modal State
  const [editOpen, setEditOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [editRole, setEditRole] = useState<Role>("DONOR");
  const [editPhone, setEditPhone] = useState("");
  const [updating, setUpdating] = useState(false);

  // Delete User Confirmation State
  const [deleteTarget, setDeleteTarget] = useState<User | null>(null);
  const [deleting, setDeleting] = useState(false);

  const filtered = useMemo(() => {
    const list = data ?? [];
    return list.filter((u) => {
      const matchesRole = role === "ALL" || u.role === role;
      const userName = (u.name || "").toLowerCase();
      const userEmail = (u.email || "").toLowerCase();
      const q = query.toLowerCase();
      const matchesQuery = !q || userName.includes(q) || userEmail.includes(q);
      return matchesRole && matchesQuery;
    });
  }, [data, role, query]);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createUsername.trim() || !createEmail.trim() || !createPassword.trim()) {
      toast.error("Please fill in username, email, and password.");
      return;
    }
    setCreating(true);
    try {
      await userService.createUser({
        username: createUsername.trim(),
        email: createEmail.trim(),
        password: createPassword,
        role: createRole,
        first_name: createFirstName.trim(),
        last_name: createLastName.trim(),
        phone: createPhone.trim(),
        is_active: true,
      });
      toast.success(`User '${createUsername}' created successfully.`);
      setCreateOpen(false);
      setCreateUsername("");
      setCreateEmail("");
      setCreatePassword("");
      setCreateFirstName("");
      setCreateLastName("");
      setCreatePhone("");
      reload();
    } catch (err: any) {
      toast.error(err.message || "Failed to create user account.");
    } finally {
      setCreating(false);
    }
  };

  const handleOpenEdit = (u: User) => {
    setEditingUser(u);
    setEditRole(u.role);
    setEditPhone("");
    setEditOpen(true);
  };

  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;
    setUpdating(true);
    try {
      await userService.updateUser(editingUser.id, {
        role: editRole,
        ...(editPhone.trim() ? { phone: editPhone.trim() } : {}),
      });
      toast.success(`User '${editingUser.name}' updated successfully.`);
      setEditOpen(false);
      setEditingUser(null);
      reload();
    } catch (err: any) {
      toast.error(err.message || "Failed to update user.");
    } finally {
      setUpdating(false);
    }
  };

  const handleToggleStatus = async (u: User) => {
    try {
      await userService.toggleActive(u.id, u.status);
      toast.success(
        `User '${u.name}' account is now ${u.status === "ACTIVE" ? "suspended" : "active"}.`,
      );
      reload();
    } catch (err: any) {
      toast.error(err.message || "Failed to change account status.");
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await userService.deleteUser(deleteTarget.id);
      toast.success(`User '${deleteTarget.name}' deleted permanently.`);
      setDeleteTarget(null);
      reload();
    } catch (err: any) {
      toast.error(err.message || "Failed to delete user account.");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <DashboardLayout title="Users">
      <PageHeader
        title="User management"
        description="Accounts, role provisioning, and access permissions across the platform."
      />
      <SectionCard
        bodyClassName="p-0"
        title="All accounts"
        description={`${filtered.length} account${filtered.length === 1 ? "" : "s"}`}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="w-48 pl-9"
                placeholder="Search users"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                aria-label="Search users"
              />
            </div>
            <Select value={role} onValueChange={setRole}>
              <SelectTrigger className="w-44" aria-label="Filter by role">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All roles</SelectItem>
                {Object.entries(ROLE_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Dialog open={createOpen} onOpenChange={setCreateOpen}>
              <DialogTrigger asChild>
                <Button size="sm">
                  <Plus className="mr-2 size-4" /> Add User
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <form onSubmit={handleCreateUser}>
                  <DialogHeader>
                    <DialogTitle>Provision New User</DialogTitle>
                    <DialogDescription>
                      Create a verified user account with assigned system permissions.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-3 py-3">
                    <div className="grid grid-cols-2 gap-2">
                      <div className="space-y-1">
                        <Label htmlFor="create-first" className="text-xs">First Name</Label>
                        <Input
                          id="create-first"
                          value={createFirstName}
                          onChange={(e) => setCreateFirstName(e.target.value)}
                          placeholder="John"
                        />
                      </div>
                      <div className="space-y-1">
                        <Label htmlFor="create-last" className="text-xs">Last Name</Label>
                        <Input
                          id="create-last"
                          value={createLastName}
                          onChange={(e) => setCreateLastName(e.target.value)}
                          placeholder="Doe"
                        />
                      </div>
                    </div>

                    <div className="space-y-1">
                      <Label htmlFor="create-user" className="text-xs">Username *</Label>
                      <Input
                        id="create-user"
                        value={createUsername}
                        onChange={(e) => setCreateUsername(e.target.value)}
                        placeholder="johndoe"
                        required
                      />
                    </div>

                    <div className="space-y-1">
                      <Label htmlFor="create-email" className="text-xs">Email Address *</Label>
                      <Input
                        id="create-email"
                        type="email"
                        value={createEmail}
                        onChange={(e) => setCreateEmail(e.target.value)}
                        placeholder="john@example.com"
                        required
                      />
                    </div>

                    <div className="space-y-1">
                      <Label htmlFor="create-pass" className="text-xs">Initial Password *</Label>
                      <Input
                        id="create-pass"
                        type="password"
                        value={createPassword}
                        onChange={(e) => setCreatePassword(e.target.value)}
                        placeholder="••••••••••••"
                        required
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <div className="space-y-1">
                        <Label htmlFor="create-role" className="text-xs">Assigned Role *</Label>
                        <Select
                          value={createRole}
                          onValueChange={(v) => setCreateRole(v as Role)}
                        >
                          <SelectTrigger id="create-role">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {Object.entries(ROLE_LABELS).map(([k, v]) => (
                              <SelectItem key={k} value={k}>
                                {v}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-1">
                        <Label htmlFor="create-phone" className="text-xs">Phone Number</Label>
                        <Input
                          id="create-phone"
                          value={createPhone}
                          onChange={(e) => setCreatePhone(e.target.value)}
                          placeholder="+1 555-0100"
                        />
                      </div>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setCreateOpen(false)}
                    >
                      Cancel
                    </Button>
                    <Button type="submit" disabled={creating}>
                      {creating ? "Creating..." : "Create Account"}
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        }
      >
        {loading ? (
          <TableSkeleton cols={6} />
        ) : error ? (
          <div className="p-5">
            <EmptyState
              icon={Users}
              title="Access restricted or unavailable"
              description={error.message || "User management is restricted to Super Administrators."}
            />
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-5">
            <EmptyState
              icon={Users}
              title="No matching users"
              description="Try adjusting your search query or role filter."
            />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Organisation</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((u) => (
                <TableRow key={u.id}>
                  <TableCell className="font-medium">{u.name || "User"}</TableCell>
                  <TableCell>{u.email || "—"}</TableCell>
                  <TableCell>{ROLE_LABELS[u.role as Role] || u.role}</TableCell>
                  <TableCell>{u.organization || "—"}</TableCell>
                  <TableCell>
                    <StatusBadge status={u.status || "ACTIVE"} />
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleOpenEdit(u)}
                        title="Edit User"
                        aria-label={`Edit ${u.name}`}
                      >
                        <Edit className="size-4 text-muted-foreground" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleToggleStatus(u)}
                        title={u.status === "ACTIVE" ? "Suspend Account" : "Activate Account"}
                        aria-label={`Toggle status for ${u.name}`}
                      >
                        {u.status === "ACTIVE" ? (
                          <UserX className="size-4 text-amber-500" />
                        ) : (
                          <UserCheck className="size-4 text-success" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => setDeleteTarget(u)}
                        title="Delete User"
                        aria-label={`Delete ${u.name}`}
                      >
                        <Trash2 className="size-4 text-destructive" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SectionCard>

      {/* Edit User Modal */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-md">
          {editingUser && (
            <form onSubmit={handleUpdateUser}>
              <DialogHeader>
                <DialogTitle>Edit User Account</DialogTitle>
                <DialogDescription>
                  Modify role permissions and contact details for {editingUser.name}.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-3 py-3">
                <div className="space-y-1">
                  <Label className="text-xs">Email</Label>
                  <Input value={editingUser.email} disabled className="bg-muted" />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="edit-role" className="text-xs">Assigned Role</Label>
                  <Select
                    value={editRole}
                    onValueChange={(v) => setEditRole(v as Role)}
                  >
                    <SelectTrigger id="edit-role">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(ROLE_LABELS).map(([k, v]) => (
                        <SelectItem key={k} value={k}>
                          {v}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1">
                  <Label htmlFor="edit-phone" className="text-xs">Update Phone</Label>
                  <Input
                    id="edit-phone"
                    value={editPhone}
                    onChange={(e) => setEditPhone(e.target.value)}
                    placeholder="New phone number"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setEditOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={updating}>
                  {updating ? "Saving..." : "Save Changes"}
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Alert Dialog */}
      <AlertDialog
        open={Boolean(deleteTarget)}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete User Account?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to permanently remove the account for{" "}
              <strong>{deleteTarget?.name}</strong> ({deleteTarget?.email})? This action cannot be
              undone and removes their system access.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              disabled={deleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleting ? "Deleting..." : "Delete Account"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </DashboardLayout>
  );
}
