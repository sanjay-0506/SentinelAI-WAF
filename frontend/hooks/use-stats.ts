'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import {
  StatsResponse,
  LogsResponse,
  RulesResponse,
  HealthResponse,
  MetricsResponse,
  LogsParams,
} from '@/types';

export function useStats() {
  return useQuery<StatsResponse>({
    queryKey: ['stats'],
    queryFn: api.getStats as () => Promise<StatsResponse>,
    refetchInterval: 5000,
    staleTime: 4000,
  });
}

export function useLogs(params: LogsParams = {}) {
  return useQuery<LogsResponse>({
    queryKey: ['logs', params],
    queryFn: () => api.getLogs(params) as Promise<LogsResponse>,
    refetchInterval: 5000,
    staleTime: 4000,
  });
}

export function useRules() {
  return useQuery<RulesResponse>({
    queryKey: ['rules'],
    queryFn: api.getRules as () => Promise<RulesResponse>,
    refetchInterval: 30000,
    staleTime: 25000,
  });
}

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: api.getHealth as () => Promise<HealthResponse>,
    refetchInterval: 10000,
    staleTime: 8000,
  });
}

export function useMetrics() {
  return useQuery<MetricsResponse>({
    queryKey: ['metrics'],
    queryFn: api.getMetrics as () => Promise<MetricsResponse>,
    refetchInterval: 5000,
    staleTime: 4000,
  });
}
