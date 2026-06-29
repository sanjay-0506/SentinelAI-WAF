'use client';

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { useEffect, useState } from 'react';
import { format, subMinutes } from 'date-fns';
import { Skeleton } from '@/components/ui/skeleton';

interface DataPoint {
  time: string;
  requests: number;
  blocked: number;
  allowed: number;
}

interface Props {
  totalRequests?: number;
  blocked?: number;
  allowed?: number;
  isLoading?: boolean;
}

function generateSyntheticTimeline(
  total: number,
  blocked: number,
  allowed: number
): DataPoint[] {
  const points: DataPoint[] = [];
  const now = new Date();

  for (let i = 11; i >= 0; i--) {
    const t = subMinutes(now, i * 5);
    const base = total / 12;
    const variance = base * 0.4;
    const r = Math.max(0, Math.round(base + (Math.random() - 0.5) * variance));
    const blockRate = total > 0 ? blocked / total : 0.3;
    const b = Math.round(r * blockRate);
    points.push({
      time: format(t, 'HH:mm'),
      requests: r,
      blocked: b,
      allowed: r - b,
    });
  }
  return points;
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ dataKey: string; value: number; color: string }>; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-card rounded-lg px-4 py-3 border border-white/10 shadow-2xl min-w-[160px]">
      <p className="text-xs text-zinc-400 mb-2 font-medium">{label}</p>
      {payload.map((p) => (
        <div key={p.dataKey} className="flex items-center justify-between gap-4 text-sm">
          <span style={{ color: p.color }} className="capitalize text-xs">
            {p.dataKey}
          </span>
          <span className="font-bold text-white text-xs">{p.value.toLocaleString()}</span>
        </div>
      ))}
    </div>
  );
}

export function RequestsTimelineChart({ totalRequests, blocked, allowed, isLoading }: Props) {
  const [data, setData] = useState<DataPoint[]>([]);

  useEffect(() => {
    if (totalRequests !== undefined) {
      setData(generateSyntheticTimeline(totalRequests, blocked ?? 0, allowed ?? 0));
    }
  }, [totalRequests, blocked, allowed]);

  // Refresh every 5s to simulate live data
  useEffect(() => {
    if (!totalRequests) return;
    const interval = setInterval(() => {
      setData(generateSyntheticTimeline(totalRequests, blocked ?? 0, allowed ?? 0));
    }, 5000);
    return () => clearInterval(interval);
  }, [totalRequests, blocked, allowed]);

  if (isLoading || !totalRequests) {
    return (
      <div className="glass-card rounded-xl p-6">
        <Skeleton className="h-6 w-48 mb-6 bg-zinc-800" />
        <Skeleton className="h-64 w-full bg-zinc-800 rounded-lg" />
      </div>
    );
  }

  return (
    <div className="glass-card rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-base font-semibold text-white">Requests Timeline</h3>
          <p className="text-sm text-zinc-400 mt-1">Last 60 minutes (5-min intervals)</p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-blue-400" />
            <span className="text-zinc-400">Total</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-red-400" />
            <span className="text-zinc-400">Blocked</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full bg-emerald-400" />
            <span className="text-zinc-400">Allowed</span>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={240}>
        <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="blueGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="redGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="greenGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
          <XAxis
            dataKey="time"
            tick={{ fill: '#71717a', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#71717a', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="requests"
            stroke="#3b82f6"
            strokeWidth={2}
            fill="url(#blueGrad)"
            dot={false}
            activeDot={{ r: 4, fill: '#3b82f6' }}
            isAnimationActive={true}
            animationDuration={600}
          />
          <Area
            type="monotone"
            dataKey="blocked"
            stroke="#ef4444"
            strokeWidth={2}
            fill="url(#redGrad)"
            dot={false}
            activeDot={{ r: 4, fill: '#ef4444' }}
            isAnimationActive={true}
            animationDuration={600}
          />
          <Area
            type="monotone"
            dataKey="allowed"
            stroke="#10b981"
            strokeWidth={1.5}
            fill="url(#greenGrad)"
            dot={false}
            activeDot={{ r: 3, fill: '#10b981' }}
            isAnimationActive={true}
            animationDuration={600}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
