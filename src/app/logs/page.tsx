"use client";

import { useSage } from "@/lib/store";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { DataTable, DataTableHeader, DataTableHeaderCell, DataTableRow, DataTableCell } from "@/components/ui/DataTable";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function LogsPage() {
  const { logs } = useSage();

  return (
    <div className="flex flex-col h-full bg-[var(--background)] overflow-y-auto">
      <header className="px-6 lg:px-12 py-8 flex-shrink-0 flex justify-between items-end border-b border-[var(--border)] bg-[var(--surface-primary)]">
        <div>
           <h1 className="text-2xl font-bold tracking-tight text-[var(--foreground)] font-sans">System Logs</h1>
        </div>
        <div className="text-[10px] tracking-widest font-sans font-semibold text-[var(--muted-foreground)] uppercase">
           {logs.length} Events Recorded
        </div>
      </header>

      <div className="flex-1 flex flex-col min-h-0 bg-[var(--surface-elevated)] m-6 lg:m-12 rounded-md shadow-sm border border-[var(--border)] min-w-0">
         
         {/* Filters placeholder */}
         <div className="px-6 lg:px-10 py-5 border-b border-[var(--border)] flex flex-wrap gap-x-10 gap-y-4 text-[10px] font-sans font-semibold tracking-widest text-[var(--muted-foreground)] uppercase bg-[var(--surface-primary)] rounded-t-md">
            <button className="hover:text-[var(--foreground)] transition-colors text-[var(--foreground)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--foreground)]">Severity: All</button>
            <button className="hover:text-[var(--foreground)] transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--foreground)]">Component: All</button>
            <button className="hover:text-[var(--foreground)] transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--foreground)]">Incident: All</button>
         </div>

         {/* Logs Content */}
         <div className="flex-1 overflow-y-auto px-6 lg:px-10 py-6">
            {logs.length === 0 ? (
              <div className="flex items-center justify-center h-[300px] text-[var(--muted-foreground)] text-sm font-sans tracking-wide">
                System initializing. No events recorded in the current session.
              </div>
            ) : (
              <DataTable>
                 <DataTableHeader className="grid-cols-12 px-4">
                    <DataTableHeaderCell className="col-span-2">Time</DataTableHeaderCell>
                    <DataTableHeaderCell className="col-span-1">Severity</DataTableHeaderCell>
                    <DataTableHeaderCell className="col-span-3">Component</DataTableHeaderCell>
                    <DataTableHeaderCell className="col-span-5">Event</DataTableHeaderCell>
                    <DataTableHeaderCell className="col-span-1" align="right">Incident</DataTableHeaderCell>
                 </DataTableHeader>
                 
                 <div className="pb-4">
                   {logs.map((log) => (
                     <DataTableRow key={log.id} className="grid-cols-12 px-4" interactive>
                        <DataTableCell className="col-span-2" technical>{log.time}</DataTableCell>
                        <DataTableCell className={cn(
                           "col-span-1 uppercase font-bold tracking-widest",
                           log.severity === "OK" ? "text-[var(--status-healthy)]" :
                           ["WARN", "ALERT", "HIGH"].includes(log.severity) ? "text-[var(--status-warning)]" :
                           "text-[var(--muted-foreground)]"
                        )} technical>{log.severity}</DataTableCell>
                        <DataTableCell className="col-span-3 text-[var(--status-info)] uppercase font-medium truncate" technical>{log.component}</DataTableCell>
                        <DataTableCell className="col-span-5 leading-relaxed">{log.message}</DataTableCell>
                        <DataTableCell className="col-span-1 text-[var(--status-attack)] opacity-60 group-hover:opacity-100 transition-opacity font-bold" align="right" technical>
                          {log.incidentId || "-"}
                        </DataTableCell>
                     </DataTableRow>
                   ))}
                 </div>
              </DataTable>
            )}
         </div>

      </div>
    </div>
  );
}
