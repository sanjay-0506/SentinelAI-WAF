'use client';

import { useState } from 'react';
import { useMetrics, useHealth } from '@/hooks/use-stats';
import { LatencyChart } from '@/components/latency-chart';
import { StatsCard } from '@/components/stats-card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Activity,
  Database,
  Server,
  Clock,
  BookOpen,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { clsx } from 'clsx';

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m ${s}s`;
  return `${m}m ${s}s`;
}

function MetricBadge({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="glass-card rounded-lg px-4 py-3 flex items-center gap-3">
      <div className={clsx('h-2 w-2 rounded-full flex-shrink-0', color)} />
      <div className="min-w-0">
        <p className="text-xs text-zinc-500">{label}</p>
        <p className="text-sm font-semibold text-zinc-100 font-mono">{value}</p>
      </div>
    </div>
  );
}

export default function MetricsPage() {
  const { data: metrics, isLoading: metricsLoading } = useMetrics();
  const { data: health, isLoading: healthLoading } = useHealth();
  const [jsonExpanded, setJsonExpanded] = useState(false);

  const isLoading = metricsLoading || healthLoading;

  const blockRate = metrics?.block_rate
    ? `${(metrics.block_rate * 100).toFixed(2)}%`
    : '—';

  return (
    <div className="space-y-6 fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold animated-gradient-text inline-block">
          System Metrics
        </h1>
        <p className="text-zinc-400 text-sm mt-1">
          Performance, health, and operational telemetry
        </p>
      </div>

      {/* System Info Row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 fade-in-delay-1">
        <MetricBadge
          label="Uptime"
          value={health ? formatUptime(health.uptime_seconds) : '—'}
          color="bg-emerald-400"
        />
        <MetricBadge
          label="Version"
          value={health?.version ?? '—'}
          color="bg-blue-400"
        />
        <MetricBadge
          label="Rules Loaded"
          value={String(health?.rules_loaded ?? metrics?.rules_loaded ?? '—')}
          color="bg-purple-400"
        />
        <MetricBadge
          label="Ruleset"
          value={`v${health?.ruleset_version ?? '—'}`}
          color="bg-amber-400"
        />
        <MetricBadge
          label="PostgreSQL"
          value={health?.postgres ?? '—'}
          color={health?.postgres === 'ok' ? 'bg-emerald-400' : 'bg-red-400'}
        />
        <MetricBadge
          label="Redis"
          value={health?.redis ?? '—'}
          color={health?.redis === 'ok' ? 'bg-emerald-400' : 'bg-red-400'}
        />
        <MetricBadge
          label="Block Rate"
          value={blockRate}
          color="bg-red-400"
        />
        <MetricBadge
          label="Status"
          value={health?.status ?? '—'}
          color={health?.status === 'healthy' ? 'bg-emerald-400' : 'bg-amber-400'}
        />
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 fade-in-delay-2">
        <StatsCard
          title="Total Requests"
          value={metrics?.requests_total}
          icon={Activity}
          color="blue"
          isLoading={isLoading}
        />
        <StatsCard
          title="Total Blocked"
          value={metrics?.blocked_total}
          icon={Server}
          color="red"
          isLoading={isLoading}
        />
        <StatsCard
          title="Total Allowed"
          value={metrics?.allowed_total}
          icon={Database}
          color="emerald"
          isLoading={isLoading}
        />
        <StatsCard
          title="Rules Active"
          value={metrics?.rules_loaded}
          icon={BookOpen}
          color="amber"
          isLoading={isLoading}
        />
      </div>

      {/* Latency Chart */}
      <div className="fade-in-delay-2">
        <LatencyChart
          p50={metrics?.latency_p50_ms}
          p95={metrics?.latency_p95_ms}
          p99={metrics?.latency_p99_ms}
          isLoading={isLoading}
        />
      </div>

      {/* Attack Counter Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 fade-in-delay-3">
        {[
          { label: 'SQL Injection', value: metrics?.sqli_total, color: '#ef4444' },
          { label: 'XSS', value: metrics?.xss_total, color: '#f97316' },
          { label: 'Path Traversal', value: metrics?.path_traversal_total, color: '#eab308' },
          { label: 'Command Injection', value: metrics?.command_injection_total, color: '#a855f7' },
        ].map(({ label, value, color }) => (
          <div key={label} className="glass-card rounded-xl p-4">
            <div
              className="text-xs font-semibold mb-2"
              style={{ color }}
            >
              {label}
            </div>
            {isLoading ? (
              <Skeleton className="h-8 w-24 bg-zinc-800" />
            ) : (
              <p className="text-2xl font-bold text-white font-mono">
                {(value ?? 0).toLocaleString()}
              </p>
            )}
            <p className="text-xs text-zinc-500 mt-1">total detections</p>
          </div>
        ))}
      </div>

      {/* Uptime counter */}
      <div className="glass-card rounded-xl p-6 fade-in-delay-3">
        <div className="flex items-center gap-3 mb-4">
          <Clock className="h-5 w-5 text-blue-400" />
          <h3 className="text-base font-semibold text-white">System Uptime</h3>
        </div>
        {isLoading ? (
          <Skeleton className="h-12 w-48 bg-zinc-800" />
        ) : (
          <div>
            <p className="text-4xl font-bold text-white font-mono">
              {health ? formatUptime(health.uptime_seconds) : '—'}
            </p>
            <p className="text-sm text-zinc-400 mt-2">
              {metrics?.uptime_seconds?.toLocaleString() ?? health?.uptime_seconds?.toLocaleString() ?? '0'} seconds
            </p>
          </div>
        )}
      </div>

      {/* Raw JSON Viewer */}
      <div className="glass-card rounded-xl overflow-hidden fade-in-delay-4">
        <button
          onClick={() => setJsonExpanded(!jsonExpanded)}
          className="w-full flex items-center justify-between p-4 text-left hover:bg-zinc-800/30 transition-colors"
        >
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-zinc-300">Raw API Response</span>
            <span className="text-xs text-zinc-500 px-2 py-0.5 bg-zinc-800 rounded">JSON</span>
          </div>
          {jsonExpanded ? (
            <ChevronUp className="h-4 w-4 text-zinc-400" />
          ) : (
            <ChevronDown className="h-4 w-4 text-zinc-400" />
          )}
        </button>
        {jsonExpanded && (
          <div className="border-t border-zinc-800">
            <div className="p-4">
              <p className="text-xs text-zinc-500 mb-2 font-mono">GET /metrics</p>
              <pre className="text-xs text-zinc-300 font-mono overflow-x-auto bg-zinc-900/50 p-4 rounded-lg max-h-96 overflow-y-auto">
                {JSON.stringify(metrics, null, 2)}
              </pre>
            </div>
            <div className="p-4 border-t border-zinc-800">
              <p className="text-xs text-zinc-500 mb-2 font-mono">GET /health</p>
              <pre className="text-xs text-zinc-300 font-mono overflow-x-auto bg-zinc-900/50 p-4 rounded-lg">
                {JSON.stringify(health, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
