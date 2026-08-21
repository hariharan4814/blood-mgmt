import { useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Droplets } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState, TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { donorService, type DonationRecord } from "@/services/donors/donorService";

export const Route = createFileRoute("/app/donation-history")({
  head: () => ({
    meta: [
      { title: "Donation History — Blood Management System" },
      {
        name: "description",
        content: "Every donation you have made, including deferred visits and collected volume.",
      },
      { property: "og:title", content: "Donation History — Blood Management System" },
      { property: "og:description", content: "Your complete blood donation record." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: DonationHistoryPage,
});

function DonationHistoryPage() {
  const [history, setHistory] = useState<DonationRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const data = await donorService.getDonationHistory();
        setHistory(data);
      } catch (err) {
        toast.error(err instanceof Error ? err.message : "Failed to load donation history.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <DashboardLayout title="Donation History">
      <PageHeader
        title="Donation history"
        description="Your complete historical record of voluntary blood donations and facility collections."
      />
      <SectionCard bodyClassName="p-0">
        {loading ? (
          <TableSkeleton cols={5} />
        ) : history.length === 0 ? (
          <div className="p-6">
            <EmptyState
              icon={Droplets}
              title="No donation records found"
              description="Your completed donations at blood banks and donation camps will appear here."
            />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Reference</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Centre / Camp</TableHead>
                <TableHead>Volume</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {history.map((d) => (
                <TableRow key={d.id}>
                  <TableCell className="font-mono text-xs">{d.id}</TableCell>
                  <TableCell>{new Date(d.date).toLocaleDateString()}</TableCell>
                  <TableCell className="font-medium">{d.center}</TableCell>
                  <TableCell>{d.volumeMl ? `${d.volumeMl} ml` : "—"}</TableCell>
                  <TableCell>
                    <StatusBadge status={d.status === "COMPLETED" ? "COMPLETED" : "REVIEW"} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SectionCard>
    </DashboardLayout>
  );
}
