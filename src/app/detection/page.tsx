"use client";

import { useSage } from "@/lib/store";
import { MODEL_METADATA } from "@/lib/config";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { MetricReadout } from "@/components/ui/MetricReadout";
import { StatusBadge } from "@/components/ui/StatusBadge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function DetectionPage() {
  const { state, prediction, config } = useSage();

  const isAttack = state === "ATTACK_DETECTED" || state === "CLASSIFIED" || state === "MITIGATING" || state === "RECOVERING";

  return (
    <div className="flex flex-col h-full bg-[var(--background)] overflow-y-auto">
      <header className="px-6 lg:px-12 py-8 flex-shrink-0 border-b border-[var(--border)] bg-[var(--surface-primary)]">
        <h1 className="text-2xl font-bold tracking-tight text-[var(--foreground)] font-sans">Detection Intelligence</h1>
      </header>

      <div className="flex-1 px-6 lg:px-12 py-10 flex flex-col gap-12 min-w-0">
        
        {/* ML Contribution Workspace */}
        <section className="bg-[var(--surface-elevated)] p-6 lg:p-12 rounded-md border border-[var(--border)] shadow-sm">
           <div className="mb-14">
             <div className="text-[11px] font-bold font-sans tracking-widest text-[var(--status-info)] uppercase mb-4">Active Classification Model</div>
             <div className="text-4xl lg:text-6xl text-[var(--foreground)] font-serif tracking-tight">{MODEL_METADATA.name}</div>
           </div>

           <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-12 mb-14 border-b border-[var(--border)] pb-14">
              <MetricReadout label="Accuracy" value={MODEL_METADATA.metrics.accuracy} unit="%" size="large" className="border-l-2 border-[var(--border)] pl-6" />
              <MetricReadout label="Macro Precision" value={MODEL_METADATA.metrics.precision} unit="%" size="large" className="border-l-2 border-[var(--border)] pl-6" />
              <MetricReadout label="Macro Recall" value={MODEL_METADATA.metrics.recall} unit="%" size="large" className="border-l-2 border-[var(--border)] pl-6" />
              <MetricReadout label="Macro F1" value={MODEL_METADATA.metrics.f1} unit="%" size="large" status="info" className="border-l-2 border-[var(--status-info)] pl-6" />
           </div>

           <div>
              <div className="text-[11px] font-bold font-sans tracking-widest text-[var(--muted-foreground)] uppercase mb-8">Traffic Classification Matrix</div>
              <div className="flex flex-wrap gap-4">
                 {MODEL_METADATA.supportedClasses.map((cls) => {
                   const isActive = prediction.prediction === cls;
                   return (
                     <div key={cls} className={cn(
                       "py-3 px-6 rounded-sm border flex items-center justify-center transition-colors duration-500",
                       isActive && cls === "Benign" ? "bg-[var(--status-healthy)]/10 border-[var(--status-healthy)]/30 text-[var(--status-healthy)]" :
                       isActive ? "bg-[var(--status-attack)]/10 border-[var(--status-attack)]/30 text-[var(--status-attack)] shadow-[0_0_15px_rgba(200,92,92,0.1)]" :
                       "bg-[var(--surface-primary)] border-[var(--border)] text-[var(--secondary-foreground)]"
                     )}>
                        <span className={cn("text-[13px] font-sans tracking-wide", isActive && "font-bold")}>{cls}</span>
                     </div>
                   );
                 })}
              </div>
           </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
           {/* Current Prediction */}
           <section className="bg-[var(--surface-primary)] p-6 lg:p-10 rounded-md border border-[var(--border)] flex flex-col justify-between">
             <SectionHeader eyebrow="Current Intelligence" />
             
             <div className="flex justify-between items-end pb-10 mb-10 border-b border-[var(--border)]">
                <div>
                  <div className="text-[10px] tracking-widest font-sans font-semibold text-[var(--muted-foreground)] mb-3 uppercase">Prediction Target</div>
                  <div className={cn(
                    "text-5xl lg:text-6xl font-serif tracking-tight uppercase leading-none transition-colors duration-500",
                    prediction.prediction === "Benign" ? "text-[var(--status-healthy)]" : "text-[var(--status-attack)]"
                  )}>
                    {prediction.prediction}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] tracking-widest font-sans font-semibold text-[var(--muted-foreground)] mb-3 uppercase">Model Confidence</div>
                  <div className="text-4xl lg:text-5xl font-serif text-[var(--foreground)] tracking-tight">
                    {prediction.confidence.toFixed(1)}<span className="text-2xl text-[var(--secondary-foreground)] ml-1 font-sans">%</span>
                  </div>
                </div>
             </div>
             
             <div className="grid grid-cols-2 gap-8">
                <div>
                  <div className="text-[10px] tracking-widest font-sans font-semibold text-[var(--muted-foreground)] mb-3 uppercase">System Risk Level</div>
                  <StatusBadge 
                    label={prediction.risk} 
                    status={prediction.risk === "HIGH" ? "attack" : prediction.risk === "MEDIUM" ? "warning" : "healthy"} 
                  />
                </div>
                <div>
                  <div className="text-[10px] tracking-widest font-sans font-semibold text-[var(--muted-foreground)] mb-3 uppercase">Analysis Pipeline</div>
                  <div className="font-sans text-[15px] font-medium text-[var(--foreground)] tracking-tight">Real-time Flow Inspection</div>
                </div>
             </div>
           </section>

           {/* Signals */}
           <section className="bg-[var(--surface-primary)] p-6 lg:p-10 rounded-md border border-[var(--border)] overflow-x-auto">
              <SectionHeader eyebrow="Detection Evidence" />
              
              <div className="min-w-[400px] space-y-6">
                 {/* Table Header */}
                 <div className="grid grid-cols-4 gap-4 pb-4 border-b border-[var(--border)]">
                    <div className="text-[10px] tracking-widest font-sans font-semibold text-[var(--muted-foreground)] uppercase">Signal</div>
                    <div className="text-[10px] tracking-widest font-sans font-semibold text-[var(--muted-foreground)] uppercase">Baseline</div>
                    <div className="text-[10px] tracking-widest font-sans font-semibold text-[var(--muted-foreground)] uppercase">Current</div>
                    <div className="text-[10px] tracking-widest font-sans font-semibold text-[var(--muted-foreground)] uppercase text-right">Deviation</div>
                 </div>

                 {/* Rows */}
                 <div className="grid grid-cols-4 gap-4 items-center pb-5 border-b border-[var(--border)] group">
                    <div className="text-[13px] font-sans font-medium text-[var(--foreground)] tracking-wide">Request Rate</div>
                    <div className="text-[13px] font-mono text-[var(--technical-text)]">~{(config.baselineRequestRate / 1000).toFixed(1)}k req/s</div>
                    <div className={cn("text-[13px] font-mono transition-colors", isAttack ? "text-[var(--status-attack)] font-bold" : "text-[var(--foreground)]")}>{isAttack ? ">18.7k req/s" : `${(config.baselineRequestRate / 1000).toFixed(2)}k req/s`}</div>
                    <div className="text-right">
                      <StatusBadge label={isAttack ? "High" : "Normal"} status={isAttack ? "attack" : "healthy"} />
                    </div>
                 </div>

                 <div className="grid grid-cols-4 gap-4 items-center pb-5 border-b border-[var(--border)] group">
                    <div className="text-[13px] font-sans font-medium text-[var(--foreground)] tracking-wide">IP Entropy</div>
                    <div className="text-[13px] font-mono text-[var(--technical-text)]">{config.baselineEntropy}</div>
                    <div className={cn("text-[13px] font-mono transition-colors", prediction.prediction !== "Benign" ? "text-[var(--status-attack)] font-bold" : "text-[var(--foreground)]")}>{prediction.prediction !== "Benign" ? "0.31" : config.baselineEntropy}</div>
                    <div className="text-right">
                      <StatusBadge label={prediction.prediction !== "Benign" ? "Low" : "Normal"} status={prediction.prediction !== "Benign" ? "attack" : "healthy"} />
                    </div>
                 </div>

                 <div className="grid grid-cols-4 gap-4 items-center pb-5 border-b border-[var(--border)] group">
                    <div className="text-[13px] font-sans font-medium text-[var(--foreground)] tracking-wide">Concentration</div>
                    <div className="text-[13px] font-mono text-[var(--technical-text)]">21%</div>
                    <div className={cn("text-[13px] font-mono transition-colors", prediction.prediction !== "Benign" ? "text-[var(--status-warning)] font-bold" : "text-[var(--foreground)]")}>{prediction.prediction !== "Benign" ? "74%" : "22%"}</div>
                    <div className="text-right">
                      <StatusBadge label={prediction.prediction !== "Benign" ? "High" : "Normal"} status={prediction.prediction !== "Benign" ? "warning" : "healthy"} />
                    </div>
                 </div>

                 <div className="grid grid-cols-4 gap-4 items-center group">
                    <div className="text-[13px] font-sans font-medium text-[var(--foreground)] tracking-wide">TCP Behavior</div>
                    <div className="text-[13px] font-mono text-[var(--technical-text)]">Balanced</div>
                    <div className={cn("text-[13px] font-mono transition-colors", prediction.prediction === "Syn" ? "text-[var(--status-attack)] font-bold" : "text-[var(--foreground)]")}>{prediction.prediction === "Syn" ? "SYN Heavy" : "Balanced"}</div>
                    <div className="text-right">
                      <StatusBadge label={prediction.prediction === "Syn" ? "Abnorm" : "Normal"} status={prediction.prediction === "Syn" ? "attack" : "healthy"} />
                    </div>
                 </div>
              </div>
           </section>
        </div>

      </div>
    </div>
  );
}
