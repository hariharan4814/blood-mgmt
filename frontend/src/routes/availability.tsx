import { useState } from "react";
import { Link, createFileRoute } from "@tanstack/react-router";
import { Search } from "lucide-react";
import { PublicLayout } from "@/components/layout/PublicLayout";
import { BloodGroupTile } from "@/components/common/BloodGroupTile";
import { EmptyState } from "@/components/common/StateBlocks";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { bloodBanks, publicAvailability } from "@/services/mock/data";

export const Route = createFileRoute("/availability")({
  head: () => ({
    meta: [
      { title: "Blood Availability — Blood Management System" },
      {
        name: "description",
        content:
          "Browse indicative blood group availability across partner blood banks and see which groups are running low.",
      },
      { property: "og:title", content: "Blood Availability" },
      {
        property: "og:description",
        content: "Indicative blood group stock levels across partner blood banks.",
      },
    ],
  }),
  component: AvailabilityPage,
});

function AvailabilityPage() {
  const [query, setQuery] = useState("");
  const banks = bloodBanks.filter(
    (b) =>
      b.name.toLowerCase().includes(query.toLowerCase()) ||
      b.city.toLowerCase().includes(query.toLowerCase()),
  );

  return (
    <PublicLayout>
      <div className="mx-auto max-w-6xl space-y-10 px-4 py-12">
        <header>
          <h1 className="text-3xl font-semibold tracking-tight">Blood availability</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Indicative stock levels from demo data. Levels are recalculated against each group's safe
            threshold — always confirm with the blood bank before travelling.
          </p>
        </header>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {publicAvailability.map((g) => (
            <BloodGroupTile key={g.group} group={g.group} units={g.units} level={g.level} />
          ))}
        </div>

        <section className="card-surface overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-4">
            <h2 className="font-semibold tracking-tight">Partner blood banks</h2>
            <div className="relative">
              <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search by name or city"
                className="w-full pl-9 sm:w-64"
              />
            </div>
          </div>
          {banks.length === 0 ? (
            <EmptyState
              title="No blood banks match that search"
              description="Try a different city or clear the search field."
              action={{ label: "Clear search", onClick: () => setQuery("") }}
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Blood bank</TableHead>
                  <TableHead>City</TableHead>
                  <TableHead>Licence</TableHead>
                  <TableHead className="text-right">Units in stock</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {banks.map((b) => (
                  <TableRow key={b.id}>
                    <TableCell className="font-medium">{b.name}</TableCell>
                    <TableCell>{b.city}</TableCell>
                    <TableCell className="text-muted-foreground">{b.license}</TableCell>
                    <TableCell className="text-right">{b.units}</TableCell>
                    <TableCell>
                      <StatusBadge status={b.status} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </section>

        <div className="card-surface flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="font-semibold tracking-tight">Can't find your blood group?</h2>
            <p className="text-sm text-muted-foreground">
              Register as a donor and we'll alert you when your group is needed nearby.
            </p>
          </div>
          <Button asChild>
            <Link to="/register">Become a Donor</Link>
          </Button>
        </div>
      </div>
    </PublicLayout>
  );
}