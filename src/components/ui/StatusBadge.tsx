import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function StatusBadge({
  status,
  label,
  className
}: {
  status: "neutral" | "healthy" | "warning" | "attack" | "info";
  label: string;
  className?: string;
}) {
  const getColors = () => {
    switch (status) {
      case "healthy": return "text-[var(--status-healthy)] bg-[var(--status-healthy)]/10 border-[var(--status-healthy)]/20";
      case "warning": return "text-[var(--status-warning)] bg-[var(--status-warning)]/10 border-[var(--status-warning)]/20";
      case "attack": return "text-[var(--status-attack)] bg-[var(--status-attack)]/10 border-[var(--status-attack)]/20";
      case "info": return "text-[var(--status-info)] bg-[var(--status-info)]/10 border-[var(--status-info)]/20";
      default: return "text-[var(--foreground)] bg-[var(--surface-primary)] border-[var(--border)]";
    }
  };

  return (
    <span className={cn(
      "inline-flex items-center text-[10px] sm:text-[11px] font-bold font-sans tracking-widest px-2.5 sm:px-3 py-1 sm:py-1.5 uppercase rounded-sm border transition-colors duration-500",
      getColors(),
      className
    )}>
      {label}
    </span>
  );
}
