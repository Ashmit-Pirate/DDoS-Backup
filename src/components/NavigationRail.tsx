"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSage } from "@/lib/store";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { 
  LayoutDashboard, 
  Activity, 
  ScanSearch, 
  ShieldCheck, 
  TriangleAlert, 
  ScrollText,
  FlaskConical,
  Settings2,
  Menu,
  X
} from "lucide-react";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const navItems = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/live-traffic", label: "Live Traffic", icon: Activity },
  { href: "/detection", label: "Detection", icon: ScanSearch },
  { href: "/mitigation", label: "Mitigation", icon: ShieldCheck },
  { href: "/incidents", label: "Incidents", icon: TriangleAlert },
  { href: "/logs", label: "Logs", icon: ScrollText },
];

export default function NavigationRail() {
  const pathname = usePathname();
  const { state } = useSage();
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsOpen(false);
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, []);

  const closeDrawer = () => setIsOpen(false);

  const getStatusColor = () => {
    switch (state) {
      case "NORMAL":
      case "RECOVERED":
        return "bg-[var(--status-healthy)]";
      case "ATTACK_DETECTED":
      case "CLASSIFIED":
        return "bg-[var(--status-attack)] shadow-[0_0_8px_var(--status-attack)] animate-pulse";
      case "MITIGATING":
      case "RECOVERING":
        return "bg-[var(--status-warning)]";
      default:
        return "bg-[var(--muted-foreground)]";
    }
  };

  const statusLabel = state.replace("_", " ");

  return (
    <>
      {/* Mobile Top Bar */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-[72px] bg-[var(--surface-primary)] border-b border-[var(--border)] z-40 flex items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="p-2 -ml-2 text-[var(--foreground)] hover:bg-[var(--surface-secondary)] rounded-md transition-colors"
            aria-label="Toggle Menu"
            aria-expanded={isOpen}
            aria-controls="mobile-navigation"
          >
            {isOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
          <div className="flex flex-col">
            <h1 className="font-serif text-[22px] font-normal leading-none text-[var(--foreground)] tracking-tight">SAGE</h1>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className={cn("w-2.5 h-2.5 rounded-full flex-shrink-0 border border-white/20 shadow-sm", getStatusColor())} />
        </div>
      </div>

      {/* Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
          onClick={closeDrawer}
          aria-hidden="true"
        />
      )}

      {/* Sidebar / Drawer */}
      <div 
        id="mobile-navigation"
        className={cn(
          "fixed inset-y-0 left-0 z-50 h-full w-[280px] bg-[var(--surface-primary)] border-r border-[var(--border)] flex flex-col flex-shrink-0 transition-transform duration-300 ease-in-out",
          "lg:relative lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Brand (Desktop only visually, or keep in drawer if desired) */}
        <div className="pt-10 pb-8 px-10 border-b border-[var(--border)] bg-[var(--surface-primary)] hidden lg:block">
          <h1 className="font-serif text-[26px] font-normal leading-none text-[var(--foreground)] tracking-tight">SAGE</h1>
          <div className="text-[11px] font-sans font-medium text-[var(--muted-foreground)] tracking-[0.14em] uppercase mt-2">Security Observatory</div>
        </div>

        {/* Mobile close header for drawer (optional, but requested close on link click handles it) */}
        <div className="pt-6 pb-4 px-6 border-b border-[var(--border)] bg-[var(--surface-primary)] lg:hidden flex justify-between items-center">
          <h1 className="font-serif text-[26px] font-normal leading-none text-[var(--foreground)] tracking-tight">SAGE</h1>
          <button onClick={closeDrawer} className="p-2 text-[var(--muted-foreground)] hover:text-[var(--foreground)]">
            <X size={20} />
          </button>
        </div>
        <div className="text-[11px] font-sans font-medium text-[var(--muted-foreground)] tracking-[0.14em] uppercase mt-2">Security Observatory</div>
      
      {/* Main Nav */}
      <nav className="flex-1 pt-10 pb-10 flex flex-col overflow-y-auto overflow-x-hidden">
        
        {/* MONITORING */}
        <div className="px-6 flex flex-col">
          <div className="text-[11px] font-sans font-semibold text-[var(--muted-foreground)] px-4 mb-5 uppercase tracking-[0.14em]">Monitoring</div>
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={closeDrawer}
                className={cn(
                  "flex items-center px-4 py-2.5 transition-colors duration-200 relative cursor-interactive mb-0.5 rounded-sm",
                  isActive 
                    ? "bg-[var(--status-info)]/10 text-[var(--foreground)]" 
                    : "text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--surface-secondary)]"
                )}
              >
                {isActive && (
                  <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-[var(--status-info)] rounded-r-sm" />
                )}
                <div className={cn(
                  "w-[32px] flex-shrink-0 flex items-center justify-start transition-colors duration-200",
                  isActive ? "text-[var(--status-info)]" : "text-[var(--muted-foreground)]"
                )}>
                  <Icon className="w-[18px] h-[18px]" strokeWidth={1.5} />
                </div>
                <span className={cn("text-[15px] font-sans tracking-normal transition-colors duration-200", isActive ? "font-semibold" : "font-medium")}>{item.label}</span>
              </Link>
            );
          })}
        </div>

        {/* LAB */}
        <div className="mt-12 px-6 flex flex-col">
          <div className="text-[11px] font-sans font-semibold text-[var(--muted-foreground)] px-4 mb-5 uppercase tracking-[0.14em]">Lab</div>
          <Link
            href="/attack-lab"
            onClick={closeDrawer}
            className={cn(
              "flex items-center px-4 py-2.5 transition-colors duration-200 relative cursor-interactive rounded-sm",
              pathname === "/attack-lab"
                ? "bg-[var(--status-info)]/10 text-[var(--foreground)]" 
                : "text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--surface-secondary)]"
            )}
          >
            {pathname === "/attack-lab" && (
              <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-[var(--status-info)] rounded-r-sm" />
            )}
            <div className={cn(
              "w-[32px] flex-shrink-0 flex items-center justify-start transition-colors duration-200",
              pathname === "/attack-lab" ? "text-[var(--status-info)]" : "text-[var(--muted-foreground)]"
            )}>
               <FlaskConical className="w-[18px] h-[18px]" strokeWidth={1.5} />
            </div>
            <span className={cn("text-[15px] font-sans tracking-normal transition-colors duration-200", pathname === "/attack-lab" ? "font-semibold" : "font-medium")}>Attack Lab</span>
          </Link>
        </div>

        {/* SYSTEM */}
        <div className="mt-12 px-6 flex flex-col">
          <div className="text-[11px] font-sans font-semibold text-[var(--muted-foreground)] px-4 mb-5 uppercase tracking-[0.14em]">System</div>
          <Link
            href="/settings"
            onClick={closeDrawer}
            className={cn(
              "flex items-center px-4 py-2.5 transition-colors duration-200 relative cursor-interactive rounded-sm",
              pathname === "/settings"
                ? "bg-[var(--status-info)]/10 text-[var(--foreground)]" 
                : "text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--surface-secondary)]"
            )}
          >
            {pathname === "/settings" && (
              <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-[var(--status-info)] rounded-r-sm" />
            )}
            <div className={cn(
              "w-[32px] flex-shrink-0 flex items-center justify-start transition-colors duration-200",
              pathname === "/settings" ? "text-[var(--status-info)]" : "text-[var(--muted-foreground)]"
            )}>
               <Settings2 className="w-[18px] h-[18px]" strokeWidth={1.5} />
            </div>
            <span className={cn("text-[15px] font-sans tracking-normal transition-colors duration-200", pathname === "/settings" ? "font-semibold" : "font-medium")}>Settings</span>
          </Link>
        </div>
      </nav>

      {/* Status */}
      <div className="p-10 border-t border-[var(--border)] bg-[var(--surface-primary)]">
        <div className="flex items-center">
          <div className={cn("w-3 h-3 rounded-full flex-shrink-0 border border-white/20 shadow-sm", getStatusColor())} />
          <div className="ml-4 flex flex-col">
            <span className="text-[10px] text-[var(--muted-foreground)] tracking-[0.1em] font-sans uppercase font-bold">System Status</span>
            <span className={cn("text-xs font-mono font-bold tracking-[0.1em] mt-1 uppercase", 
              state === "NORMAL" || state === "RECOVERED" ? "text-[var(--status-healthy)]" : 
              state === "MITIGATING" || state === "RECOVERING" ? "text-[var(--status-warning)]" : 
              ["ATTACK_DETECTED", "CLASSIFIED"].includes(state) ? "text-[var(--status-attack)]" :
              "text-[var(--status-healthy)]"
            )}>
              {statusLabel}
            </span>
          </div>
        </div>
      </div>
      </div>
    </>
  );
}
