"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  Activity,
  BarChart3,
  Calendar,
  Cog,
  Flag,
  GraduationCap,
  LayoutDashboard,
  MessageSquare,
  Phone,
  PhoneCall,
  Users,
} from "lucide-react";

const NAV = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/calls", label: "Calls", icon: PhoneCall },
  { href: "/messages", label: "Messages", icon: MessageSquare },
  { href: "/appointments", label: "Appointments", icon: Calendar },
  { href: "/contacts", label: "Contacts", icon: Users },
  { href: "/knowledge", label: "Knowledge", icon: GraduationCap },
  { href: "/config", label: "Agent Config", icon: Cog },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/quality", label: "Quality", icon: Flag },
  { href: "/settings", label: "Settings", icon: Activity },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-60 shrink-0 border-r bg-card md:block">
      <div className="flex h-16 items-center border-b px-6">
        <Phone className="mr-2 h-5 w-5" />
        <span className="text-lg font-semibold">Receptionist</span>
      </div>
      <nav className="space-y-1 p-3">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors",
                active
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-accent hover:text-accent-foreground",
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}