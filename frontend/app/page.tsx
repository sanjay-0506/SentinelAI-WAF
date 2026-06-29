'use client';

import { Activity, ShieldX, ShieldCheck, Zap } from 'lucide-react';
import { StatsCard } from '@/components/stats-card';
import { RequestsTimelineChart } from '@/components/requests-timeline-chart';
import { AttackBreakdownChart } from '@/components/attack-breakdown-chart';
import { useStats } from '@/hooks/use-stats';
import { format } from 'date-fns';
import { Skeleton } from '@/components/ui/skeleton';

function RecentBlockedMini({ data, isLoading }: { data?: Array<{ path: string; attack_type: string; created_at: string; ip_address: string }>; isLoading?: boolean }) {
  const attackColors: Record<string, string> = {
    SQLI: 'text-red-400',
    XSS: 'text-orange-400',
    PATH_TRAVERSAL: 'text-yellow-400',
    COMMAND_INJECTION: 'text-purple-400',
  };

  return (
    <div className="glass-card rounded-xl p-6 h-full">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-white">Recent Blocks</h3>
        <p className="text-sm text-zinc-400 mt-1">Latest blocked requests</p>
      </div>
      <div className="space-y-3">
        {isLoading
          ? Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex gap-3">
                <Skeleton className="h-4 w-24 bg-zinc-800" />
                <Skeleton className="h-4 flex-1 bg-zinc-800" />
              </div>
            ))
          : (data ?? []).slice(0, 8).map((item, i) => (
              <div
                key={i}
                className="flex items-start gap-3 py-2 border-b border-zinc-800/50 last:border-0"
              >
                <div className="flex-shrink-0 mt-0.5">
                  <ShieldX className="h-3.5 w-3.5 text-red-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span
                      className={`text-xs font-bold font-mono ${attackColors[item.attack_type] ?? 'text-zinc-400'}`}
                    >
                      {item.attack_type}
                    </span>
                    <span className="text-xs text-zinc-600">·</span>
                    <span className="text-xs text-zinc-500 font-mono">
                      {item.ip_address}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-400 font-mono truncate">
                    {item.path}
                  </p>
                  <p className="text-xs text-zinc-600 mt-0.5">
                    {format(new Date(item.created_at), 'HH:mm:ss')}
                  </p>
                </div>
              </div>
            ))}
        {!isLoading && (!data || data.length === 0) && (
          <div className="py-8 text-center">
            <ShieldCheck className="h-8 w-8 text-emerald-500 mx-auto mb-2" />
            <p className="text-zinc-500 text-sm">No recent blocks</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function OverviewPage() {
  const { data: stats, isLoading, error } = useStats();

  const totalAttacks = stats
    ? Object.values(stats.attack_breakdown).reduce((a, b) => a + b, 0)
    : 0;

  const blockRate =
    stats?.total_requests && stats.total_requests > 0
      ? ((stats.blocked / stats.total_requests) * 100).toFixed(1)
      : '0';

  return (
    <div className="space-y-6 fade-in">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-bold animated-gradient-text inline-block">
          Dashboard Overview
        </h1>
        <p className="text-zinc-400 text-sm mt-1">
          Real-time AI-WAF monitoring and threat intelligence
        </p>
      </div>

      {/* Error State */}
      {error && !isLoading && (
        <div className="glass-card rounded-xl p-4 border border-red-500/20 bg-red-500/5">
          <p className="text-red-400 text-sm font-medium">
            ⚠ Unable to connect to backend API. Make sure the server is running at{' '}
            <code className="font-mono text-xs">http://localhost/api/v1</code>
          </p>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 fade-in-delay-1">
        <StatsCard
          title="Total Requests"
          value={stats?.total_requests}
          icon={Activity}
          color="blue"
          isLoading={isLoading}
        />
        <StatsCard
          title="Blocked"
          value={stats?.blocked}
          icon={ShieldX}
          color="red"
          isLoading={isLoading}
          trend={stats ? { value: parseFloat(blockRate), label: 'block rate' } : undefined}
        />
        <StatsCard
          title="Allowed"
          value={stats?.allowed}
          icon={ShieldCheck}
          color="emerald"
          isLoading={isLoading}
        />
        <StatsCard
          title="Unique Attack Types"
          value={totalAttacks}
          icon={Zap}
          color="amber"
          isLoading={isLoading}
        />
      </div>

      {/* Timeline Chart */}
      <div className="fade-in-delay-2">
        <RequestsTimelineChart
          totalRequests={stats?.total_requests}
          blocked={stats?.blocked}
          allowed={stats?.allowed}
          isLoading={isLoading}
        />
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 fade-in-delay-3">
        <AttackBreakdownChart
          data={stats?.attack_breakdown}
          isLoading={isLoading}
        />
        <RecentBlockedMini
          data={stats?.recent_blocked}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
