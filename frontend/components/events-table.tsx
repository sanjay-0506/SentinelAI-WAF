'use client';

import { useState } from 'react';
import { format } from 'date-fns';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { LogItem, LogsResponse } from '@/types';
import { ChevronLeft, ChevronRight, ShieldX, ShieldCheck } from 'lucide-react';
import { clsx } from 'clsx';

const attackColors: Record<string, string> = {
  SQLI: 'bg-red-500/15 text-red-400 border-red-500/30',
  XSS: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
  PATH_TRAVERSAL: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
  COMMAND_INJECTION: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
};

const methodColors: Record<string, string> = {
  GET: 'text-blue-400',
  POST: 'text-emerald-400',
  PUT: 'text-amber-400',
  DELETE: 'text-red-400',
  PATCH: 'text-purple-400',
};

interface Props {
  data: LogsResponse | undefined;
  isLoading?: boolean;
  page: number;
  onPageChange: (p: number) => void;
}

export function EventsTable({ data, isLoading, page, onPageChange }: Props) {
  if (isLoading) {
    return (
      <div className="glass-card rounded-xl overflow-hidden">
        <div className="p-4 border-b border-zinc-800">
          <Skeleton className="h-5 w-40 bg-zinc-800" />
        </div>
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="px-4 py-3 border-b border-zinc-800/50 flex gap-4">
            <Skeleton className="h-4 w-32 bg-zinc-800" />
            <Skeleton className="h-4 w-28 bg-zinc-800" />
            <Skeleton className="h-4 w-16 bg-zinc-800" />
            <Skeleton className="h-4 w-48 bg-zinc-800" />
            <Skeleton className="h-4 w-20 bg-zinc-800" />
          </div>
        ))}
      </div>
    );
  }

  if (!data?.items?.length) {
    return (
      <div className="glass-card rounded-xl p-16 flex flex-col items-center justify-center text-center">
        <ShieldCheck className="h-12 w-12 text-zinc-600 mb-4" />
        <p className="text-zinc-400 font-medium">No events found</p>
        <p className="text-zinc-600 text-sm mt-1">Try adjusting your filters</p>
      </div>
    );
  }

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="border-zinc-800 hover:bg-transparent">
              <TableHead className="text-zinc-400 font-medium text-xs uppercase tracking-wider w-40">
                Timestamp
              </TableHead>
              <TableHead className="text-zinc-400 font-medium text-xs uppercase tracking-wider">
                IP Address
              </TableHead>
              <TableHead className="text-zinc-400 font-medium text-xs uppercase tracking-wider w-16">
                Method
              </TableHead>
              <TableHead className="text-zinc-400 font-medium text-xs uppercase tracking-wider">
                Path
              </TableHead>
              <TableHead className="text-zinc-400 font-medium text-xs uppercase tracking-wider w-24">
                Decision
              </TableHead>
              <TableHead className="text-zinc-400 font-medium text-xs uppercase tracking-wider">
                Attack Type
              </TableHead>
              <TableHead className="text-zinc-400 font-medium text-xs uppercase tracking-wider text-right w-24">
                Latency
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.items.map((item: LogItem) => (
              <TableRow
                key={item.request_id}
                className="border-zinc-800/50 hover:bg-zinc-800/30 transition-colors cursor-default"
              >
                <TableCell className="text-zinc-400 text-xs font-mono">
                  {format(new Date(item.created_at), 'MM/dd HH:mm:ss')}
                </TableCell>
                <TableCell className="text-zinc-300 text-sm font-mono">
                  {item.ip_address}
                </TableCell>
                <TableCell>
                  <span
                    className={clsx(
                      'text-xs font-bold font-mono',
                      methodColors[item.method] ?? 'text-zinc-400'
                    )}
                  >
                    {item.method}
                  </span>
                </TableCell>
                <TableCell className="text-zinc-300 text-sm font-mono max-w-[240px] truncate">
                  <span title={item.path}>{item.path}</span>
                </TableCell>
                <TableCell>
                  {item.decision === 'blocked' ? (
                    <div className="flex items-center gap-1.5 text-red-400">
                      <ShieldX className="h-3.5 w-3.5" />
                      <span className="text-xs font-medium">Blocked</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 text-emerald-400">
                      <ShieldCheck className="h-3.5 w-3.5" />
                      <span className="text-xs font-medium">Allowed</span>
                    </div>
                  )}
                </TableCell>
                <TableCell>
                  {item.attack_type ? (
                    <span
                      className={clsx(
                        'inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border',
                        attackColors[item.attack_type] ?? 'bg-zinc-700/50 text-zinc-400 border-zinc-600'
                      )}
                    >
                      {item.attack_type}
                    </span>
                  ) : (
                    <span className="text-zinc-600 text-xs">—</span>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  <span
                    className={clsx(
                      'text-xs font-mono font-medium',
                      item.latency_ms < 10
                        ? 'text-emerald-400'
                        : item.latency_ms < 20
                        ? 'text-amber-400'
                        : 'text-red-400'
                    )}
                  >
                    {item.latency_ms.toFixed(1)}ms
                  </span>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between px-4 py-3 border-t border-zinc-800">
        <p className="text-xs text-zinc-500">
          Showing {(page - 1) * (data.page_size) + 1}–
          {Math.min(page * data.page_size, data.total)} of {data.total.toLocaleString()} events
        </p>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="h-8 w-8 p-0 bg-transparent border-zinc-700 text-zinc-400 hover:bg-zinc-800 hover:text-white disabled:opacity-30"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-xs text-zinc-400 font-medium px-2">
            {page} / {data.pages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(page + 1)}
            disabled={page >= data.pages}
            className="h-8 w-8 p-0 bg-transparent border-zinc-700 text-zinc-400 hover:bg-zinc-800 hover:text-white disabled:opacity-30"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
