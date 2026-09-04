import type { LinkProps } from "@tanstack/react-router";
import {
  Activity,
  BarChart3,
  Bell,
  Building2,
  CalendarHeart,
  ClipboardList,
  Droplets,
  FlaskConical,
  History,
  Hospital,
  LayoutDashboard,
  Mail,
  MapPin,
  MessageSquare,
  ScrollText,
  Settings,
  Siren,
  User,
  Users,
} from "lucide-react";
import type { Role } from "./types";

export interface NavItem {
  label: string;
  to: NonNullable<LinkProps["to"]>;
  icon: typeof LayoutDashboard;
}

export const ROLE_NAV: Record<Role, NavItem[]> = {
  SUPER_ADMIN: [
    { label: "Dashboard", to: "/app/dashboard", icon: LayoutDashboard },
    { label: "Nearby Map", to: "/app/map", icon: MapPin },
    { label: "Users", to: "/app/users", icon: Users },
    { label: "Email Management", to: "/app/emails", icon: Mail },
    { label: "Inventory", to: "/app/inventory", icon: Droplets },
    { label: "Blood Requests", to: "/app/requests", icon: ClipboardList },
    { label: "Emergency SOS", to: "/app/sos", icon: Siren },
    { label: "Blood Banks", to: "/app/blood-banks", icon: Building2 },
    { label: "Hospitals", to: "/app/hospitals", icon: Hospital },
    { label: "Review Moderation", to: "/app/reviews", icon: MessageSquare },
    { label: "Analytics", to: "/app/analytics", icon: BarChart3 },
    { label: "Audit Logs", to: "/app/audit-logs", icon: ScrollText },
    { label: "Notifications", to: "/app/notifications", icon: Bell },
    { label: "System Settings", to: "/app/settings", icon: Settings },
  ],
  BLOOD_BANK_ADMIN: [
    { label: "Dashboard", to: "/app/dashboard", icon: LayoutDashboard },
    { label: "Nearby Map", to: "/app/map", icon: MapPin },
    { label: "Inventory", to: "/app/inventory", icon: Droplets },
    { label: "Blood Requests", to: "/app/requests", icon: ClipboardList },
    { label: "Donation Camps", to: "/app/camps", icon: CalendarHeart },
    { label: "Donors", to: "/app/donors", icon: Users },
    { label: "Testing QC", to: "/app/tests", icon: FlaskConical },
    { label: "Emergency SOS", to: "/app/sos", icon: Siren },
    { label: "Notifications", to: "/app/notifications", icon: Bell },
    { label: "Analytics", to: "/app/analytics", icon: BarChart3 },
  ],
  HOSPITAL_STAFF: [
    { label: "Dashboard", to: "/app/dashboard", icon: LayoutDashboard },
    { label: "Nearby Map", to: "/app/map", icon: MapPin },
    { label: "Blood Requests", to: "/app/requests", icon: ClipboardList },
    { label: "Request History", to: "/app/request-history", icon: History },
    { label: "Notifications", to: "/app/notifications", icon: Bell },
    { label: "My Profile", to: "/app/profile", icon: User },
  ],
  LAB_TECHNICIAN: [
    { label: "Dashboard", to: "/app/dashboard", icon: LayoutDashboard },
    { label: "Nearby Map", to: "/app/map", icon: MapPin },
    { label: "Pending Tests", to: "/app/tests", icon: FlaskConical },
    { label: "Test History", to: "/app/test-history", icon: Activity },
    { label: "Notifications", to: "/app/notifications", icon: Bell },
    { label: "My Profile", to: "/app/profile", icon: User },
  ],
  DONOR: [
    { label: "Dashboard", to: "/app/dashboard", icon: LayoutDashboard },
    { label: "Nearby Map", to: "/app/map", icon: MapPin },
    { label: "My Profile", to: "/app/profile", icon: User },
    { label: "Donation History", to: "/app/donation-history", icon: History },
    { label: "Donation Camps", to: "/app/camps", icon: CalendarHeart },
    { label: "Notifications", to: "/app/notifications", icon: Bell },
  ],
};