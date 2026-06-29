'use client';

import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { AttackBreakdown } from '@/types';
import { Skeleton } from '@/components/ui/skeleton';

const ATTACK_COLORS = {
  SQLI: '#ef4444',
  XSS: '#f97316',
  PATH_TRAVERSAL: '#eab308',
  COMMAND_INJECTION: '#a855f7',
};

const ATTACK_LABELS = {
  SQLI: 'SQL Injection',
  XSS: 'Cross-Site Scripting',
  PATH_TRAVERSAL: 'Path Traversal',
  COMMAND_INJECTION: 'Command Injection',
};

interface Props {
  data: AttackBreakdown | undefined;
  isLoading?: boolean;
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ name: string; value: number; payload: { fill: string } }> }) {
  if (!active || !payload?.length) return null;
  const item = payload[0];
  return (
    <div className="glass-card rounded-lg px-4 py-3 border border-white/10 shadow-2xl">
      <p className="text-xs text-zinc-400 mb-1">{item.name}</p>
      <p className="text-lg font-bold text-white">{item.value.toLocaleString()}</p>
      <p className="text-xs" style={{ color: item.payload.fill }}>
        attacks detected
      </p>
    </div>
  );
}

export function AttackBreakdownChart({ data, isLoading }: Props) {
  if (isLoading || !data) {
    return (
      <div className="glass-card rounded-xl p-6">
        <Skeleton className="h-6 w-48 mb-6 bg-zinc-800" />
        <Skeleton className="h-64 w-full bg-zinc-800 rounded-lg" />
      </div>
    );
  }

  const chartData = Object.entries(data).map(([key, value]) => ({
    name: ATTACK_LABELS[key as keyof typeof ATTACK_LABELS] || key,
    shortName: key,
    value,
    fill: ATTACK_COLORS[key as keyof typeof ATTACK_COLORS] || '#6b7280',
  }));

  const total = chartData.reduce((sum, d) => sum + d.value, 0);

  return (
    <div className="glass-card rounded-xl p-6">
      <div className="mb-6">
        <h3 className="text-base font-semibold text-white">Attack Breakdown</h3>
        <p className="text-sm text-zinc-400 mt-1">
          {total.toLocaleString()} total attacks detected
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Donut Chart */}
        <div className="flex-1 relative">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={3}
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={index} fill={entry.fill} stroke="transparent" />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          {/* Center label */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-2xl font-bold text-white">
              {total >= 1000 ? `${(total / 1000).toFixed(1)}K` : total}
            </span>
            <span className="text-xs text-zinc-500">Total</span>
          </div>
        </div>

        {/* Legend + Bar */}
        <div className="flex-1 space-y-3">
          {chartData.map((item) => {
            const pct = total > 0 ? ((item.value / total) * 100).toFixed(1) : '0';
            return (
              <div key={item.shortName} className="space-y-1.5">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span
                      className="inline-block h-2.5 w-2.5 rounded-sm"
                      style={{ backgroundColor: item.fill }}
                    />
                    <span className="text-zinc-300 text-xs">{item.shortName}</span>
                  </div>
                  <span className="text-zinc-400 text-xs font-mono">
                    {item.value.toLocaleString()} ({pct}%)
                  </span>
                </div>
                <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: item.fill,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Bar chart at bottom */}
      <div className="mt-6 pt-4 border-t border-zinc-800">
        <ResponsiveContainer width="100%" height={100}>
          <BarChart data={chartData} barSize={24}>
            <XAxis
              dataKey="shortName"
              tick={{ fill: '#71717a', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis hide />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={index} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
