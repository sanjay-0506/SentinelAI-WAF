'use client';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { Rule, RulesResponse, Severity } from '@/types';
import { clsx } from 'clsx';

const severityConfig: Record<Severity, { label: string; classes: string }> = {
  CRITICAL: {
    label: 'CRITICAL',
    classes: 'bg-red-500/15 text-red-400 border-red-500/30',
  },
  HIGH: {
    label: 'HIGH',
    classes: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
  },
  MEDIUM: {
    label: 'MEDIUM',
    classes: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
  },
  LOW: {
    label: 'LOW',
    classes: 'bg-zinc-700/50 text-zinc-400 border-zinc-600/30',
  },
};

const categoryColors: Record<string, string> = {
  SQLI: 'text-red-400',
  XSS: 'text-orange-400',
  PATH_TRAVERSAL: 'text-yellow-400',
  COMMAND_INJECTION: 'text-purple-400',
};

interface Props {
  data: RulesResponse | undefined;
  isLoading?: boolean;
  categoryFilter?: string;
}

export function RuleStatsTable({ data, isLoading, categoryFilter }: Props) {
  if (isLoading) {
    return (
      <div className="glass-card rounded-xl overflow-hidden">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="px-4 py-3 border-b border-zinc-800/50 flex gap-4">
            <Skeleton className="h-4 w-24 bg-zinc-800" />
            <Skeleton className="h-4 w-48 bg-zinc-800" />
            <Skeleton className="h-4 w-20 bg-zinc-800" />
            <Skeleton className="h-4 w-16 bg-zinc-800" />
            <Skeleton className="h-4 w-28 bg-zinc-800" />
          </div>
        ))}
      </div>
    );
  }

  const rules = data?.rules ?? [];
  const filtered =
    categoryFilter && categoryFilter !== 'all'
      ? rules.filter(
          (r) => r.category.toUpperCase() === categoryFilter.toUpperCase()
        )
      : rules;

  const sorted = [...filtered].sort((a, b) => b.hit_count - a.hit_count);
  const maxHits = sorted[0]?.hit_count ?? 1;

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="border-zinc-800 hover:bg-transparent">
            <TableHead className="text-zinc-400 font-medium text-xs uppercase tracking-wider w-28">
              Rule ID
            </TableHead>
            <TableHead className="text-zinc-400 font-medium text-xs uppercase tracking-wider">
              Name
            </TableHead>
            <TableHead className="text-zinc-400 font-medium text-xs uppercase tracking-wider w-36">
              Category
            </TableHead>
            <TableHead className="text-zinc-400 font-medium text-xs uppercase tracking-wider w-24">
              Severity
            </TableHead>
            <TableHead className="text-zinc-400 font-medium text-xs uppercase tracking-wider w-32 text-right">
              Priority
            </TableHead>
            <TableHead className="text-zinc-400 font-medium text-xs uppercase tracking-wider min-w-[200px]">
              Hit Count
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.length === 0 && (
            <TableRow>
              <TableCell
                colSpan={6}
                className="text-center py-12 text-zinc-500"
              >
                No rules found for this category
              </TableCell>
            </TableRow>
          )}
          {sorted.map((rule: Rule) => {
            const sev = severityConfig[rule.severity] ?? severityConfig.LOW;
            const pct = maxHits > 0 ? (rule.hit_count / maxHits) * 100 : 0;
            return (
              <TableRow
                key={rule.id}
                className="border-zinc-800/50 hover:bg-zinc-800/30 transition-colors"
              >
                <TableCell className="text-zinc-500 text-xs font-mono">
                  {rule.id}
                </TableCell>
                <TableCell>
                  <div>
                    <p className="text-zinc-200 text-sm font-medium">{rule.name}</p>
                    <p className="text-zinc-500 text-xs mt-0.5 truncate max-w-[280px]">
                      {rule.description}
                    </p>
                  </div>
                </TableCell>
                <TableCell>
                  <span
                    className={clsx(
                      'text-xs font-medium font-mono',
                      categoryColors[rule.category] ?? 'text-zinc-400'
                    )}
                  >
                    {rule.category}
                  </span>
                </TableCell>
                <TableCell>
                  <span
                    className={clsx(
                      'inline-flex items-center px-2 py-0.5 rounded-md text-xs font-bold border',
                      sev.classes
                    )}
                  >
                    {sev.label}
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  <span className="text-xs text-zinc-400 font-mono">
                    P{rule.priority}
                  </span>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-500"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="text-xs text-zinc-300 font-mono w-14 text-right">
                      {rule.hit_count.toLocaleString()}
                    </span>
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
