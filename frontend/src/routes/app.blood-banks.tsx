import { useState, useEffect } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  Building2,
  Droplets,
  Edit2,
  Eye,
  Loader2,
  Mail,
  MapPin,
  Phone,
  Plus,
  Power,
  Search,
  Star,
  Warehouse,
} from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ReviewDialog } from "@/components/reviews/ReviewDialog";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/providers/AuthProvider";
import { facilityService, type BloodBankFacility, type BloodBankInput } from "@/services/facilities/facilityService";
import { reviewService, type ReviewItem } from "@/services/reviews/reviewService";

export const Route = createFileRoute("/app/blood-banks")({
  head: () => ({
    meta: [
      { title: "Blood Banks — Blood Management System" },
      { name: "description", content: "Registered blood banks, capacity, inventory, and facility management." },
      { property: "og:title", content: "Blood Banks — Blood Management System" },
      { property: "og:description", content: "Registered blood banks and facilities." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: BloodBanksPage,
});

function BloodBanksPage() {
  const { user: currentUser } = useAuth();
  const isSuperAdmin = currentUser?.role === "SUPER_ADMIN";
  const isBloodBankAdmin = currentUser?.role === "BLOOD_BANK_ADMIN";

  const [bloodBanks, setBloodBanks] = useState<BloodBankFacility[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  // Add / Edit Modal state
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [editingBank, setEditingBank] = useState<BloodBankFacility | null>(null);
  const [formData, setFormData] = useState<BloodBankInput>({
    name: "",
    address: "",
    city: "",
    state: "",
    contact_number: "",
    email: "",
    capacity: 500,
    latitude: null,
    longitude: null,
    is_active: true,
  });
  const [saving, setSaving] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Detail Sheet state
  const [detailOpen, setDetailOpen] = useState<boolean>(false);
  const [selectedBank, setSelectedBank] = useState<BloodBankFacility | null>(null);
  const [bankReviews, setBankReviews] = useState<ReviewItem[]>([]);
  const [loadingReviews, setLoadingReviews] = useState<boolean>(false);

  // Review Dialog state
  const [reviewDialogOpen, setReviewDialogOpen] = useState<boolean>(false);

  const fetchBloodBanks = async () => {
    try {
      setLoading(true);
      const data = await facilityService.getBloodBanks({
        search: search.trim() || undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
      });
      setBloodBanks(data);
    } catch (err: any) {
      toast.error(err?.message || "Failed to load blood banks.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBloodBanks();
  }, [statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchBloodBanks();
  };

  const openCreateModal = () => {
    setEditingBank(null);
    setFormData({
      name: "",
      address: "",
      city: "",
      state: "",
      contact_number: "",
      email: "",
      capacity: 500,
      latitude: null,
      longitude: null,
      is_active: true,
    });
    setFormError(null);
    setModalOpen(true);
  };

  const openEditModal = (bank: BloodBankFacility) => {
    setEditingBank(bank);
    setFormData({
      name: bank.name,
      address: bank.address,
      city: bank.city,
      state: bank.state,
      contact_number: bank.contact_number,
      email: bank.email,
      capacity: bank.capacity,
      latitude: bank.latitude,
      longitude: bank.longitude,
      is_active: bank.is_active,
    });
    setFormError(null);
    setModalOpen(true);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.city.trim() || !formData.contact_number?.trim() || !formData.email?.trim()) {
      setFormError("Name, City, Contact Number, and Email are required fields.");
      return;
    }

    setSaving(true);
    setFormError(null);

    try {
      if (editingBank) {
        await facilityService.updateBloodBank(editingBank.id, formData);
        toast.success(`Blood Bank "${formData.name}" updated successfully.`);
      } else {
        await facilityService.createBloodBank(formData);
        toast.success(`Blood Bank "${formData.name}" registered successfully.`);
      }
      setModalOpen(false);
      fetchBloodBanks();
    } catch (err: any) {
      setFormError(err?.message || "Failed to save blood bank.");
      toast.error(err?.message || "Failed to save blood bank.");
    } finally {
      setSaving(false);
    }
  };

  const handleToggleActive = async (bank: BloodBankFacility) => {
    const nextStatus = !bank.is_active;
    try {
      await facilityService.updateBloodBank(bank.id, { is_active: nextStatus });
      toast.success(`Blood Bank "${bank.name}" ${nextStatus ? "activated" : "deactivated"}.`);
      fetchBloodBanks();
    } catch (err: any) {
      toast.error(err?.message || "Failed to update blood bank status.");
    }
  };

  const openDetails = async (bank: BloodBankFacility) => {
    setSelectedBank(bank);
    setDetailOpen(true);
    setLoadingReviews(true);

    try {
      const reviews = await reviewService.getReviews({
        blood_bank: bank.id,
        status: "APPROVED",
      });
      setBankReviews(reviews);
    } catch (err) {
      console.error(err);
      setBankReviews([]);
    } finally {
      setLoadingReviews(false);
    }
  };

  return (
    <DashboardLayout title="Blood Banks">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
        <PageHeader
          title="Blood Banks"
          description="Manage storage facilities, licensed capacity, ratings, and active operational status."
        />
        {isSuperAdmin && (
          <Button onClick={openCreateModal} className="bg-primary gap-2 shrink-0">
            <Plus className="h-4 w-4" />
            Add Blood Bank
          </Button>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between bg-card p-4 rounded-lg border">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by blood bank name, city, or address..."
            className="pl-9"
          />
        </form>

        <div className="flex items-center gap-3">
          <Label className="text-xs text-muted-foreground whitespace-nowrap">Status:</Label>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[130px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="active">Active only</SelectItem>
              <SelectItem value="inactive">Inactive only</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Blood Bank Table */}
      <SectionCard bodyClassName="p-0">
        {loading ? (
          <TableSkeleton cols={6} />
        ) : bloodBanks.length === 0 ? (
          <div className="py-12 text-center text-muted-foreground">
            <Building2 className="mx-auto h-12 w-12 opacity-30 mb-2" />
            <p className="text-base font-medium">No blood banks found</p>
            <p className="text-sm mt-1">Try adjusting your search criteria or add a new blood bank.</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Facility Name</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Capacity</TableHead>
                <TableHead>Inventory Units</TableHead>
                <TableHead>Rating</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {bloodBanks.map((b) => {
                const canEdit = isSuperAdmin || (isBloodBankAdmin && b.admin_id === currentUser?.id);

                return (
                  <TableRow key={b.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <Building2 className="h-4 w-4 text-primary shrink-0" />
                        <div>
                          <span>{b.name}</span>
                          {b.contact_number && (
                            <div className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                              <Phone className="h-3 w-3" />
                              <span>{b.contact_number}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {b.city}
                        {b.state ? `, ${b.state}` : ""}
                      </div>
                      {b.latitude && b.longitude && (
                        <div className="text-xs font-mono text-muted-foreground">
                          {Number(b.latitude).toFixed(4)}, {Number(b.longitude).toFixed(4)}
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <span className="font-semibold text-sm">{b.capacity}</span>
                      <span className="text-xs text-muted-foreground ml-1">units</span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <Droplets className="h-3.5 w-3.5 text-primary" />
                        <span className="font-semibold text-sm">{b.total_units_count}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {typeof b.average_rating === "number" ? (
                        <div className="flex items-center gap-1.5">
                          <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                          <span className="font-medium text-sm">{b.average_rating.toFixed(1)}</span>
                          <span className="text-xs text-muted-foreground">({b.review_count})</span>
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground italic">No ratings</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={b.is_active ? "ACTIVE" : "INACTIVE"} />
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openDetails(b)}
                          title="View details & reviews"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        {canEdit && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openEditModal(b)}
                            title="Edit blood bank"
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                        )}
                        {isSuperAdmin && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleToggleActive(b)}
                            title={b.is_active ? "Deactivate" : "Activate"}
                            className={b.is_active ? "text-destructive hover:text-destructive" : "text-emerald-600 hover:text-emerald-700"}
                          >
                            <Power className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </SectionCard>

      {/* Add / Edit Blood Bank Dialog */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="sm:max-w-[540px]">
          <form onSubmit={handleFormSubmit}>
            <DialogHeader>
              <DialogTitle>{editingBank ? "Edit Blood Bank" : "Add Blood Bank Facility"}</DialogTitle>
              <DialogDescription>
                Configure location, contact information, and storage capacity parameters.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4 max-h-[65vh] overflow-y-auto px-1">
              {formError && (
                <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
                  {formError}
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="b-name">Blood Bank Name *</Label>
                <Input
                  id="b-name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Metro Blood Bank & Component Lab"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor="b-city">City *</Label>
                  <Input
                    id="b-city"
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    placeholder="e.g. Chennai"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="b-state">State / Province *</Label>
                  <Input
                    id="b-state"
                    value={formData.state || ""}
                    onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                    placeholder="e.g. Tamil Nadu"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="b-address">Physical Street Address</Label>
                <Textarea
                  id="b-address"
                  value={formData.address || ""}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  placeholder="Street name, landmark, postal code"
                  rows={2}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor="b-contact">Contact Number *</Label>
                  <Input
                    id="b-contact"
                    value={formData.contact_number || ""}
                    onChange={(e) => setFormData({ ...formData, contact_number: e.target.value })}
                    placeholder="+91-..."
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="b-email">Official Email *</Label>
                  <Input
                    id="b-email"
                    type="email"
                    value={formData.email || ""}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="contact@bloodbank.org"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="b-capacity">Storage Capacity (Units) *</Label>
                <Input
                  id="b-capacity"
                  type="number"
                  min={0}
                  value={formData.capacity ?? 500}
                  onChange={(e) => setFormData({ ...formData, capacity: parseInt(e.target.value, 10) || 0 })}
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor="b-lat">Latitude (-90 to 90)</Label>
                  <Input
                    id="b-lat"
                    type="number"
                    step="0.000001"
                    min={-90}
                    max={90}
                    value={formData.latitude ?? ""}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        latitude: e.target.value ? parseFloat(e.target.value) : null,
                      })
                    }
                    placeholder="13.0827"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="b-lng">Longitude (-180 to 180)</Label>
                  <Input
                    id="b-lng"
                    type="number"
                    step="0.000001"
                    min={-180}
                    max={180}
                    value={formData.longitude ?? ""}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        longitude: e.target.value ? parseFloat(e.target.value) : null,
                      })
                    }
                    placeholder="80.2707"
                  />
                </div>
              </div>

              {isSuperAdmin && (
                <div className="flex items-center justify-between pt-2 border-t">
                  <div className="space-y-0.5">
                    <Label>Active Status</Label>
                    <p className="text-xs text-muted-foreground">
                      Inactive blood banks cannot accept donations or dispatch units.
                    </p>
                  </div>
                  <Switch
                    checked={Boolean(formData.is_active)}
                    onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                  />
                </div>
              )}
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={saving}>
                {saving ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : editingBank ? (
                  "Save Changes"
                ) : (
                  "Create Blood Bank"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Blood Bank Detail Drawer */}
      <Sheet open={detailOpen} onOpenChange={setDetailOpen}>
        <SheetContent className="w-full sm:max-w-md overflow-y-auto">
          {selectedBank && (
            <div className="space-y-6 pt-4">
              <SheetHeader>
                <div className="flex items-center gap-2">
                  <Building2 className="h-6 w-6 text-primary shrink-0" />
                  <div>
                    <SheetTitle>{selectedBank.name}</SheetTitle>
                    <SheetDescription>
                      {selectedBank.city}, {selectedBank.state}
                    </SheetDescription>
                  </div>
                </div>
              </SheetHeader>

              {/* Status & Rating Banner */}
              <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <div>
                  <div className="text-xs text-muted-foreground">Rating</div>
                  <div className="flex items-center gap-1 mt-0.5">
                    <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                    <span className="font-bold text-sm">
                      {typeof selectedBank.average_rating === "number"
                        ? selectedBank.average_rating.toFixed(1)
                        : "No ratings"}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      ({selectedBank.review_count} approved)
                    </span>
                  </div>
                </div>
                <StatusBadge status={selectedBank.is_active ? "ACTIVE" : "INACTIVE"} />
              </div>

              {/* Details List */}
              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-muted-foreground">Address:</span>
                  <p className="font-medium mt-0.5">{selectedBank.address || "Not specified"}</p>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <span className="text-muted-foreground">Contact:</span>
                    <p className="font-medium mt-0.5">{selectedBank.contact_number}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Storage Capacity:</span>
                    <p className="font-medium mt-0.5">{selectedBank.capacity} units</p>
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground">Current Available Stock:</span>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <Droplets className="h-4 w-4 text-primary" />
                    <span className="font-bold text-sm">{selectedBank.total_units_count} units</span>
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground">Email:</span>
                  <p className="font-medium mt-0.5">{selectedBank.email}</p>
                </div>
                {selectedBank.admin_username && (
                  <div>
                    <span className="text-muted-foreground">Assigned Administrator:</span>
                    <p className="font-medium mt-0.5">{selectedBank.admin_username}</p>
                  </div>
                )}
                {selectedBank.latitude && selectedBank.longitude && (
                  <div>
                    <span className="text-muted-foreground">Coordinates:</span>
                    <p className="font-mono text-xs mt-0.5">
                      {selectedBank.latitude}, {selectedBank.longitude}
                    </p>
                  </div>
                )}
              </div>

              {/* Reviews Section */}
              <div className="pt-4 border-t space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-sm">Approved Reviews</h4>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setReviewDialogOpen(true)}
                    className="gap-1.5"
                  >
                    <Star className="h-3.5 w-3.5" />
                    Write Review
                  </Button>
                </div>

                {loadingReviews ? (
                  <div className="py-4 text-center">
                    <Loader2 className="h-5 w-5 animate-spin mx-auto text-muted-foreground" />
                  </div>
                ) : bankReviews.length === 0 ? (
                  <p className="text-xs text-muted-foreground py-4 text-center italic">
                    No approved reviews yet. Be the first to share your experience!
                  </p>
                ) : (
                  <div className="space-y-3">
                    {bankReviews.map((r) => (
                      <div key={r.id} className="p-3 rounded-lg border bg-card/60 space-y-1.5 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold">{r.reviewer.full_name || r.reviewer.username}</span>
                          <div className="flex items-center text-amber-500">
                            {Array.from({ length: r.rating }).map((_, i) => (
                              <Star key={i} className="h-3 w-3 fill-current" />
                            ))}
                          </div>
                        </div>
                        <p className="text-muted-foreground leading-relaxed">{r.comment}</p>
                        <span className="text-[10px] text-muted-foreground/60 block">
                          {new Date(r.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>

      {/* Write Review Dialog */}
      {selectedBank && (
        <ReviewDialog
          open={reviewDialogOpen}
          onOpenChange={setReviewDialogOpen}
          targetType="blood_bank"
          targetId={selectedBank.id}
          targetName={selectedBank.name}
          onSubmitted={() => {
            fetchBloodBanks();
            if (selectedBank) openDetails(selectedBank);
          }}
        />
      )}
    </DashboardLayout>
  );
}
