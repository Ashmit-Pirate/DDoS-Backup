import { useEffect, useRef, useState, useCallback } from 'react';

export type ConnectionMode = 'live' | 'simulation';

export const useLiveConnection = (dispatchStateUpdate: (newState: any) => void) => {
  const [connectionMode, setConnectionMode] = useState<ConnectionMode>('simulation');
  
  // Use a ref to always have the latest dispatchStateUpdate without triggering re-renders
  const dispatchRef = useRef(dispatchStateUpdate);
  useEffect(() => {
    dispatchRef.current = dispatchStateUpdate;
  }, [dispatchStateUpdate]);

  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef(0);

  const connect = useCallback(async () => {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL;
    const wsBase = process.env.NEXT_PUBLIC_WS_URL;

    if (!apiBase || !wsBase) {
      console.warn("API or WS URL missing. Staying in simulation mode.");
      scheduleRetry();
      return;
    }

    try {
      // 1. Hydrate via REST
      const [statusRes, eventsRes, mitigationsRes, configRes] = await Promise.all([
        fetch(`${apiBase}/api/v1/status`),
        fetch(`${apiBase}/api/v1/events`),
        fetch(`${apiBase}/api/v1/mitigation/active`),
        fetch(`${apiBase}/api/v1/config`)
      ]);

      if (!statusRes.ok || !eventsRes.ok || !mitigationsRes.ok || !configRes.ok) {
        throw new Error("Hydration failed");
      }

      const statusData = await statusRes.json();
      const eventsData = await eventsRes.json();
      const mitigationsData = await mitigationsRes.json();
      const configData = await configRes.json();

      dispatchRef.current({
        state: statusData.state,
        incidents: eventsData.incidents,
        logs: eventsData.logs,
        mitigations: mitigationsData,
        config: configData
      });

      // 2. Connect to WS
      const ws = new WebSocket(`${wsBase}/ws/live`);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnectionMode('live');
        retryCountRef.current = 0; // Reset retry count on success
      };

      ws.onmessage = (event) => {
        try {
          const { type, data } = JSON.parse(event.data);
          
          if (type === 'status_change') {
            dispatchRef.current({ state: data });
          } else if (type === 'detection') {
            dispatchRef.current({ prediction: data });
          } else if (type === 'mitigation') {
            // Need to handle updating just one mitigation or all? 
            // The instruction says "mitigation event shape: { id, name, status, result, sourceIp }".
            // So data is a SINGLE MitigationAction.
            // But we need to update the mitigations array. 
            // So we'll pass a function to dispatchRef to indicate a functional update is needed, or we just handle it here.
            dispatchRef.current({ type: 'mitigation', payload: data });
          } else if (type === 'telemetry') {
            dispatchRef.current({ type: 'telemetry', payload: data });
          }
        } catch (e) {
          console.error("Error parsing WS message", e);
        }
      };

      ws.onclose = () => {
        setConnectionMode('simulation');
        scheduleRetry();
      };

      ws.onerror = () => {
        // Error will trigger close, so just let onclose handle retry
      };

    } catch (error) {
      console.warn("Failed to connect or hydrate:", error);
      scheduleRetry();
    }
  }, []);

  const scheduleRetry = useCallback(() => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
    }
    
    // Exponential backoff: 5s, 10s, 20s, capped at 30s
    const backoff = Math.min(5000 * Math.pow(2, retryCountRef.current), 30000);
    retryCountRef.current += 1;
    
    retryTimeoutRef.current = setTimeout(() => {
      connect();
    }, backoff);
  }, [connect]);

  useEffect(() => {
    // Initial connection attempt
    connect();

    return () => {
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.onclose = null; // Prevent scheduling retry on intentional unmount close
        wsRef.current.close();
      }
    };
  }, [connect]);

  return connectionMode;
};
