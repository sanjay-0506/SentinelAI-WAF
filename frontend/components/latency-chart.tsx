'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Cell,
  ResponsiveContainer,
} from 'recharts';
import { Skeleton } from '@/components/ui/skeleton';

interface Props {
  p50?: number;
  p95?: number;
  p99?: number;
  isLoading?: boolean;
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: { name: string; value: number; color: string } }>;
}) {
  if (!active || !payload?.length) return null;
  const { name, value, color } = payload[0].payload;
  return (
    <div className="glass-card rounded-lg px-4 py-3 border border-white/10 shadow-2xl">
      <p className="text-xs text-zinc-400 mb-1">{name}</p>
      <p className="text-lg font-bold" style={{ color }}>
        {value.toFixed(2)}ms
      </p>
      <p className="text-xs text-zinc-500">
        {value < 10 ? '✓ Excellent' : value < 20 ? '⚠ Acceptable' : '✗ High'}
      </p>
    </div>
  );
}

function getColor(value: number): string {
  if (value < 10) return '#10b981'; // green
  if (value < 20) return '#f59e0b'; // amber
  return '#ef4444'; // red
}

export function LatencyChart({ p50, p95, p99, isLoading }: Props) {
  if (isLoading || p50 === undefined) {
    return (
      <div className="glass-card rounded-xl p-6">
        <Skeleton className="h-6 w-48 mb-6 bg-zinc-800" />
        <Skeleton className="h-48 w-full bg-zinc-800 rounded-lg" />
      </div>
    );
  }

  const data = [
    { name: 'P50 (Median)', value: p50 ?? 0, color: getColor(p50 ?? 0) },
    { name: 'P95', value: p95 ?? 0, color: getColor(p95 ?? 0) },
    { name: 'P99', value: p99 ?? 0, color: getColor(p99 ?? 0) },
  ];

  return (
    <div className="glass-card rounded-xl p-6">
      <div className="mb-6">
        <h3 className="text-base font-semibold text-white">Request Latency</h3>
        <p className="text-sm text-zinc-400 mt-1">
          Percentile distribution (ms) · Target P95 &lt; 20ms
        </p>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <BarChart
          data={data}
          margin={{ top: 10, right: 20, left: -10, bottom: 0 }}
          barSize={56}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fill: '#71717a', fontSize: 12 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#71717a', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            unit="ms"
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
          <ReferenceLine
            y={20}
            stroke="#f59e0b"
            strokeDasharray="6 3"
            strokeWidth={1.5}
            label={{
              value: '20ms target',
              fill: '#f59e0b',
              fontSize: 11,
              position: 'insideTopRight',
            }}
          />
          <Bar dataKey="value" radius={[6, 6, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={index} fill={entry.color} fillOpacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Latency breakdown */}
      <div className="grid grid-cols-3 gap-4 mt-6 pt-4 border-t border-zinc-800">
        {data.map((item) => (
          <div key={item.name} className="text-center">
            <p className="text-xs text-zinc-500 mb-1">{item.name.split(' ')[0]}</p>
            <p className="text-xl font-bold font-mono" style={{ color: item.color }}>
              {item.value.toFixed(1)}
            </p>
            <p className="text-xs text-zinc-500">ms</p>
          </div>
        ))}
      </div>
    </div>
  );
}
