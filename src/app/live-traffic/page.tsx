"use client";

import { useSage } from "@/lib/store";
import TrafficGraph from "@/components/TrafficGraph";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function LiveTrafficPage() {
  const { trafficData, state } = useSage();
  const latest = trafficData[trafficData.length - 1];
  
  const isAttack = state === "ATTACK_DETECTED" || state === "CLASSIFIED" || state === "MITIGATING";
  const legitimateTraffic = state === "NORMAL" ? "99.9" : state === "RECOVERED" ? "99.8" : "12.4";

  return (
    <div className="flex flex-col h-full bg-[var(--background)]">
      <header className="px-12 py-8 border-b border-[var(--border)] bg-[var(--surface-primary)] flex-shrink-0">
        <h1 className="text-2xl font-bold font-sans tracking-tight text-[var(--foreground)]">Live Traffic Analysis</h1>
      </header>

      <div className="flex-1 px-12 py-10 overflow-y-auto space-y-10">
        
        {/* Top metrics - Avoid identical cards, use aligned typography */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-10">
           <div className="border-l-2 border-[var(--status-info)] pl-6">
             <div className="text-[10px] tracking-widest font-sans text-[var(--muted-foreground)] mb-2 uppercase font-semibold">Current Rate</div>
             <div className="flex items-baseline space-x-2">
               <div className={cn("text-5xl font-serif tracking-tight", isAttack ? "text-[var(--status-attack)]" : "text-[var(--foreground)]")}>
                 {latest?.incoming.toLocaleString(undefined, { maximumFractionDigits: 0 }) || 0}
               </div>
               <span className="text-sm text-[var(--secondary-foreground)] font-sans font-medium uppercase">req/s</span>
             </div>
           </div>
           
           <div className="border-l-2 border-[var(--border)] pl-6">
             <div className="text-[10px] tracking-widest font-sans text-[var(--muted-foreground)] mb-2 uppercase font-semibold">Origin Load</div>
             <div className="flex items-baseline space-x-2">
               <div className="text-5xl font-serif tracking-tight text-[var(--foreground)]">
                 {latest?.origin.toLocaleString(undefined, { maximumFractionDigits: 0 }) || 0}
               </div>
               <span className="text-sm text-[var(--secondary-foreground)] font-sans font-medium uppercase">req/s</span>
             </div>
           </div>
           
           <div className="border-l-2 border-[var(--border)] pl-6">
             <div className="text-[10px] tracking-widest font-sans text-[var(--muted-foreground)] mb-2 uppercase font-semibold">Active Flows</div>
             <div className="text-5xl font-serif tracking-tight text-[var(--foreground)]">
               {Math.floor((latest?.incoming || 0) / 10).toLocaleString()}
             </div>
           </div>
           
           <div className="border-l-2 border-[var(--border)] pl-6">
             <div className="text-[10px] tracking-widest font-sans text-[var(--muted-foreground)] mb-2 uppercase font-semibold">Legitimate Traffic</div>
             <div className="flex items-baseline space-x-1">
               <div className={cn("text-5xl font-serif tracking-tight", isAttack ? "text-[var(--status-attack)]" : "text-[var(--status-healthy)]")}>
                 {legitimateTraffic}
               </div>
               <span className="text-lg text-[var(--secondary-foreground)] font-sans">%</span>
             </div>
           </div>
        </div>

        {/* Primary Chart */}
        <section className="h-[500px] border border-[var(--border)] p-10 bg-[var(--surface-elevated)] rounded-md shadow-sm">
           <TrafficGraph />
        </section>

        {/* Lower section - Editorial tables / structured data */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-10">
           <div className="bg-[var(--surface-primary)] border border-[var(--border)] p-10 rounded-md">
             <h2 className="text-[11px] font-bold tracking-widest text-[var(--muted-foreground)] font-sans uppercase mb-8">Protocol Distribution</h2>
             <div className="space-y-6">
               <div className="grid grid-cols-3 text-[13px] font-sans border-b border-[var(--border)] pb-2 group">
                 <div className="font-semibold text-[var(--foreground)]">HTTPS / 443</div>
                 <div className="text-right text-[var(--secondary-foreground)]">TCP</div>
                 <div className="text-right font-mono font-medium text-[var(--status-info)]">{(latest?.incoming ? (latest.incoming * 0.85) : 0).toLocaleString(undefined, {maximumFractionDigits:0})} req/s</div>
               </div>
               <div className="grid grid-cols-3 text-[13px] font-sans border-b border-[var(--border)] pb-2 group">
                 <div className="font-semibold text-[var(--foreground)]">HTTP / 80</div>
                 <div className="text-right text-[var(--secondary-foreground)]">TCP</div>
                 <div className="text-right font-mono font-medium text-[var(--status-info)]">{(latest?.incoming ? (latest.incoming * 0.12) : 0).toLocaleString(undefined, {maximumFractionDigits:0})} req/s</div>
               </div>
               <div className="grid grid-cols-3 text-[13px] font-sans pb-2 group">
                 <div className="font-semibold text-[var(--foreground)]">DNS / 53</div>
                 <div className="text-right text-[var(--secondary-foreground)]">UDP</div>
                 <div className="text-right font-mono font-medium text-[var(--status-info)]">{(latest?.incoming ? (latest.incoming * 0.03) : 0).toLocaleString(undefined, {maximumFractionDigits:0})} req/s</div>
               </div>
             </div>
           </div>
           
           <div className="bg-[var(--surface-primary)] border border-[var(--border)] p-10 rounded-md">
             <h2 className="text-[11px] font-bold tracking-widest text-[var(--muted-foreground)] font-sans uppercase mb-8">Traffic Composition</h2>
             <div className="space-y-6">
               <div className="grid grid-cols-3 text-[13px] font-sans border-b border-[var(--border)] pb-2">
                 <div className="font-semibold text-[var(--foreground)]">Domestic</div>
                 <div className="text-right text-[var(--secondary-foreground)]">US/CA</div>
                 <div className="text-right font-mono font-medium text-[var(--foreground)]">{isAttack ? "15.2%" : "82.4%"}</div>
               </div>
               <div className="grid grid-cols-3 text-[13px] font-sans border-b border-[var(--border)] pb-2">
                 <div className="font-semibold text-[var(--foreground)]">International</div>
                 <div className="text-right text-[var(--secondary-foreground)]">EU/AP</div>
                 <div className="text-right font-mono font-medium text-[var(--foreground)]">{isAttack ? "81.5%" : "16.1%"}</div>
               </div>
               <div className="grid grid-cols-3 text-[13px] font-sans pb-2">
                 <div className="font-semibold text-[var(--foreground)]">Unknown / Tor</div>
                 <div className="text-right text-[var(--secondary-foreground)]">Anonymized</div>
                 <div className={cn("text-right font-mono font-medium", isAttack ? "text-[var(--status-attack)]" : "text-[var(--foreground)]")}>{isAttack ? "3.3%" : "1.5%"}</div>
               </div>
             </div>
           </div>
        </section>

      </div>
    </div>
  );
}
