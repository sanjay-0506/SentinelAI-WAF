import { LogsParams } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost/api/v1';

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  getStats: () => fetchJSON(`${API_BASE}/stats`),
  getLogs: (params: LogsParams = {}) => {
    const searchParams = new URLSearchParams();
    if (params.page) searchParams.set('page', String(params.page));
    if (params.page_size) searchParams.set('page_size', String(params.page_size));
    if (params.decision && params.decision !== 'all') searchParams.set('decision', params.decision);
    if (params.attack_type && params.attack_type !== 'all') searchParams.set('attack_type', params.attack_type);
    const qs = searchParams.toString();
    return fetchJSON(`${API_BASE}/logs${qs ? `?${qs}` : ''}`);
  },
  getRules: () => fetchJSON(`${API_BASE}/rules`),
  getHealth: () => fetchJSON(`${API_BASE}/health`),
  getMetrics: () => fetchJSON(`${API_BASE}/metrics`),
};
