"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode, useMemo } from "react";
import { 
  SystemState, TrafficPoint, PredictionResult, MitigationAction, Incident, LogEvent, RuntimeSystemConfig
} from "@/types/sage";
import { defaultPrediction, defaultConfig, generateBaseTraffic, createLog } from "./simulation/engine";
import { useLiveConnection, ConnectionMode } from "./api/wsClient";

interface SageContextType {
  state: SystemState;
  trafficData: TrafficPoint[];
  prediction: PredictionResult;
  mitigations: MitigationAction[];
  incidents: Incident[];
  logs: LogEvent[];
  config: RuntimeSystemConfig;
  connectionMode: ConnectionMode;
  blockedIps: string[];
  simulateAttack: (intensity: "LOW" | "MEDIUM" | "HIGH") => void;
  resetSimulation: () => void;
  // Expose setters for future backend integration without rewriting pages
  dispatchStateUpdate: (newState: any) => void;
}

const SageContext = createContext<SageContextType | undefined>(undefined);

export const SageProvider = ({ children }: { children: ReactNode }) => {
  const [state, setState] = useState<SystemState>("NORMAL");
  const [trafficData, setTrafficData] = useState<TrafficPoint[]>([]);
  const [prediction, setPrediction] = useState<PredictionResult>(defaultPrediction);
  const [mitigations, setMitigations] = useState<MitigationAction[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const [config, setConfig] = useState<RuntimeSystemConfig>(defaultConfig);
  
  const [isSimulating, setIsSimulating] = useState(false);
  const [simIntensity, setSimIntensity] = useState<"LOW" | "MEDIUM" | "HIGH">("MEDIUM");

  // A generalized dispatcher for a future WebSocket adapter to call
  const dispatchStateUpdate = (newState: any) => {
    if (newState.type === 'mitigation') {
      const mitigation = newState.payload as MitigationAction;
      setMitigations(prev => {
        const idx = prev.findIndex(m => m.id === mitigation.id);
        if (idx >= 0) {
          const arr = [...prev];
          arr[idx] = mitigation;
          return arr;
        }
        return [...prev, mitigation];
      });
      return;
    }
    
    if (newState.type === 'telemetry') {
      const point = newState.payload as TrafficPoint;
      setTrafficData(prev => [...prev.slice(1), point]); // Keep sliding window
      return;
    }

    if (newState.state !== undefined) setState(newState.state);
    if (newState.trafficData !== undefined) setTrafficData(newState.trafficData);
    if (newState.prediction !== undefined) setPrediction(newState.prediction);
    if (newState.mitigations !== undefined) setMitigations(newState.mitigations);
    if (newState.incidents !== undefined) setIncidents(newState.incidents);
    if (newState.logs !== undefined) setLogs(newState.logs);
    if (newState.config !== undefined) setConfig(newState.config);
  };

  const connectionMode = useLiveConnection(dispatchStateUpdate);

  const blockedIps = useMemo(() => {
    return mitigations
      .filter(m => m.status === 'ACTIVE' && m.sourceIp)
      .map(m => m.sourceIp as string);
  }, [mitigations]);
  
  // Initialize baseline data
  useEffect(() => {
    if (connectionMode === 'live') return;
    setTrafficData(generateBaseTraffic(60, config.baselineRequestRate));
  }, [config.baselineRequestRate, connectionMode]);

  const addLog = (logItem: Omit<LogEvent, "id" | "time">) => {
    setLogs((prev) => [createLog(logItem), ...prev].slice(0, 100)); // keep last 100
  };

  // ---------------------------------------------------------
  // SIMULATION ENGINE (Can be replaced by WebSocket later)
  // ---------------------------------------------------------
  
  // Traffic Tick
  useEffect(() => {
    if (connectionMode === 'live') return;

    const interval = setInterval(() => {
      setTrafficData((prev) => {
        if (prev.length === 0) return prev;
        const last = prev[prev.length - 1];
        const timestamp = last.timestamp + 1000;
        const date = new Date(timestamp);
        const time = `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`;
        const baseline = config.baselineRequestRate;
        
        const attackTarget = simIntensity === "HIGH" ? 28400 : simIntensity === "MEDIUM" ? 18700 : 9800;
        
        let targetIncoming = baseline;
        let targetOrigin = baseline;

        if (state === "ATTACK_DETECTED" || state === "CLASSIFIED") {
          targetIncoming = attackTarget;
          targetOrigin = attackTarget;
        } else if (state === "MITIGATING") {
          targetIncoming = attackTarget * 0.8;
          targetOrigin = baseline + 800;
        } else if (state === "RECOVERING") {
          targetIncoming = baseline + 1500;
          targetOrigin = baseline + 200;
        } else if (state === "RECOVERED" || state === "NORMAL") {
          targetIncoming = baseline;
          targetOrigin = baseline;
        }

        // Interpolate organically
        let incoming = last.incoming + (targetIncoming - last.incoming) * 0.35 + (Math.random() * 800 - 400);
        let origin = last.origin + (targetOrigin - last.origin) * 0.45 + (Math.random() * 400 - 200);

        if (incoming < baseline - 500) incoming = baseline + (Math.random() * 400 - 200);
        if (origin < baseline - 500) origin = baseline + (Math.random() * 400 - 200);

        let event: string | undefined = undefined;

        if (state === "ATTACK_DETECTED" && last.event !== "ATTACK STARTED" && !prev.find(p => p.event === "ATTACK STARTED")) {
            event = "ATTACK STARTED";
        }

        const newPoint = { time, timestamp, incoming, origin, baseline, event };
        return [...prev.slice(1), newPoint];
      });
    }, config.telemetryRefreshRateMs);

    return () => clearInterval(interval);
  }, [state, simIntensity, config.baselineRequestRate, config.telemetryRefreshRateMs, connectionMode]);

  // State Machine Orchestrator
  useEffect(() => {
    if (!isSimulating || connectionMode === 'live') return;

    let timeoutId: NodeJS.Timeout;

    if (state === "NORMAL") {
      setState("ATTACK_DETECTED");
      setConfig(prev => ({ ...prev, baselineEntropy: 0.31 }));
      setPrediction({ prediction: "Syn", confidence: 89.5, risk: "HIGH" });
      addLog({ severity: "WARN", component: "DETECTION_ENGINE", message: "Traffic rate significantly above baseline" });
    } else if (state === "ATTACK_DETECTED") {
      timeoutId = setTimeout(() => {
        setState("CLASSIFIED");
        setPrediction({ prediction: "Syn", confidence: 99.4, risk: "HIGH" });
        const incidentId = "INC-" + Math.floor(Math.random() * 1000).toString().padStart(3, '0');
        setIncidents([{
          id: incidentId,
          status: "ACTIVE",
          type: "Syn",
          severity: "HIGH",
          start: new Date().toISOString(),
          detectionTime: "1.7s",
          mitigationTime: "-",
          duration: "-",
        }]);
        addLog({ severity: "ALERT", component: "CLASSIFIER", message: "Prediction=SYN Confidence=99.4%", incidentId });
      }, 1700);
    } else if (state === "CLASSIFIED") {
      timeoutId = setTimeout(() => {
        setState("MITIGATING");
        setConfig(prev => ({ ...prev, serverAvailability: 99.2 }));
        setMitigations([
          { id: "1", name: "SYN RATE LIMIT", status: "SIMULATED", result: "ACTIVE" },
          { id: "2", name: "IP FILTER", status: "SIMULATED", result: "1,406 BLOCKED" },
        ]);
        const currentIncident = incidents[0];
        addLog({ severity: "HIGH", component: "DECISION_ENGINE", message: "Action=SYN_RATE_LIMIT", incidentId: currentIncident?.id });
        addLog({ severity: "INFO", component: "MITIGATION_ENGINE", message: "SYN_RATE_LIMIT ACTIVE (SIMULATED)", incidentId: currentIncident?.id });
        setTrafficData(prev => {
            const arr = [...prev];
            arr[arr.length-1] = { ...arr[arr.length-1], event: "MITIGATION ENGAGED" };
            return arr;
        });
      }, 3050);
    } else if (state === "MITIGATING") {
      timeoutId = setTimeout(() => {
        setState("RECOVERING");
        setConfig(prev => ({ ...prev, serverAvailability: 99.7 }));
        addLog({ severity: "INFO", component: "SYSTEM", message: "Traffic reduction observed" });
      }, 5000);
    } else if (state === "RECOVERING") {
      timeoutId = setTimeout(() => {
        setState("RECOVERED");
        setPrediction(defaultPrediction);
        setConfig(defaultConfig); // Restores healthy configs
        setMitigations(m => m.map(x => ({ ...x, status: "COMPLETED" })));
        setIncidents(i => i.map(x => ({ ...x, status: "RESOLVED", duration: "12.4s", mitigationTime: "3.05s" })));
        addLog({ severity: "OK", component: "SYSTEM", message: "Traffic normalized" });
        setTrafficData(prev => {
            const arr = [...prev];
            arr[arr.length-1] = { ...arr[arr.length-1], event: "NORMALIZED" };
            return arr;
        });
        setIsSimulating(false);
      }, 4000);
    }

    return () => clearTimeout(timeoutId);
  }, [state, isSimulating, incidents, connectionMode]);

  const simulateAttack = (intensity: "LOW" | "MEDIUM" | "HIGH") => {
    if (connectionMode === 'live') return;
    if (state !== "NORMAL" && state !== "RECOVERED") return;
    setSimIntensity(intensity);
    setIsSimulating(true);
    if (state === "RECOVERED") {
        setState("NORMAL");
        setConfig(defaultConfig);
    }
  };

  const resetSimulation = () => {
    if (connectionMode === 'live') return;
    setIsSimulating(false);
    setState("NORMAL");
    setPrediction(defaultPrediction);
    setConfig(defaultConfig);
    setMitigations([]);
    setIncidents([]);
    setLogs([]);
    setTrafficData(generateBaseTraffic(60, config.baselineRequestRate));
  };

  return (
    <SageContext.Provider
      value={{
        state,
        trafficData,
        prediction,
        mitigations,
        incidents,
        logs,
        config,
        connectionMode,
        blockedIps,
        simulateAttack,
        resetSimulation,
        dispatchStateUpdate
      }}
    >
      {connectionMode === 'simulation' && (
        <div className="fixed bottom-4 right-4 bg-amber-500/10 border border-amber-500/30 text-amber-500 px-3 py-1.5 rounded-full text-sm font-medium flex items-center gap-2 z-50 backdrop-blur-sm">
          <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
          Simulation Mode
        </div>
      )}
      {children}
    </SageContext.Provider>
  );
};

export const useSage = () => {
  const context = useContext(SageContext);
  if (!context) {
    throw new Error("useSage must be used within a SageProvider");
  }
  return context;
};
