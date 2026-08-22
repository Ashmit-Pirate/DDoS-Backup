"use client";

import { useSage } from "@/lib/store";
import { MODEL_METADATA } from "@/lib/config";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function SettingsPage() {
  const { config } = useSage();

  return (
    <div className="flex flex-col h-full bg-[var(--background)] overflow-y-auto">
      <header className="px-6 lg:px-12 py-8 flex-shrink-0 border-b border-[var(--border)] bg-[var(--surface-primary)]">
        <h1 className="text-2xl font-bold tracking-tight text-[var(--foreground)] font-sans">System Configuration</h1>
      </header>

      <div className="flex-1 px-6 lg:px-12 py-14 flex justify-center">
        <div className="w-full max-w-3xl">
          
          <div className="space-y-16">
            <section>
               <SectionHeader eyebrow="Environment Profile" />
               <div className="space-y-6">
                  <div className="grid grid-cols-12 gap-2 md:gap-8 md:items-center group">
                     <div className="col-span-12 md:col-span-5 text-[14px] font-sans font-medium text-[var(--foreground)] tracking-wide">Target Application</div>
                     <div className="col-span-12 md:col-span-7 text-[14px] font-mono text-[var(--technical-text)] md:text-right break-words">{config.targetApplication}</div>
                  </div>
                  <div className="grid grid-cols-12 gap-2 md:gap-8 md:items-center group">
                     <div className="col-span-12 md:col-span-5 text-[14px] font-sans font-medium text-[var(--foreground)] tracking-wide">Operational Mode</div>
                     <div className="col-span-12 md:col-span-7 md:text-right">
                       <StatusBadge label={config.environment} status="warning" />
                     </div>
                  </div>
                  <div className="grid grid-cols-12 gap-2 md:gap-8 md:items-center group">
                     <div className="col-span-12 md:col-span-5 text-[14px] font-sans font-medium text-[var(--foreground)] tracking-wide">Telemetry Refresh Rate</div>
                     <div className="col-span-12 md:col-span-7 text-[14px] font-mono text-[var(--technical-text)] md:text-right">{config.telemetryRefreshRateMs}ms</div>
                  </div>
               </div>
            </section>

            <section>
               <SectionHeader eyebrow="Detection Engine" />
               <div className="space-y-6">
                  <div className="grid grid-cols-12 gap-2 md:gap-8 md:items-center group">
                     <div className="col-span-12 md:col-span-5 text-[14px] font-sans font-medium text-[var(--foreground)] tracking-wide">Classification Model</div>
                     <div className="col-span-12 md:col-span-7 text-[15px] font-serif font-bold text-[var(--foreground)] md:text-right">{MODEL_METADATA.name}</div>
                  </div>
                  <div className="grid grid-cols-12 gap-2 md:gap-8 md:items-center group">
                     <div className="col-span-12 md:col-span-5 text-[14px] font-sans font-medium text-[var(--foreground)] tracking-wide">Active Feature Count</div>
                     <div className="col-span-12 md:col-span-7 text-[14px] font-mono font-bold text-[var(--status-info)] md:text-right">{MODEL_METADATA.featureCount}</div>
                  </div>
                  <div className="grid grid-cols-12 gap-2 md:gap-8 md:items-center group">
                     <div className="col-span-12 md:col-span-5 text-[14px] font-sans font-medium text-[var(--foreground)] tracking-wide">Trained Threat Classes</div>
                     <div className="col-span-12 md:col-span-7 text-[14px] font-mono font-bold text-[var(--status-info)] md:text-right">{MODEL_METADATA.trainedClasses}</div>
                  </div>
                  <div className="grid grid-cols-12 gap-2 md:gap-8 md:items-center group">
                     <div className="col-span-12 md:col-span-5 text-[14px] font-sans font-medium text-[var(--foreground)] tracking-wide">Model Artifact Path</div>
                     <div className="col-span-12 md:col-span-7 text-[13px] font-mono text-[var(--technical-text)] md:text-right break-all">{MODEL_METADATA.modelArtifactPath}</div>
                  </div>
                  <div className="grid grid-cols-12 gap-2 md:gap-8 md:items-center group">
                     <div className="col-span-12 md:col-span-5 text-[14px] font-sans font-medium text-[var(--foreground)] tracking-wide">Feature Schema Path</div>
                     <div className="col-span-12 md:col-span-7 text-[13px] font-mono text-[var(--technical-text)] md:text-right break-all">{MODEL_METADATA.featureSchemaPath}</div>
                  </div>
               </div>
            </section>

            <section>
               <SectionHeader eyebrow="Mitigation Controller" />
               <div className="space-y-6">
                  <div className="grid grid-cols-12 gap-2 md:gap-8 md:items-center group">
                     <div className="col-span-12 md:col-span-5 text-[14px] font-sans font-medium text-[var(--foreground)] tracking-wide">Execution Mode</div>
                     <div className="col-span-12 md:col-span-7 md:text-right">
                       <StatusBadge label={config.mitigationMode} status={config.mitigationMode === "Simulation Only" ? "warning" : "info"} />
                     </div>
                  </div>
                  
                  <div className="pt-2">
                     <p className="text-[13px] font-sans tracking-wide text-[var(--secondary-foreground)] leading-relaxed bg-[var(--surface-elevated)] p-6 rounded-md border border-[var(--border)] shadow-sm">
                        In simulation mode, the decision engine selects appropriate mitigations based on identified threat vectors but does not enforce them on upstream firewalls. No actual traffic will be dropped.
                     </p>
                  </div>
               </div>
            </section>

          </div>
          
        </div>
      </div>
    </div>
  );
}
