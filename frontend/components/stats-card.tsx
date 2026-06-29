'use client';

import { clsx } from 'clsx';
import { LucideIcon } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Skeleton } from '@/components/ui/skeleton';

interface StatsCardProps {
  title: string;
  value: number | undefined;
  icon: LucideIcon;
  color: 'blue' | 'red' | 'emerald' | 'amber';
  trend?: { value: number; label: string };
  isLoading?: boolean;
  suffix?: string;
  format?: 'number' | 'percent';
}

const colorMap = {
  blue: {
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/20',
    icon: 'text-blue-400',
    glow: 'hover:border-blue-500/40 hover:shadow-blue-500/10',
    text: 'text-blue-400',
  },
  red: {
    bg: 'bg-red-500/10',
    border: 'border-red-500/20',
    icon: 'text-red-400',
    glow: 'hover:border-red-500/40 hover:shadow-red-500/10',
    text: 'text-red-400',
  },
  emerald: {
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/20',
    icon: 'text-emerald-400',
    glow: 'hover:border-emerald-500/40 hover:shadow-emerald-500/10',
    text: 'text-emerald-400',
  },
  amber: {
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/20',
    icon: 'text-amber-400',
    glow: 'hover:border-amber-500/40 hover:shadow-amber-500/10',
    text: 'text-amber-400',
  },
};

function useCountUp(target: number, duration = 1200) {
  const [count, setCount] = useState(0);
  const prevTarget = useRef(0);

  useEffect(() => {
    if (target === prevTarget.current) return;
    const start = prevTarget.current;
    const diff = target - start;
    const startTime = performance.now();

    const step = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.round(start + diff * eased));
      if (progress < 1) requestAnimationFrame(step);
      else prevTarget.current = target;
    };

    requestAnimationFrame(step);
  }, [target, duration]);

  return count;
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

export function StatsCard({
  title,
  value,
  icon: Icon,
  color,
  trend,
  isLoading,
  suffix,
  format: fmt = 'number',
}: StatsCardProps) {
  const colors = colorMap[color];
  const animated = useCountUp(value ?? 0);

  if (isLoading) {
    return (
      <div className="glass-card rounded-xl p-6 animate-pulse">
        <Skeleton className="h-4 w-24 mb-4 bg-zinc-800" />
        <Skeleton className="h-10 w-32 mb-2 bg-zinc-800" />
        <Skeleton className="h-3 w-20 bg-zinc-800" />
      </div>
    );
  }

  return (
    <div
      className={clsx(
        'glass-card rounded-xl p-6 transition-all duration-300',
        'hover:scale-[1.02] hover:shadow-xl cursor-default',
        colors.glow
      )}
    >
      <div className="flex items-start justify-between mb-4">
        <p className="text-sm font-medium text-zinc-400">{title}</p>
        <div className={clsx('p-2.5 rounded-lg', colors.bg, 'border', colors.border)}>
          <Icon className={clsx('h-5 w-5', colors.icon)} />
        </div>
      </div>

      <div className="mb-2">
        <span className="text-3xl font-bold text-white tabular-nums">
          {fmt === 'percent'
            ? `${animated.toFixed(1)}%`
            : `${formatNumber(animated)}${suffix ?? ''}`}
        </span>
      </div>

      {trend && (
        <div className="flex items-center gap-1.5">
          <span
            className={clsx(
              'text-xs font-medium px-2 py-0.5 rounded-full',
              trend.value >= 0
                ? 'text-emerald-400 bg-emerald-500/10'
                : 'text-red-400 bg-red-500/10'
            )}
          >
            {trend.value >= 0 ? '+' : ''}
            {trend.value}%
          </span>
          <span className="text-xs text-zinc-500">{trend.label}</span>
        </div>
      )}
    </div>
  );
}
