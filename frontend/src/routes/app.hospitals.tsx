import { useState, useEffect } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  Building2,
  CheckCircle2,
  Edit2,
  Eye,
  Hospital as HospitalIcon,
  Loader2,
  MapPin,
  Phone,
  Plus,
  Power,
  Search,
  Star,
  XCircle,
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
import { facilityService, type HospitalFacility, type HospitalInput } from "@/services/facilities/facilityService";
import { reviewService, type ReviewItem } from "@/services/reviews/reviewService";

export const Route = createFileRoute("/app/hospitals")({
  head: () => ({
    meta: [
      { title: "Hospitals — Blood Management System" },
      { name: "description", content: "Partner hospitals, bed capacity and facility management." },
      { property: "og:title", content: "Hospitals — Blood Management System" },
      { property: "og:description", content: "Partner hospitals and facilities." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: HospitalsPage,
});

function HospitalsPage() {
  const { user: currentUser } = useAuth();
  const isSuperAdmin = currentUser?.role === "SUPER_ADMIN";

  const [hospitals, setHospitals] = useState<HospitalFacility[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  // Add / Edit Modal state
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [editingHospital, setEditingHospital] = useState<HospitalFacility | null>(null);
  const [formData, setFormData] = useState<HospitalInput>({
    name: "",
    address: "",
    city: "",
    state: "",
    contact_number: "",
    email: "",
    beds: 0,
    latitude: null,
    longitude: null,
    is_active: true,
  });
  const [saving, setSaving] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Detail Sheet state
  const [detailOpen, setDetailOpen] = useState<boolean>(false);
  const [selectedHospital, setSelectedHospital] = useState<HospitalFacility | null>(null);
  const [hospitalReviews, setHospitalReviews] = useState<ReviewItem[]>([]);
  const [loadingReviews, setLoadingReviews] = useState<boolean>(false);

  // Review Dialog state
  const [reviewDialogOpen, setReviewDialogOpen] = useState<boolean>(false);

  const fetchHospitals = async () => {
    try {
      setLoading(true);
      const data = await facilityService.getHospitals({
        search: search.trim() || undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
      });
      setHospitals(data);
    } catch (err: any) {
      toast.error(err?.message || "Failed to load hospitals.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHospitals();
  }, [statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchHospitals();
  };

  const openCreateModal = () => {
    setEditingHospital(null);
    setFormData({
      name: "",
      address: "",
      city: "",
      state: "",
      contact_number: "",
      email: "",
      beds: 0,
      latitude: null,
      longitude: null,
      is_active: true,
    });
    setFormError(null);
    setModalOpen(true);
  };

  const openEditModal = (hospital: HospitalFacility) => {
    setEditingHospital(hospital);
    setFormData({
      name: hospital.name,
      address: hospital.address,
      city: hospital.city,
      state: hospital.state,
      contact_number: hospital.contact_number,
      email: hospital.email,
      beds: hospital.beds,
      latitude: hospital.latitude,
      longitude: hospital.longitude,
      is_active: hospital.is_active,
    });
    setFormError(null);
    setModalOpen(true);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.city.trim()) {
      setFormError("Name and City are required fields.");
      return;
    }

    setSaving(true);
    setFormError(null);

    try {
      if (editingHospital) {
        await facilityService.updateHospital(editingHospital.id, formData);
        toast.success(`Hospital "${formData.name}" updated successfully.`);
      } else {
        await facilityService.createHospital(formData);
        toast.success(`Hospital "${formData.name}" registered successfully.`);
      }
      setModalOpen(false);
      fetchHospitals();
    } catch (err: any) {
      setFormError(err?.message || "Failed to save hospital.");
      toast.error(err?.message || "Failed to save hospital.");
    } finally {
      setSaving(false);
    }
  };

  const handleToggleActive = async (hospital: HospitalFacility) => {
    const nextStatus = !hospital.is_active;
    try {
      await facilityService.updateHospital(hospital.id, { is_active: nextStatus });
      toast.success(`Hospital "${hospital.name}" ${nextStatus ? "activated" : "deactivated"}.`);
      fetchHospitals();
    } catch (err: any) {
      toast.error(err?.message || "Failed to update hospital status.");
    }
  };

  const openDetails = async (hospital: HospitalFacility) => {
    setSelectedHospital(hospital);
    setDetailOpen(true);
    setLoadingReviews(true);

    try {
      const reviews = await reviewService.getReviews({
        hospital: hospital.id,
        status: "APPROVED",
      });
      setHospitalReviews(reviews);
    } catch (err) {
      console.error(err);
      setHospitalReviews([]);
    } finally {
      setLoadingReviews(false);
    }
  };

  return (
    <DashboardLayout title="Hospitals">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
        <PageHeader
          title="Hospitals"
          description="Manage partner hospital facilities, locations, capacity, and ratings."
        />
        {isSuperAdmin && (
          <Button onClick={openCreateModal} className="bg-primary gap-2 shrink-0">
            <Plus className="h-4 w-4" />
            Add Hospital
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
            placeholder="Search by hospital name, city, or address..."
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

      {/* Hospital Table */}
      <SectionCard bodyClassName="p-0">
        {loading ? (
          <TableSkeleton cols={6} />
        ) : hospitals.length === 0 ? (
          <div className="py-12 text-center text-muted-foreground">
            <HospitalIcon className="mx-auto h-12 w-12 opacity-30 mb-2" />
            <p className="text-base font-medium">No hospitals found</p>
            <p className="text-sm mt-1">Try adjusting your search criteria or add a new hospital.</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Hospital Name</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Beds</TableHead>
                <TableHead>Rating</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {hospitals.map((h) => (
                <TableRow key={h.id}>
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      <HospitalIcon className="h-4 w-4 text-primary shrink-0" />
                      <div>
                        <span>{h.name}</span>
                        {h.contact_number && (
                          <div className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                            <Phone className="h-3 w-3" />
                            <span>{h.contact_number}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">
                      {h.city}
                      {h.state ? `, ${h.state}` : ""}
                    </div>
                    {h.latitude && h.longitude && (
                      <div className="text-xs font-mono text-muted-foreground">
                        {Number(h.latitude).toFixed(4)}, {Number(h.longitude).toFixed(4)}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    <span className="font-semibold text-sm">{h.beds}</span>
                    <span className="text-xs text-muted-foreground ml-1">beds</span>
                  </TableCell>
                  <TableCell>
                    {typeof h.average_rating === "number" ? (
                      <div className="flex items-center gap-1.5">
                        <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                        <span className="font-medium text-sm">{h.average_rating.toFixed(1)}</span>
                        <span className="text-xs text-muted-foreground">({h.review_count})</span>
                      </div>
                    ) : (
                      <span className="text-xs text-muted-foreground italic">No ratings</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={h.is_active ? "ACTIVE" : "INACTIVE"} />
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openDetails(h)}
                        title="View details & reviews"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      {isSuperAdmin && (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openEditModal(h)}
                            title="Edit hospital"
                          >
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleToggleActive(h)}
                            title={h.is_active ? "Deactivate" : "Activate"}
                            className={h.is_active ? "text-destructive hover:text-destructive" : "text-emerald-600 hover:text-emerald-700"}
                          >
                            <Power className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SectionCard>

      {/* Add / Edit Hospital Dialog */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="sm:max-w-[540px]">
          <form onSubmit={handleFormSubmit}>
            <DialogHeader>
              <DialogTitle>{editingHospital ? "Edit Hospital" : "Add Partner Hospital"}</DialogTitle>
              <DialogDescription>
                Provide clinical and location parameters for the partner hospital facility.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4 max-h-[65vh] overflow-y-auto px-1">
              {formError && (
                <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
                  {formError}
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="h-name">Hospital Name *</Label>
                <Input
                  id="h-name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. City General Hospital"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor="h-city">City *</Label>
                  <Input
                    id="h-city"
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    placeholder="e.g. Chennai"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="h-state">State / Province</Label>
                  <Input
                    id="h-state"
                    value={formData.state || ""}
                    onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                    placeholder="e.g. Tamil Nadu"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="h-address">Physical Street Address</Label>
                <Textarea
                  id="h-address"
                  value={formData.address || ""}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  placeholder="Street name, landmark, postal code"
                  rows={2}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor="h-contact">Emergency / Phone</Label>
                  <Input
                    id="h-contact"
                    value={formData.contact_number || ""}
                    onChange={(e) => setFormData({ ...formData, contact_number: e.target.value })}
                    placeholder="+91-..."
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="h-email">Official Email</Label>
                  <Input
                    id="h-email"
                    type="email"
                    value={formData.email || ""}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="contact@hospital.org"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="h-beds">Inpatient Bed Capacity</Label>
                <Input
                  id="h-beds"
                  type="number"
                  min={0}
                  value={formData.beds ?? 0}
                  onChange={(e) => setFormData({ ...formData, beds: parseInt(e.target.value, 10) || 0 })}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor="h-lat">Latitude (-90 to 90)</Label>
                  <Input
                    id="h-lat"
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
                  <Label htmlFor="h-lng">Longitude (-180 to 180)</Label>
                  <Input
                    id="h-lng"
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

              <div className="flex items-center justify-between pt-2 border-t">
                <div className="space-y-0.5">
                  <Label>Active Status</Label>
                  <p className="text-xs text-muted-foreground">
                    Inactive facilities will not appear as active nearby resources.
                  </p>
                </div>
                <Switch
                  checked={Boolean(formData.is_active)}
                  onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                />
              </div>
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
                ) : editingHospital ? (
                  "Save Changes"
                ) : (
                  "Create Hospital"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Hospital Detail Drawer */}
      <Sheet open={detailOpen} onOpenChange={setDetailOpen}>
        <SheetContent className="w-full sm:max-w-md overflow-y-auto">
          {selectedHospital && (
            <div className="space-y-6 pt-4">
              <SheetHeader>
                <div className="flex items-center gap-2">
                  <HospitalIcon className="h-6 w-6 text-primary shrink-0" />
                  <div>
                    <SheetTitle>{selectedHospital.name}</SheetTitle>
                    <SheetDescription>
                      {selectedHospital.city}, {selectedHospital.state || ""}
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
                      {typeof selectedHospital.average_rating === "number"
                        ? selectedHospital.average_rating.toFixed(1)
                        : "No ratings"}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      ({selectedHospital.review_count} approved)
                    </span>
                  </div>
                </div>
                <StatusBadge status={selectedHospital.is_active ? "ACTIVE" : "INACTIVE"} />
              </div>

              {/* Details List */}
              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-muted-foreground">Address:</span>
                  <p className="font-medium mt-0.5">{selectedHospital.address || "Not specified"}</p>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <span className="text-muted-foreground">Contact:</span>
                    <p className="font-medium mt-0.5">{selectedHospital.contact_number || "—"}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Bed Capacity:</span>
                    <p className="font-medium mt-0.5">{selectedHospital.beds} approved beds</p>
                  </div>
                </div>
                {selectedHospital.email && (
                  <div>
                    <span className="text-muted-foreground">Email:</span>
                    <p className="font-medium mt-0.5">{selectedHospital.email}</p>
                  </div>
                )}
                {selectedHospital.latitude && selectedHospital.longitude && (
                  <div>
                    <span className="text-muted-foreground">Coordinates:</span>
                    <p className="font-mono text-xs mt-0.5">
                      {selectedHospital.latitude}, {selectedHospital.longitude}
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
                ) : hospitalReviews.length === 0 ? (
                  <p className="text-xs text-muted-foreground py-4 text-center italic">
                    No approved reviews yet. Be the first to share your experience!
                  </p>
                ) : (
                  <div className="space-y-3">
                    {hospitalReviews.map((r) => (
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
      {selectedHospital && (
        <ReviewDialog
          open={reviewDialogOpen}
          onOpenChange={setReviewDialogOpen}
          targetType="hospital"
          targetId={selectedHospital.id}
          targetName={selectedHospital.name}
          onSubmitted={() => {
            fetchHospitals();
            if (selectedHospital) openDetails(selectedHospital);
          }}
        />
      )}
    </DashboardLayout>
  );
}
