"use client";

import { useSage } from "@/lib/store";
import TrafficGraph from "@/components/TrafficGraph";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useParams } from "next/navigation";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { MetricReadout } from "@/components/ui/MetricReadout";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function IncidentDetailPage() {
  const { id } = useParams();
  const { incidents, logs } = useSage();
  
  const incident = incidents.find(i => i.id === id);
  const incidentLogs = logs.filter(l => l.incidentId === id);

  if (!incident) {
    return (
       <div className="flex flex-col items-center justify-center h-full bg-[var(--background)]">
          <div className="text-[11px] font-mono tracking-widest text-[var(--muted-foreground)] uppercase">404</div>
          <div className="text-2xl font-bold font-sans text-[var(--foreground)] mt-2">Incident not found</div>
          <Link href="/incidents" className="mt-6 text-[13px] font-sans font-semibold text-[var(--status-info)] hover:underline cursor-interactive">Return to Incidents</Link>
       </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-[var(--background)] overflow-y-auto">
      <header className="px-6 lg:px-12 py-8 flex-shrink-0 flex items-center justify-between border-b border-[var(--border)] bg-[var(--surface-primary)]">
        <div className="flex items-center">
          <Link href="/incidents" className="mr-6 text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors cursor-interactive">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <h1 className="text-xl lg:text-2xl font-bold tracking-tight text-[var(--foreground)] font-sans flex items-center flex-wrap">
             Investigation <span className="text-[var(--border)] mx-4">/</span> <span className="font-mono font-medium text-[var(--status-info)] text-[16px] lg:text-[18px] mt-0.5 tracking-widest">{id}</span>
          </h1>
        </div>
        <StatusBadge 
          label={incident.status} 
          status={incident.status === "ACTIVE" ? "attack" : "healthy"} 
        />
      </header>

      <div className="flex-1 px-6 lg:px-12 py-10 flex flex-col gap-10 min-w-0">
         
         {/* Incident Summary */}
         <section className="bg-[var(--surface-elevated)] p-6 lg:p-10 rounded-md border border-[var(--border)] shadow-sm overflow-x-auto">
            <SectionHeader eyebrow="Incident Summary" />
            
            <div className="min-w-[700px] grid grid-cols-5 gap-8 border-b border-[var(--border)] pb-10">
               <MetricReadout 
                 label="Threat Classification" 
                 value={incident.type} 
                 status="attack" 
                 size="small" 
                 className="border-l-2 border-[var(--status-attack)] pl-5" 
               />
               <MetricReadout 
                 label="Severity" 
                 value={incident.severity} 
                 size="small" 
                 className="border-l-2 border-[var(--border)] pl-5 uppercase" 
               />
               <MetricReadout 
                 label="Detection Latency" 
                 value={incident.detectionTime} 
                 size="small" 
                 className="border-l-2 border-[var(--border)] pl-5" 
               />
               <MetricReadout 
                 label="Mitigation Latency" 
                 value={incident.mitigationTime} 
                 size="small" 
                 className="border-l-2 border-[var(--border)] pl-5" 
               />
               <MetricReadout 
                 label="Total Duration" 
                 value={incident.duration} 
                 size="small" 
                 className="border-l-2 border-[var(--border)] pl-5" 
               />
            </div>
         </section>

         <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 min-h-[500px]">
            {/* Traffic Evidence */}
            <section className="lg:col-span-8 bg-[var(--surface-elevated)] p-6 lg:p-10 rounded-md border border-[var(--border)] shadow-sm flex flex-col h-[400px] lg:h-[550px] min-w-0">
               <SectionHeader eyebrow="Traffic Evidence Archive" />
               <div className="flex-1 w-full min-h-0 -mx-4 -mb-4">
                 <TrafficGraph />
               </div>
            </section>
            
            {/* Incident Logs */}
            <section className="lg:col-span-4 bg-[var(--surface-primary)] p-6 lg:p-10 rounded-md border border-[var(--border)] flex flex-col h-[400px] lg:h-[550px]">
               <SectionHeader eyebrow="Event Timeline" />
               <div className="flex-1 overflow-y-auto space-y-6">
                  {incidentLogs.length === 0 ? (
                     <div className="h-full flex items-center justify-center text-[10px] tracking-widest font-sans text-[var(--muted-foreground)] uppercase">No logs linked.</div>
                  ) : (
                     incidentLogs.map(log => (
                        <div key={log.id} className="pb-5 border-b border-[var(--border)] last:border-0 relative group">
                           <div className="flex justify-between items-center mb-2">
                              <span className="text-[11px] font-mono text-[var(--technical-text)] tracking-widest">{log.time.split('.')[0]}</span>
                              <StatusBadge 
                                label={log.severity} 
                                status={
                                  log.severity === "OK" ? "healthy" :
                                  ["WARN", "ALERT", "HIGH"].includes(log.severity) ? "warning" :
                                  "neutral"
                                } 
                              />
                           </div>
                           <div className="text-[10px] font-sans font-bold text-[var(--status-info)] uppercase tracking-widest mb-1.5">{log.component}</div>
                           <div className="text-[13px] font-sans font-medium text-[var(--foreground)] tracking-wide leading-relaxed">{log.message}</div>
                        </div>
                     ))
                  )}
               </div>
            </section>
         </div>

      </div>
    </div>
  );
}
