'use client';

import { useState } from 'react';
import { RuleStatsTable } from '@/components/rule-stats-table';
import { useRules } from '@/hooks/use-stats';
import { clsx } from 'clsx';
import { BookOpen, Tag } from 'lucide-react';

const CATEGORIES = [
  { value: 'all', label: 'All' },
  { value: 'SQLI', label: 'SQLI' },
  { value: 'XSS', label: 'XSS' },
  { value: 'PATH_TRAVERSAL', label: 'Path Traversal' },
  { value: 'COMMAND_INJECTION', label: 'Command Injection' },
];

const categoryColors: Record<string, string> = {
  SQLI: 'data-[active=true]:border-red-500 data-[active=true]:text-red-400 data-[active=true]:bg-red-500/10',
  XSS: 'data-[active=true]:border-orange-500 data-[active=true]:text-orange-400 data-[active=true]:bg-orange-500/10',
  PATH_TRAVERSAL: 'data-[active=true]:border-yellow-500 data-[active=true]:text-yellow-400 data-[active=true]:bg-yellow-500/10',
  COMMAND_INJECTION: 'data-[active=true]:border-purple-500 data-[active=true]:text-purple-400 data-[active=true]:bg-purple-500/10',
  all: 'data-[active=true]:border-blue-500 data-[active=true]:text-blue-400 data-[active=true]:bg-blue-500/10',
};

export default function RulesPage() {
  const [category, setCategory] = useState('all');
  const { data, isLoading } = useRules();

  const totalHits = data?.rules.reduce((sum, r) => sum + r.hit_count, 0) ?? 0;
  const filteredCount =
    category === 'all'
      ? (data?.rules.length ?? 0)
      : (data?.rules.filter((r) => r.category.toUpperCase() === category).length ?? 0);

  return (
    <div className="space-y-6 fade-in">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold animated-gradient-text inline-block">
            Rule Engine
          </h1>
          <p className="text-zinc-400 text-sm mt-1">
            Active detection rules sorted by effectiveness
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Ruleset Version */}
          {data?.ruleset_version && (
            <div className="flex items-center gap-2 px-3 py-1.5 glass-card rounded-lg">
              <Tag className="h-3.5 w-3.5 text-blue-400" />
              <span className="text-xs font-mono text-zinc-300">
                v{data.ruleset_version}
              </span>
            </div>
          )}
          {/* Total Rules */}
          <div className="flex items-center gap-2 px-3 py-1.5 glass-card rounded-lg">
            <BookOpen className="h-3.5 w-3.5 text-emerald-400" />
            <span className="text-xs text-zinc-300 font-medium">
              {data?.rules.length ?? '—'} rules
            </span>
          </div>
          {/* Total Hits */}
          <div className="flex items-center gap-2 px-3 py-1.5 glass-card rounded-lg">
            <span className="text-xs text-zinc-300 font-medium">
              {totalHits.toLocaleString()} total hits
            </span>
          </div>
        </div>
      </div>

      {/* Category Tabs */}
      <div className="flex flex-wrap gap-2 fade-in-delay-1">
        {CATEGORIES.map(({ value, label }) => (
          <button
            key={value}
            data-active={category === value}
            onClick={() => setCategory(value)}
            className={clsx(
              'px-4 py-1.5 rounded-lg text-sm font-medium border transition-all duration-200',
              'border-zinc-700 text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200',
              categoryColors[value]
            )}
          >
            {label}
            {value !== 'all' && data && (
              <span className="ml-2 text-xs opacity-60">
                ({data.rules.filter((r) => r.category.toUpperCase() === value).length})
              </span>
            )}
          </button>
        ))}
        {category !== 'all' && (
          <span className="text-xs text-zinc-500 self-center ml-2">
            Showing {filteredCount} rules
          </span>
        )}
      </div>

      {/* Rule Stats Table */}
      <div className="fade-in-delay-2">
        <RuleStatsTable
          data={data}
          isLoading={isLoading}
          categoryFilter={category}
        />
      </div>
    </div>
  );
}
