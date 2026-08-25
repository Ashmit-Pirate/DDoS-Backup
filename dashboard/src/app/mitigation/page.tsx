"use client";

import { useSage } from "@/lib/store";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { DataTable, DataTableHeader, DataTableHeaderCell, DataTableRow, DataTableCell } from "@/components/ui/DataTable";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function MitigationPage() {
  const { state, prediction, mitigations, config } = useSage();
  const isMitigating = state === "MITIGATING" || state === "RECOVERING";
  const isActive = state === "ATTACK_DETECTED" || state === "CLASSIFIED" || isMitigating;

  return (
    <div className="flex flex-col h-full bg-[var(--background)] overflow-y-auto">
      <header className="px-6 lg:px-12 py-8 flex-shrink-0 border-b border-[var(--border)] bg-[var(--surface-primary)]">
        <h1 className="text-2xl font-bold tracking-tight text-[var(--foreground)] font-sans">Mitigation Control</h1>
      </header>

      <div className="flex-1 px-6 lg:px-12 py-10 space-y-10 min-w-0">
        
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
           {/* Decision Engine */}
           <section className={cn(
             "lg:col-span-7 p-6 lg:p-10 rounded-md border shadow-sm transition-colors duration-500",
             isActive ? "bg-[var(--surface-elevated)] border-[var(--status-warning)]/40 shadow-[0_4px_20px_rgba(196,147,74,0.1)] relative overflow-hidden" : "bg-[var(--surface-primary)] border-[var(--border)]"
           )}>
              {isActive && <div className="absolute top-0 left-0 w-1.5 h-full bg-[var(--status-warning)]" />}
              <SectionHeader eyebrow="Decision Engine" />
              
              <div className="grid grid-cols-2 gap-x-8 gap-y-10">
                 <div>
                    <div className="text-[10px] font-semibold font-sans tracking-widest text-[var(--muted-foreground)] uppercase mb-2">Calculated Risk</div>
                    <div className={cn(
                      "text-4xl font-bold font-sans uppercase tracking-tight",
                      prediction.risk === "HIGH" ? "text-[var(--status-attack)]" : prediction.risk === "MEDIUM" ? "text-[var(--status-warning)]" : "text-[var(--status-healthy)]"
                    )}>{prediction.risk}</div>
                 </div>
                 <div>
                    <div className="text-[10px] font-semibold font-sans tracking-widest text-[var(--muted-foreground)] uppercase mb-2">Automated Decision</div>
                    <div className="text-4xl font-bold font-sans text-[var(--foreground)] tracking-tight">{isActive ? "MITIGATE" : "ALLOW"}</div>
                 </div>
                 <div>
                    <div className="text-[10px] font-semibold font-sans tracking-widest text-[var(--muted-foreground)] uppercase mb-2">Identified Threat</div>
                    <div className={cn("text-3xl font-serif tracking-tight", isActive ? "text-[var(--status-attack)]" : "text-[var(--foreground)]")}>{prediction.prediction}</div>
                 </div>
                 <div>
                    <div className="text-[10px] font-semibold font-sans tracking-widest text-[var(--muted-foreground)] uppercase mb-2">Model Confidence</div>
                    <div className="text-3xl font-serif text-[var(--foreground)] tracking-tight">{prediction.confidence.toFixed(1)}<span className="text-xl text-[var(--secondary-foreground)] ml-1 font-sans">%</span></div>
                 </div>
              </div>
           </section>

           {/* Metrics */}
           <section className="lg:col-span-5 bg-[var(--surface-primary)] p-6 lg:p-10 rounded-md border border-[var(--border)] flex flex-col justify-between">
              <div>
                <SectionHeader eyebrow="Mitigation Metrics" />
                
                <div className="space-y-8">
                   <div>
                      <div className="text-[10px] font-semibold font-sans tracking-widest text-[var(--muted-foreground)] uppercase mb-2">Time to Mitigate</div>
                      <div className="text-4xl font-serif text-[var(--foreground)] tracking-tight">{isMitigating ? "3.05" : "-"}<span className="text-xl text-[var(--secondary-foreground)] ml-1 font-sans">{isMitigating ? "s" : ""}</span></div>
                   </div>
                   <div>
                      <div className="text-[10px] font-semibold font-sans tracking-widest text-[var(--muted-foreground)] uppercase mb-2">Server Availability</div>
                      <div className={cn("text-4xl font-serif tracking-tight", isMitigating ? "text-[var(--status-warning)]" : "text-[var(--status-healthy)]")}>
                        {config.serverAvailability}<span className="text-xl text-[var(--secondary-foreground)] ml-1 font-sans">%</span>
                      </div>
                   </div>
                </div>
              </div>

              <div className="mt-10 pt-6 border-t border-[var(--border)]">
                 <div className="flex justify-between items-center">
                    <span className="text-[11px] font-semibold font-sans tracking-widest text-[var(--muted-foreground)] uppercase">Execution Mode</span>
                    <StatusBadge 
                      label={config.mitigationMode} 
                      status={config.mitigationMode === "Simulation Only" ? "info" : "warning"} 
                    />
                 </div>
              </div>
           </section>
        </div>

        {/* Action List */}
        <section className="bg-[var(--surface-elevated)] p-6 lg:p-10 rounded-md border border-[var(--border)] shadow-sm">
           <SectionHeader eyebrow="Operational Actions" />

           {mitigations.length === 0 ? (
             <div className="h-32 flex items-center justify-center border border-dashed border-[var(--border)] rounded-md bg-[var(--surface-primary)]">
               <span className="text-[13px] tracking-wide font-sans text-[var(--secondary-foreground)]">System operating normally. No actions required.</span>
             </div>
           ) : (
             <DataTable>
               <DataTableHeader className="grid-cols-12 px-4">
                 <DataTableHeaderCell className="col-span-1">ID</DataTableHeaderCell>
                 <DataTableHeaderCell className="col-span-4">Action Directive</DataTableHeaderCell>
                 <DataTableHeaderCell className="col-span-2">State</DataTableHeaderCell>
                 <DataTableHeaderCell className="col-span-5">Operational Result</DataTableHeaderCell>
               </DataTableHeader>

               {mitigations.map((m, i) => (
                 <DataTableRow key={m.id} className="grid-cols-12 px-4" interactive>
                   <DataTableCell className="col-span-1" technical>0{i+1}</DataTableCell>
                   <DataTableCell className="col-span-4"><span className="font-semibold">{m.name}</span></DataTableCell>
                   <DataTableCell className="col-span-2">
                     <StatusBadge 
                        label={m.status} 
                        status={
                          m.status === "SIMULATED" ? "info" :
                          m.status === "COMPLETED" ? "healthy" :
                          "warning"
                        }
                     />
                   </DataTableCell>
                   <DataTableCell className="col-span-5" technical>{m.result}</DataTableCell>
                 </DataTableRow>
               ))}
             </DataTable>
           )}
        </section>

      </div>
    </div>
  );
}
