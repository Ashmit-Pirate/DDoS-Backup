"use client";

import { useSage } from "@/lib/store";
import TrafficGraph from "@/components/TrafficGraph";
import { format } from "date-fns";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { useState, useEffect } from "react";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function OverviewPage() {
  const { state, trafficData, prediction, mitigations, config } = useSage();

  const isNormal = state === "NORMAL" || state === "RECOVERED";
  const isAttack = state === "ATTACK_DETECTED" || state === "CLASSIFIED";
  const isMitigating = state === "MITIGATING" || state === "RECOVERING";

  const latestTraffic = trafficData[trafficData.length - 1];
  const reqRate = latestTraffic ? latestTraffic.incoming : config.baselineRequestRate;

  const [time, setTime] = useState<Date | null>(null);

  useEffect(() => {
    setTime(new Date());
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col h-full bg-[var(--background)] overflow-y-auto">
      {/* 1. Header Information Strip */}
      <header className="px-6 lg:px-12 py-8 flex flex-col md:flex-row justify-between items-start md:items-end flex-shrink-0 border-b border-[var(--border)] bg-[var(--surface-primary)] gap-6 md:gap-0">
        <div className="flex flex-wrap items-center gap-x-12 lg:gap-x-16 gap-y-6">
          <div>
            <div className="text-[10px] text-[var(--muted-foreground)] tracking-widest font-sans font-semibold mb-2 uppercase">Target System</div>
            <div className="text-[15px] font-semibold font-sans text-[var(--foreground)] tracking-tight">{config.targetApplication}</div>
          </div>
          <div>
            <div className="text-[10px] text-[var(--muted-foreground)] tracking-widest font-sans font-semibold mb-2 uppercase">Environment</div>
            <div className="text-[15px] font-semibold font-sans text-[var(--foreground)] tracking-tight">{config.environment}</div>
          </div>
          <div>
            <div className="text-[10px] text-[var(--muted-foreground)] tracking-widest font-sans font-semibold mb-2 uppercase">System State</div>
            <div className="flex items-center">
              <span className={cn(
                "w-2.5 h-2.5 rounded-full mr-3 border border-[var(--surface-elevated)] flex-shrink-0", 
                isNormal ? "bg-[var(--status-healthy)]" : 
                isMitigating ? "bg-[var(--status-warning)]" : 
                "bg-[var(--status-attack)] animate-pulse shadow-[0_0_8px_rgba(200,92,92,0.4)]"
              )} />
              <span className={cn(
                "text-[15px] font-bold tracking-widest uppercase font-sans",
                isNormal ? "text-[var(--status-healthy)]" : 
                isMitigating ? "text-[var(--status-warning)]" : "text-[var(--status-attack)]"
              )}>
                {state.replace("_", " ")}
              </span>
            </div>
          </div>
        </div>
        <div className="text-left md:text-right w-full md:w-auto">
            <div className="text-[10px] text-[var(--muted-foreground)] tracking-widest font-sans font-semibold mb-2 uppercase">Local Time</div>
            <div className="text-[16px] font-medium font-mono text-[var(--status-info)]">
              {time ? format(time, "HH:mm:ss") : "--:--:--"}
            </div>
        </div>
      </header>

      <div className="px-6 lg:px-12 py-10 flex-1 flex flex-col gap-10 min-w-0">
        
        {/* HERO: Live Traffic */}
        <section className="bg-[var(--surface-elevated)] p-6 lg:p-10 flex flex-col min-h-[500px] relative rounded-md border border-[var(--border)] shadow-sm overflow-hidden">
          <div className="flex flex-col md:flex-row justify-between items-start mb-10 z-10 gap-6">
            <div>
              <h2 className="text-[11px] font-bold font-sans tracking-widest text-[var(--muted-foreground)] uppercase mb-4">Live Traffic Telemetry</h2>
              <div className="flex items-baseline space-x-3 mb-2">
                 <div className={cn("text-5xl md:text-7xl font-serif tracking-tight", isAttack ? "text-[var(--status-attack)]" : "text-[var(--foreground)]")}>
                   {reqRate.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                 </div>
                 <span className="text-[14px] font-sans text-[var(--secondary-foreground)] font-medium tracking-wide uppercase">req/s</span>
              </div>
              <div className="text-[13px] font-sans text-[var(--secondary-foreground)]">
                 {isAttack ? "Traffic spike exceeding acceptable bounds detected." : "Traffic remains within expected operating range."}
              </div>
            </div>
            
            <div className="flex flex-col items-end gap-3 mt-2 bg-[var(--surface-primary)] px-6 py-4 rounded-md border border-[var(--border)]">
               <div className="flex items-center justify-between w-[120px]">
                 <span className="text-[11px] font-sans text-[var(--secondary-foreground)] font-semibold tracking-wide uppercase">Incoming</span>
                 <div className="w-6 h-0.5 bg-[var(--status-info)] opacity-70" />
               </div>
               <div className="flex items-center justify-between w-[120px]">
                 <span className="text-[11px] font-sans text-[var(--secondary-foreground)] font-semibold tracking-wide uppercase">Origin</span>
                 <div className="w-6 h-0.5 bg-[var(--status-data)]" />
               </div>
               <div className="flex items-center justify-between w-[120px] mt-2 pt-2 border-t border-[var(--border)]">
                 <span className="text-[11px] font-sans text-[var(--muted-foreground)] font-semibold tracking-wide uppercase">Baseline</span>
                 <span className="text-[11px] font-mono font-medium text-[var(--technical-text)] text-right">
                   {(config.baselineRequestRate / 1000).toFixed(1)}k
                 </span>
               </div>
            </div>
          </div>
          
          <div className="flex-1 w-full min-h-0 -mx-4 -mb-4">
            <TrafficGraph />
          </div>
        </section>

        {/* MIDDLE: Intelligence and Lifecycle */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
          
          {/* DETECTION */}
          <section className="xl:col-span-5 bg-[var(--surface-elevated)] p-6 lg:p-10 flex flex-col justify-between rounded-md border border-[var(--border)] shadow-sm">
            <SectionHeader eyebrow="Detection Intelligence" />
            <div className="mb-8">
              <div className="text-[12px] font-sans text-[var(--secondary-foreground)] uppercase tracking-widest font-semibold mb-2">Model Architecture</div>
              <div className="text-2xl text-[var(--foreground)] font-serif tracking-tight">Balanced Random Forest</div>
            </div>

            <div className="grid grid-cols-2 gap-x-8 gap-y-6">
              <div>
                <div className="text-[10px] font-semibold font-sans tracking-widest text-[var(--muted-foreground)] uppercase mb-1">Prediction</div>
                <div className={cn(
                  "text-[28px] font-bold font-sans tracking-tight",
                  prediction.prediction === "Benign" ? "text-[var(--status-healthy)]" : "text-[var(--status-attack)]"
                )}>
                  {prediction.prediction}
                </div>
              </div>
              <div>
                <div className="text-[10px] font-semibold font-sans tracking-widest text-[var(--muted-foreground)] uppercase mb-1">Confidence</div>
                <div className="text-[28px] font-bold font-sans tracking-tight text-[var(--foreground)]">
                  {prediction.confidence.toFixed(1)}<span className="text-lg text-[var(--secondary-foreground)] ml-1">%</span>
                </div>
              </div>
              <div className="col-span-2">
                <div className="text-[10px] font-semibold font-sans tracking-widest text-[var(--muted-foreground)] uppercase mb-2">System Risk</div>
                <StatusBadge 
                  label={prediction.risk} 
                  status={prediction.risk === "HIGH" ? "attack" : prediction.risk === "MEDIUM" ? "warning" : "healthy"} 
                />
              </div>
            </div>
          </section>

          {/* RESPONSE TIMELINE */}
          <section className="xl:col-span-7 bg-[var(--surface-elevated)] p-6 lg:p-10 rounded-md border border-[var(--border)] shadow-sm overflow-x-auto">
            <SectionHeader eyebrow="Response Lifecycle" />
            
            <div className="min-w-[500px] grid grid-cols-4 gap-4 h-full pt-2">
              {/* Detection Phase */}
              <div className="relative">
                <div className="h-px w-full bg-[var(--border)] absolute top-2.5 left-0" />
                <div className={cn("w-5 h-5 rounded-full relative z-10 flex items-center justify-center bg-[var(--surface-elevated)] border-2 transition-colors duration-500", 
                  state !== "NORMAL" ? "border-[var(--status-attack)]" : "border-[var(--border)]"
                )}>
                   {state !== "NORMAL" && <div className="w-2.5 h-2.5 rounded-full bg-[var(--status-attack)]" />}
                </div>
                <div className="mt-6">
                  <div className={cn("text-[14px] font-sans font-semibold tracking-wide transition-colors duration-500", state !== "NORMAL" ? "text-[var(--foreground)]" : "text-[var(--muted-foreground)]")}>Detected</div>
                  {state !== "NORMAL" && <div className="text-[11px] font-sans font-medium text-[var(--status-attack)] mt-1">Traffic Anomaly</div>}
                </div>
              </div>

              {/* Classification Phase */}
              <div className="relative">
                <div className="h-px w-full bg-[var(--border)] absolute top-2.5 left-0" />
                <div className={cn("w-5 h-5 rounded-full relative z-10 flex items-center justify-center bg-[var(--surface-elevated)] border-2 transition-colors duration-500", 
                  ["CLASSIFIED", "MITIGATING", "RECOVERING", "RECOVERED"].includes(state) ? "border-[var(--status-info)]" : "border-[var(--border)]"
                )}>
                   {["CLASSIFIED", "MITIGATING", "RECOVERING", "RECOVERED"].includes(state) && <div className="w-2.5 h-2.5 rounded-full bg-[var(--status-info)]" />}
                </div>
                <div className="mt-6">
                  <div className={cn("text-[14px] font-sans font-semibold tracking-wide transition-colors duration-500", ["CLASSIFIED", "MITIGATING", "RECOVERING", "RECOVERED"].includes(state) ? "text-[var(--foreground)]" : "text-[var(--muted-foreground)]")}>Classified</div>
                  {["CLASSIFIED", "MITIGATING", "RECOVERING", "RECOVERED"].includes(state) && <div className="text-[11px] font-sans font-medium text-[var(--status-info)] mt-1">{prediction.prediction} Confirmed</div>}
                </div>
              </div>

              {/* Mitigation Phase */}
              <div className="relative">
                <div className="h-px w-full bg-[var(--border)] absolute top-2.5 left-0" />
                <div className={cn("w-5 h-5 rounded-full relative z-10 flex items-center justify-center bg-[var(--surface-elevated)] border-2 transition-colors duration-500", 
                  ["MITIGATING", "RECOVERING", "RECOVERED"].includes(state) ? "border-[var(--status-warning)]" : "border-[var(--border)]"
                )}>
                   {["MITIGATING", "RECOVERING", "RECOVERED"].includes(state) && <div className="w-2.5 h-2.5 rounded-full bg-[var(--status-warning)]" />}
                </div>
                <div className="mt-6">
                  <div className={cn("text-[14px] font-sans font-semibold tracking-wide transition-colors duration-500", ["MITIGATING", "RECOVERING", "RECOVERED"].includes(state) ? "text-[var(--foreground)]" : "text-[var(--muted-foreground)]")}>Mitigating</div>
                  {["MITIGATING", "RECOVERING", "RECOVERED"].includes(state) && <div className="text-[11px] font-sans font-medium text-[var(--status-warning)] mt-1 truncate">{mitigations[0]?.name || "Active"}</div>}
                </div>
              </div>

              {/* Recovery Phase */}
              <div className="relative">
                <div className={cn("w-5 h-5 rounded-full relative z-10 flex items-center justify-center bg-[var(--surface-elevated)] border-2 transition-colors duration-500", 
                  state === "RECOVERED" ? "border-[var(--status-healthy)]" : "border-[var(--border)]"
                )}>
                   {state === "RECOVERED" && <div className="w-2.5 h-2.5 rounded-full bg-[var(--status-healthy)]" />}
                </div>
                <div className="mt-6">
                  <div className={cn("text-[14px] font-sans font-semibold tracking-wide transition-colors duration-500", state === "RECOVERED" ? "text-[var(--foreground)]" : "text-[var(--muted-foreground)]")}>Recovered</div>
                  {state === "RECOVERED" && <div className="text-[11px] font-sans font-medium text-[var(--status-healthy)] mt-1">Traffic Normalized</div>}
                </div>
              </div>

            </div>
          </section>

        </div>

        {/* BOTTOM FULL WIDTH: Evidence */}
        <section className="bg-[var(--surface-primary)] p-6 lg:p-10 rounded-md border border-[var(--border)] overflow-x-auto">
          <SectionHeader eyebrow="Detection Evidence Snapshot" />
          <div className="min-w-[600px] grid grid-cols-4 gap-8 py-4">
             <div className="border-l border-[var(--border)] pl-6">
                <div className="text-[10px] font-sans font-semibold text-[var(--muted-foreground)] uppercase tracking-widest mb-1">Request Rate</div>
                <div className="text-[15px] font-mono text-[var(--foreground)]">{reqRate > config.baselineRequestRate * 2 ? "+314% baseline" : "Nominal"}</div>
             </div>
             <div className="border-l border-[var(--border)] pl-6">
                <div className="text-[10px] font-sans font-semibold text-[var(--muted-foreground)] uppercase tracking-widest mb-1">Source IP Entropy</div>
                <div className="text-[15px] font-mono text-[var(--foreground)]">{isAttack ? "0.2 (Spoofed Range)" : `${config.baselineEntropy} (Normal)`}</div>
             </div>
             <div className="border-l border-[var(--border)] pl-6">
                <div className="text-[10px] font-sans font-semibold text-[var(--muted-foreground)] uppercase tracking-widest mb-1">Endpoint Concentration</div>
                <div className="text-[15px] font-mono text-[var(--foreground)]">{isAttack ? "98.2% /login" : "Distributed"}</div>
             </div>
             <div className="border-l border-[var(--border)] pl-6">
                <div className="text-[10px] font-sans font-semibold text-[var(--muted-foreground)] uppercase tracking-widest mb-1">TCP Behaviour</div>
                <div className="text-[15px] font-mono text-[var(--foreground)]">{prediction.prediction === "Syn" ? "Incomplete Handshakes" : "Standard"}</div>
             </div>
          </div>
        </section>

      </div>
    </div>
  );
}
