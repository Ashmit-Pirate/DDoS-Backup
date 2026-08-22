import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function DataTable({ children, className }: { children: React.ReactNode, className?: string }) {
  return (
    <div className={cn("w-full overflow-x-auto", className)}>
      <div className="min-w-[800px] flex flex-col">
        {children}
      </div>
    </div>
  );
}

export function DataTableHeader({ children, className }: { children: React.ReactNode, className?: string }) {
  return (
    <div className={cn("grid gap-4 pb-4 border-b border-[var(--border)]", className)}>
      {children}
    </div>
  );
}

export function DataTableHeaderCell({ children, className, align = "left" }: { children: React.ReactNode, className?: string, align?: "left" | "right" | "center" }) {
  return (
    <div className={cn(
      "text-[10px] tracking-widest font-sans font-semibold text-[var(--muted-foreground)] uppercase",
      align === "right" && "text-right",
      align === "center" && "text-center",
      className
    )}>
      {children}
    </div>
  );
}

export function DataTableRow({ children, className, interactive = false, href }: { children: React.ReactNode, className?: string, interactive?: boolean, href?: string }) {
  const baseClasses = "grid gap-4 items-center py-4 border-b border-[var(--border)] last:border-0 group";
  const interactiveClasses = interactive ? "hover:bg-[var(--surface-primary)] transition-colors cursor-interactive rounded-md px-4 -mx-4" : "";
  
  if (href) {
     return (
       <a href={href} className={cn(baseClasses, interactiveClasses, className)}>
         {children}
       </a>
     );
  }

  return (
    <div className={cn(baseClasses, interactiveClasses, className)}>
      {children}
    </div>
  );
}

export function DataTableCell({ children, className, align = "left", technical = false }: { children: React.ReactNode, className?: string, align?: "left" | "right" | "center", technical?: boolean }) {
  return (
    <div className={cn(
      technical ? "text-[13px] font-mono text-[var(--technical-text)]" : "text-[13px] font-sans font-medium text-[var(--foreground)] tracking-wide",
      align === "right" && "text-right",
      align === "center" && "text-center",
      className
    )}>
      {children}
    </div>
  );
}
