import type { LucideIcon } from "lucide-react";
import { Compass, LayoutDashboard, Mail, Package, Users } from "lucide-react";

export interface NavItem {
  label: string;
  path: string;
  icon: LucideIcon;
  exact?: boolean;
}

export const NAV_ITEMS: readonly NavItem[] = [
  {
    label: "Dashboard",
    path: "/",
    icon: LayoutDashboard,
    exact: true,
  },
  {
    label: "Product Passport",
    path: "/products",
    icon: Package,
  },
  {
    label: "Market Discovery",
    path: "/discovery",
    icon: Compass,
  },
  {
    label: "Buyer Leads",
    path: "/leads",
    icon: Users,
  },
  {
    label: "Outreach Studio",
    path: "/outreach",
    icon: Mail,
  },
] as const;

