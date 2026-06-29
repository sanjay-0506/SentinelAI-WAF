'use client';

import { useState } from 'react';
import { EventsTable } from '@/components/events-table';
import { useLogs } from '@/hooks/use-stats';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Shield } from 'lucide-react';

const PAGE_SIZE = 20;

const ATTACK_TYPES = [
  { value: 'all', label: 'All Attack Types' },
  { value: 'SQLI', label: 'SQL Injection' },
  { value: 'XSS', label: 'Cross-Site Scripting' },
  { value: 'PATH_TRAVERSAL', label: 'Path Traversal' },
  { value: 'COMMAND_INJECTION', label: 'Command Injection' },
];

const DECISIONS = [
  { value: 'all', label: 'All Decisions' },
  { value: 'blocked', label: 'Blocked Only' },
  { value: 'allowed', label: 'Allowed Only' },
];

export default function EventsPage() {
  const [page, setPage] = useState(1);
  const [decision, setDecision] = useState('all');
  const [attackType, setAttackType] = useState('all');

  const { data, isLoading } = useLogs({
    page,
    page_size: PAGE_SIZE,
    decision,
    attack_type: attackType,
  });

  const handleDecisionChange = (val: string | null) => {
    setDecision(val ?? 'all');
    setPage(1);
  };

  const handleAttackTypeChange = (val: string | null) => {
    setAttackType(val ?? 'all');
    setPage(1);
  };

  return (
    <div className="space-y-6 fade-in">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold animated-gradient-text inline-block">
            Security Events
          </h1>
          <p className="text-zinc-400 text-sm mt-1">
            Real-time log of all WAF decisions · Auto-refreshing every 5s
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <Shield className="h-4 w-4" />
          <span>{data?.total?.toLocaleString() ?? '—'} total events</span>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 fade-in-delay-1">
        <Select value={decision} onValueChange={handleDecisionChange}>
          <SelectTrigger className="w-40 bg-zinc-900 border-zinc-700 text-zinc-200 h-9 text-sm">
            <SelectValue placeholder="Decision" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-900 border-zinc-700 text-zinc-200">
            {DECISIONS.map((d) => (
              <SelectItem key={d.value} value={d.value} className="hover:bg-zinc-800 focus:bg-zinc-800">
                {d.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={attackType} onValueChange={handleAttackTypeChange}>
          <SelectTrigger className="w-52 bg-zinc-900 border-zinc-700 text-zinc-200 h-9 text-sm">
            <SelectValue placeholder="Attack Type" />
          </SelectTrigger>
          <SelectContent className="bg-zinc-900 border-zinc-700 text-zinc-200">
            {ATTACK_TYPES.map((a) => (
              <SelectItem key={a.value} value={a.value} className="hover:bg-zinc-800 focus:bg-zinc-800">
                {a.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {(decision !== 'all' || attackType !== 'all') && (
          <button
            onClick={() => {
              setDecision('all');
              setAttackType('all');
              setPage(1);
            }}
            className="text-xs text-zinc-400 hover:text-zinc-200 underline underline-offset-2 transition-colors"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Events Table */}
      <div className="fade-in-delay-2">
        <EventsTable
          data={data}
          isLoading={isLoading}
          page={page}
          onPageChange={setPage}
        />
      </div>
    </div>
  );
}
