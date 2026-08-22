"use client";

import { useSage } from "@/lib/store";
import { 
  AreaChart, 
  Area, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea
} from "recharts";

export default function TrafficGraph() {
  const { trafficData, state } = useSage();

  if (!trafficData || trafficData.length === 0) {
    return <div className="h-[300px] w-full flex items-center justify-center text-[10px] font-mono tracking-widest text-[var(--technical-text)] uppercase">Awaiting Telemetry...</div>;
  }

  // Find events to plot as reference lines
  const events = trafficData.filter(d => d.event);
  const isAttack = ["ATTACK_DETECTED", "CLASSIFIED", "MITIGATING"].includes(state);
  const attackStartEvent = events.find(e => e.event === "ATTACK STARTED");

  return (
    <div className="w-full h-full min-h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={trafficData} margin={{ top: 30, right: 30, left: 10, bottom: 5 }}>
          <defs>
            <linearGradient id="colorIncoming" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--status-info)" stopOpacity={0.25}/>
              <stop offset="95%" stopColor="var(--status-info)" stopOpacity={0}/>
            </linearGradient>
          </defs>
          
          {isAttack && attackStartEvent && (
            <ReferenceArea 
              x1={attackStartEvent.time}
              fill="var(--status-attack)"
              fillOpacity={0.03}
            />
          )}
          
          <CartesianGrid strokeDasharray="0" stroke="var(--border)" vertical={false} opacity={0.6} />
          
          <XAxis 
            dataKey="time" 
            stroke="var(--technical-text)" 
            fontSize={10}
            tickLine={false}
            axisLine={false}
            minTickGap={40}
            fontFamily="var(--font-mono)"
            dy={10}
          />
          
          <YAxis 
            stroke="var(--technical-text)"
            fontSize={10}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => `${(value / 1000).toFixed(1)}k`}
            width={45}
            fontFamily="var(--font-mono)"
          />
          
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'var(--surface-elevated)', 
              border: '1px solid var(--border)',
              borderRadius: '4px',
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              boxShadow: '0 4px 20px rgba(0,0,0,0.05)',
              padding: '12px 16px'
            }}
            itemStyle={{ color: 'var(--foreground)', paddingTop: '4px' }}
            labelStyle={{ color: 'var(--muted-foreground)', marginBottom: '8px', borderBottom: '1px solid var(--border)', paddingBottom: '4px' }}
          />

          <Area 
            type="monotone" 
            dataKey="incoming" 
            name="Incoming Traffic"
            stroke="var(--status-info)" 
            strokeWidth={2} 
            fillOpacity={1}
            fill="url(#colorIncoming)"
            dot={false}
            isAnimationActive={false} 
          />
          
          <Line 
            type="stepAfter" 
            dataKey="origin" 
            name="Traffic to Origin"
            stroke="var(--status-data)" 
            strokeWidth={1.5} 
            dot={false}
            isAnimationActive={false} 
          />
          
          <ReferenceLine 
            y={4200} 
            stroke="var(--technical-text)" 
            strokeDasharray="2 4" 
            strokeOpacity={0.6}
            label={{ position: 'insideTopLeft', value: 'BASELINE', fill: 'var(--technical-text)', fontSize: 10, fontFamily: 'var(--font-mono)', opacity: 0.6 }}
          />

          {events.map((ev, i) => {
             let color = "var(--status-info)"; 
             let eventLabel = ev.event;
             if (ev.event === "ATTACK STARTED") color = "var(--status-attack)";
             else if (ev.event === "MITIGATION ENGAGED") {
                 color = "var(--status-warning)";
                 eventLabel = "MITIGATION";
             }
             else if (ev.event === "NORMALIZED") {
                 color = "var(--status-healthy)";
                 eventLabel = "RECOVERED";
             }

             return (
               <ReferenceLine
                 key={i}
                 x={ev.time}
                 stroke={color}
                 strokeDasharray="0"
                 strokeOpacity={0.8}
                 label={{
                   position: 'insideTopLeft',
                   value: eventLabel,
                   fill: color,
                   fontSize: 9,
                   fontFamily: 'var(--font-mono)',
                   fontWeight: 'bold'
                 }}
               />
             );
          })}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
