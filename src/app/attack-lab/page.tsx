"use client";

import React from "react";
import { useSage } from "@/lib/store";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function AttackLabPage() {
  const { state, config, simulateAttack, resetSimulation } = useSage();
  
  const isRunning = state !== "NORMAL" && state !== "RECOVERED";

  return (
    <div className="flex flex-col h-full bg-[var(--background)] overflow-y-auto">
      <header className="px-6 lg:px-12 py-8 flex-shrink-0 flex items-center justify-between border-b border-[var(--border)] bg-[var(--surface-primary)]">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--foreground)] font-sans flex items-center flex-wrap gap-4">
            Attack Lab
            <StatusBadge label="Safe Simulation" status="warning" />
          </h1>
        </div>
      </header>

      <div className="flex-1 p-6 lg:p-12 flex justify-center">
        <div className="w-full max-w-4xl space-y-10 min-w-0">
          
          <div className="text-[14px] font-sans tracking-wide text-[var(--secondary-foreground)] leading-relaxed bg-[var(--surface-elevated)] p-6 lg:p-10 rounded-md border border-[var(--border)] border-l-4 border-l-[var(--status-info)] shadow-sm">
            <span className="font-bold text-[var(--foreground)] uppercase text-[11px] tracking-widest block mb-2">Controlled Simulation Environment</span>
            This module controls the global mock state machine. Traffic generated here is strictly restricted to the local demonstration environment. Initiating an attack will trigger a realistic response across all observatory components, including Telemetry, Detection Intelligence, Mitigation Control, and Operational Logs.
          </div>

          <section className="bg-[var(--surface-primary)] p-6 lg:p-10 rounded-md border border-[var(--border)] relative overflow-x-auto">
             <SectionHeader eyebrow="Target Definition" />
             <div className="min-w-0 flex flex-col md:grid md:grid-cols-2 gap-10">
                <div>
                  <div className="text-[10px] font-semibold font-sans tracking-widest text-[var(--muted-foreground)] uppercase mb-2">Protected Application</div>
                  <div className="text-xl font-serif text-[var(--foreground)] tracking-tight">{config.targetApplication}</div>
                </div>
                <div>
                  <div className="text-[10px] font-semibold font-sans tracking-widest text-[var(--muted-foreground)] uppercase mb-2">Environment</div>
                  <div className="text-xl font-serif text-[var(--foreground)] tracking-tight">{config.environment}</div>
                </div>
             </div>
          </section>

          <section className="bg-[var(--surface-elevated)] p-6 lg:p-10 rounded-md border border-[var(--border)] relative shadow-sm overflow-x-auto">
             <div className="absolute top-0 left-0 w-full h-1 bg-[var(--status-attack)] opacity-60 rounded-t-md" />
             <SectionHeader eyebrow="Simulation Controls" />
             
             <div className="min-w-0">
               <div className="mb-12">
                  <div className="text-[10px] font-semibold font-sans tracking-widest text-[var(--muted-foreground)] uppercase mb-3">Threat Vector Profile</div>
                  <div className="border border-[var(--status-attack)]/30 bg-[var(--status-attack)]/5 p-6 rounded-md flex items-center justify-between cursor-not-allowed">
                     <div>
                       <span className="text-[16px] text-[var(--foreground)] font-sans font-bold tracking-tight">DDoS — SYN Flood</span>
                       <div className="text-[11px] font-mono text-[var(--muted-foreground)] mt-2 font-medium">77 FEATURE VECTORS / HIGH CONFIDENCE</div>
                     </div>
                     <div className="w-3 h-3 rounded-full bg-[var(--status-attack)] shadow-[0_0_15px_rgba(200,92,92,0.3)] animate-pulse" />
                  </div>
               </div>

               <div className="flex flex-col sm:flex-row gap-6 mb-12">
                  <button 
                    onClick={() => simulateAttack("MEDIUM")}
                    disabled={isRunning}
                    className={cn(
                      "flex-1 py-4 text-[13px] font-bold font-sans tracking-widest uppercase transition-all rounded-md cursor-interactive",
                      isRunning 
                        ? "bg-[var(--surface-secondary)] text-[var(--muted-foreground)] border border-[var(--border)] pointer-events-none"
                        : "bg-[var(--foreground)] text-[var(--background)] hover:bg-[var(--foreground)]/90 shadow-md"
                    )}
                  >
                    Start Simulation
                  </button>
                  <button 
                    onClick={resetSimulation}
                    className="px-10 py-4 border border-[var(--border)] text-[13px] font-bold font-sans tracking-widest text-[var(--foreground)] uppercase hover:bg-[var(--surface-secondary)] transition-colors rounded-md bg-[var(--surface-primary)] cursor-interactive"
                  >
                    Reset State
                  </button>
               </div>

               {/* State visualizer */}
               <div className="pt-10 border-t border-[var(--border)]">
                  <div className="text-[10px] font-bold tracking-widest text-[var(--muted-foreground)] font-sans uppercase mb-8">Internal State Machine</div>
                  
                  <div className="flex items-center space-x-2 w-full overflow-x-auto pb-2 scrollbar-hide">
                     {["NORMAL", "ATTACK_DETECTED", "CLASSIFIED", "MITIGATING", "RECOVERING", "RECOVERED"].map((s, i, arr) => (
                        <React.Fragment key={s}>
                          <div className={cn(
                            "text-[10px] font-sans font-bold tracking-widest px-4 py-2.5 rounded-sm whitespace-nowrap uppercase transition-colors duration-500 border",
                            state === s ? "bg-[var(--status-warning)]/10 text-[var(--status-warning)] border-[var(--status-warning)]/30" : "bg-[var(--surface-primary)] border-[var(--border)] text-[var(--muted-foreground)]"
                          )}>
                             {s}
                          </div>
                          {i < arr.length - 1 && <div className="w-8 h-px bg-[var(--border)] flex-shrink-0" />}
                        </React.Fragment>
                     ))}
                  </div>
               </div>
             </div>
          </section>

        </div>
      </div>
    </div>
  );
}
