import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function MetricReadout({
  label,
  value,
  unit,
  status = "neutral",
  size = "large",
  className
}: {
  label: string;
  value: React.ReactNode;
  unit?: string;
  status?: "neutral" | "healthy" | "warning" | "attack" | "info";
  size?: "large" | "medium" | "small";
  className?: string;
}) {
  const getStatusColor = () => {
    switch (status) {
      case "healthy": return "text-[var(--status-healthy)]";
      case "warning": return "text-[var(--status-warning)]";
      case "attack": return "text-[var(--status-attack)]";
      case "info": return "text-[var(--status-info)]";
      default: return "text-[var(--foreground)]";
    }
  };

  const getSizeClasses = () => {
    switch (size) {
      case "large": return "text-5xl font-serif tracking-tight";
      case "medium": return "text-4xl font-sans font-bold tracking-tight uppercase";
      case "small": return "text-[28px] font-bold font-sans tracking-tight";
    }
  };

  return (
    <div className={className}>
      <div className="text-[10px] font-semibold font-sans tracking-widest text-[var(--muted-foreground)] uppercase mb-2">
        {label}
      </div>
      <div className={cn(getSizeClasses(), getStatusColor(), "transition-colors duration-500")}>
        {value}
        {unit && (
          <span className={cn(
            "ml-1 font-sans", 
            size === "large" ? "text-2xl" : size === "medium" ? "text-xl" : "text-lg",
            "text-[var(--secondary-foreground)]"
          )}>
            {unit}
          </span>
        )}
      </div>
    </div>
  );
}
