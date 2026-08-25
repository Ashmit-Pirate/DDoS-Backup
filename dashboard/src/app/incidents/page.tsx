"use client";

import { useSage } from "@/lib/store";
import { format } from "date-fns";
import { ShieldCheck } from "lucide-react";
import { DataTable, DataTableHeader, DataTableHeaderCell, DataTableRow, DataTableCell } from "@/components/ui/DataTable";
import { StatusBadge } from "@/components/ui/StatusBadge";

export default function IncidentsPage() {
  const { incidents } = useSage();

  return (
    <div className="flex flex-col h-full bg-[var(--background)] overflow-y-auto">
      <header className="px-6 lg:px-12 py-8 flex-shrink-0 border-b border-[var(--border)] bg-[var(--surface-primary)]">
        <h1 className="text-2xl font-bold tracking-tight text-[var(--foreground)] font-sans">Incidents</h1>
      </header>

      <div className="flex-1 px-6 lg:px-12 py-10 min-w-0">
        <section className="bg-[var(--surface-elevated)] rounded-md border border-[var(--border)] overflow-hidden shadow-sm">
           
           {incidents.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-32 px-10">
                 <div className="w-16 h-16 rounded-full bg-[var(--status-healthy)]/10 flex items-center justify-center mb-6 border border-[var(--status-healthy)]/20">
                    <ShieldCheck className="w-8 h-8 text-[var(--status-healthy)] opacity-80" strokeWidth={1.5} />
                 </div>
                 <h2 className="text-xl font-serif tracking-tight text-[var(--foreground)] mb-2">NO ACTIVE INCIDENTS</h2>
                 <p className="text-sm font-sans tracking-wide text-[var(--secondary-foreground)] text-center max-w-md">
                   Monitoring continues.
                 </p>
              </div>
           ) : (
              <DataTable>
                 <DataTableHeader className="grid-cols-12 px-10 pt-5 bg-[var(--surface-primary)]">
                    <DataTableHeaderCell className="col-span-2">Incident ID</DataTableHeaderCell>
                    <DataTableHeaderCell className="col-span-1">Status</DataTableHeaderCell>
                    <DataTableHeaderCell className="col-span-2">Threat</DataTableHeaderCell>
                    <DataTableHeaderCell className="col-span-1">Severity</DataTableHeaderCell>
                    <DataTableHeaderCell className="col-span-2">Start</DataTableHeaderCell>
                    <DataTableHeaderCell className="col-span-1">Detection</DataTableHeaderCell>
                    <DataTableHeaderCell className="col-span-1">Mitigation</DataTableHeaderCell>
                    <DataTableHeaderCell className="col-span-2" align="right">Duration</DataTableHeaderCell>
                 </DataTableHeader>

                 <div className="px-10 pb-5">
                    {incidents.map((inc) => (
                       <DataTableRow 
                         href={`/incidents/${inc.id}`}
                         key={inc.id} 
                         className="grid-cols-12"
                         interactive
                       >
                          <DataTableCell className="col-span-2 transition-colors group-hover:text-[var(--status-info)]" technical>{inc.id}</DataTableCell>
                          <DataTableCell className="col-span-1">
                             <StatusBadge 
                                label={inc.status} 
                                status={inc.status === "ACTIVE" ? "attack" : "healthy"} 
                             />
                          </DataTableCell>
                          <DataTableCell className="col-span-2 uppercase font-semibold">{inc.type}</DataTableCell>
                          <DataTableCell className="col-span-1 text-[var(--status-attack)]" technical><span className="font-medium">{inc.severity}</span></DataTableCell>
                          <DataTableCell className="col-span-2 text-[var(--secondary-foreground)]" technical>{format(new Date(inc.start), "HH:mm:ss")}</DataTableCell>
                          <DataTableCell className="col-span-1 text-[var(--secondary-foreground)]" technical>{inc.detectionTime}</DataTableCell>
                          <DataTableCell className="col-span-1 text-[var(--secondary-foreground)]" technical>{inc.mitigationTime}</DataTableCell>
                          <DataTableCell className="col-span-2" align="right" technical><span className="font-medium">{inc.duration}</span></DataTableCell>
                       </DataTableRow>
                    ))}
                 </div>
              </DataTable>
           )}
        </section>
      </div>
    </div>
  );
}
