import { useEffect, useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  AlertTriangle,
  Bell,
  CalendarHeart,
  ClipboardList,
  Droplets,
  Settings2,
} from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { SectionCard } from "@/components/common/SectionCard";
import { EmptyState, TableSkeleton } from "@/components/common/StateBlocks";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import type { Notification } from "@/lib/types";
import { notificationService } from "@/services/notifications/notificationService";

export const Route = createFileRoute("/app/notifications")({
  head: () => ({
    meta: [
      { title: "Notifications — Blood Management System" },
      {
        name: "description",
        content: "Emergency, request, inventory and camp alerts delivered to your role inbox.",
      },
      { property: "og:title", content: "Notifications — Blood Management System" },
      { property: "og:description", content: "Emergency, request, inventory and camp alerts." },
      { name: "robots", content: "noindex" },
    ],
  }),
  component: NotificationsPage,
});

const ICONS = {
  EMERGENCY: AlertTriangle,
  REQUEST: ClipboardList,
  INVENTORY: Droplets,
  CAMP: CalendarHeart,
  SYSTEM: Settings2,
} as const;

function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("ALL");

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const data = await notificationService.list();
      setNotifications(data);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load notifications.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, []);

  const filtered = useMemo(
    () =>
      tab === "ALL"
        ? notifications
        : tab === "UNREAD"
          ? notifications.filter((n) => !n.read)
          : notifications.filter((n) => n.category === tab),
    [notifications, tab],
  );

  const markAll = async () => {
    try {
      await notificationService.markAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      toast.success("All notifications marked as read.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to mark all as read.");
    }
  };

  const toggle = async (id: string, currentlyRead: boolean) => {
    if (currentlyRead) return;
    try {
      await notificationService.markRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true } : n)),
      );
    } catch {
      // ignore
    }
  };

  return (
    <DashboardLayout title="Notifications">
      <PageHeader
        title="Notifications"
        description="Important emergency, request, inventory, and camp alerts delivered to your inbox."
        actions={
          <Button variant="outline" onClick={markAll}>
            Mark all as read
          </Button>
        }
      />

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          {["ALL", "UNREAD", "EMERGENCY", "REQUEST", "INVENTORY", "CAMP", "SYSTEM"].map((t) => (
            <TabsTrigger key={t} value={t}>
              {t.charAt(0) + t.slice(1).toLowerCase()}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <SectionCard bodyClassName="p-0">
        {loading ? (
          <TableSkeleton cols={2} />
        ) : filtered.length === 0 ? (
          <div className="p-5">
            <EmptyState icon={Bell} title="Nothing here" description="You're all caught up in this category." />
          </div>
        ) : (
          <ul className="divide-y divide-border">
            {filtered.map((n) => {
              const Icon = ICONS[n.category] || Bell;
              return (
                <li key={n.id}>
                  <button
                    type="button"
                    onClick={() => toggle(n.id, n.read)}
                    className={cn(
                      "flex w-full items-start gap-4 px-5 py-4 text-left transition-colors hover:bg-muted/50",
                      !n.read && "bg-primary/4",
                    )}
                  >
                    <span
                      className={cn(
                        "mt-0.5 grid size-9 shrink-0 place-items-center rounded-lg",
                        n.category === "EMERGENCY"
                          ? "bg-destructive/12 text-destructive"
                          : "bg-muted text-muted-foreground",
                      )}
                    >
                      <Icon className="size-4" />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center gap-2">
                        <span className="truncate font-medium">{n.title}</span>
                        {!n.read ? (
                          <span className="size-2 shrink-0 rounded-full bg-primary" aria-label="Unread" />
                        ) : null}
                      </span>
                      <span className="mt-0.5 block text-sm text-muted-foreground">{n.body}</span>
                      <span className="mt-1 block text-xs text-muted-foreground">
                        {new Date(n.createdAt).toLocaleString()} · {n.category.toLowerCase()}
                      </span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </SectionCard>
    </DashboardLayout>
  );
}
