'use client';

import { Database, Code2, FolderOpen, Terminal } from 'lucide-react';
import { AttackBreakdownChart } from '@/components/attack-breakdown-chart';
import { StatsCard } from '@/components/stats-card';
import { useStats, useMetrics } from '@/hooks/use-stats';
import { Skeleton } from '@/components/ui/skeleton';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from 'recharts';

const ATTACK_CONFIG = [
  {
    key: 'SQLI',
    label: 'SQL Injection',
    icon: Database,
    color: 'red' as const,
    metricKey: 'sqli_total' as const,
    description: 'Attempts to inject malicious SQL code',
  },
  {
    key: 'XSS',
    label: 'Cross-Site Scripting',
    icon: Code2,
    color: 'amber' as const,
    metricKey: 'xss_total' as const,
    description: 'Client-side script injection attacks',
  },
  {
    key: 'PATH_TRAVERSAL',
    label: 'Path Traversal',
    icon: FolderOpen,
    color: 'amber' as const,
    metricKey: 'path_traversal_total' as const,
    description: 'Directory traversal / file inclusion attempts',
  },
  {
    key: 'COMMAND_INJECTION',
    label: 'Command Injection',
    icon: Terminal,
    color: 'red' as const,
    metricKey: 'command_injection_total' as const,
    description: 'OS-level command execution attempts',
  },
];

const ATTACK_COLORS: Record<string, string> = {
  SQLI: '#ef4444',
  XSS: '#f97316',
  PATH_TRAVERSAL: '#eab308',
  COMMAND_INJECTION: '#a855f7',
};

function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: { name: string; value: number; fill: string } }> }) {
  if (!active || !payload?.length) return null;
  const { name, value, fill } = payload[0].payload;
  return (
    <div className="glass-card rounded-lg px-4 py-3 border border-white/10 shadow-2xl">
      <p className="text-xs text-zinc-400 mb-1">{name}</p>
      <p className="text-lg font-bold text-white">{value.toLocaleString()}</p>
      <p className="text-xs" style={{ color: fill }}>attacks</p>
    </div>
  );
}

export default function AnalyticsPage() {
  const { data: stats, isLoading: statsLoading } = useStats();
  const { data: metrics, isLoading: metricsLoading } = useMetrics();

  const isLoading = statsLoading || metricsLoading;

  const barData = ATTACK_CONFIG.map((a) => ({
    name: a.key,
    value: metrics?.[a.metricKey] ?? stats?.attack_breakdown?.[a.key as keyof typeof stats.attack_breakdown] ?? 0,
    fill: ATTACK_COLORS[a.key],
  }));

  const blockRate = metrics?.block_rate
    ? (metrics.block_rate * 100).toFixed(1)
    : stats?.total_requests
    ? ((stats.blocked / stats.total_requests) * 100).toFixed(1)
    : '0';

  return (
    <div className="space-y-6 fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold animated-gradient-text inline-block">
          Attack Analytics
        </h1>
        <p className="text-zinc-400 text-sm mt-1">
          Comprehensive breakdown of detected threats and attack patterns
        </p>
      </div>

      {/* Attack Type Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 fade-in-delay-1">
        {ATTACK_CONFIG.map(({ key, label, icon: Icon, color, metricKey }) => (
          <StatsCard
            key={key}
            title={label}
            value={metrics?.[metricKey] ?? stats?.attack_breakdown?.[key as keyof typeof stats.attack_breakdown]}
            icon={Icon}
            color={color}
            isLoading={isLoading}
          />
        ))}
      </div>

      {/* Block Rate Card */}
      {!isLoading && (
        <div className="glass-card rounded-xl p-4 fade-in-delay-1">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-zinc-300">Overall Block Rate</span>
            <span className="text-lg font-bold text-red-400">{blockRate}%</span>
          </div>
          <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-red-600 to-red-400 rounded-full transition-all duration-700"
              style={{ width: `${Math.min(parseFloat(blockRate), 100)}%` }}
            />
          </div>
          <p className="text-xs text-zinc-500 mt-2">
            {metrics?.blocked_total?.toLocaleString() ?? stats?.blocked?.toLocaleString() ?? 0} blocked out of{' '}
            {metrics?.requests_total?.toLocaleString() ?? stats?.total_requests?.toLocaleString() ?? 0} total requests
          </p>
        </div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 fade-in-delay-2">
        {/* Donut + breakdown */}
        <AttackBreakdownChart
          data={stats?.attack_breakdown}
          isLoading={isLoading}
        />

        {/* Comparative Bar Chart */}
        <div className="glass-card rounded-xl p-6">
          <div className="mb-6">
            <h3 className="text-base font-semibold text-white">Attack Volume Comparison</h3>
            <p className="text-sm text-zinc-400 mt-1">Total detections by attack category</p>
          </div>
          {isLoading ? (
            <Skeleton className="h-64 w-full bg-zinc-800 rounded-lg" />
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={barData} barSize={48} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#71717a', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#71717a', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                  {barData.map((entry, index) => (
                    <Cell key={index} fill={entry.fill} fillOpacity={0.85} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Description Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 fade-in-delay-3">
        {ATTACK_CONFIG.map(({ key, label, icon: Icon, description }) => (
          <div key={key} className="glass-card rounded-xl p-4 flex items-start gap-4">
            <div
              className="p-2.5 rounded-lg flex-shrink-0"
              style={{ backgroundColor: `${ATTACK_COLORS[key]}15`, border: `1px solid ${ATTACK_COLORS[key]}30` }}
            >
              <Icon className="h-5 w-5" style={{ color: ATTACK_COLORS[key] }} />
            </div>
            <div>
              <p className="text-sm font-semibold text-white">{label}</p>
              <p className="text-xs text-zinc-400 mt-1">{description}</p>
              <p className="text-sm font-bold mt-2" style={{ color: ATTACK_COLORS[key] }}>
                {(
                  metrics?.[ATTACK_CONFIG.find((a) => a.key === key)!.metricKey] ??
                  stats?.attack_breakdown?.[key as keyof typeof stats.attack_breakdown] ??
                  0
                ).toLocaleString()}{' '}
                <span className="text-xs font-normal text-zinc-500">detected</span>
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
