// Attack types
export type AttackType = 'SQLI' | 'XSS' | 'PATH_TRAVERSAL' | 'COMMAND_INJECTION';
export type Decision = 'allowed' | 'blocked';
export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

// Stats API
export interface AttackBreakdown {
  SQLI: number;
  XSS: number;
  PATH_TRAVERSAL: number;
  COMMAND_INJECTION: number;
}

export interface RecentBlocked {
  path: string;
  attack_type: AttackType;
  created_at: string;
  ip_address: string;
}

export interface StatsResponse {
  total_requests: number;
  blocked: number;
  allowed: number;
  attack_breakdown: AttackBreakdown;
  recent_blocked: RecentBlocked[];
}

// Logs API
export interface LogItem {
  request_id: string;
  ip_address: string;
  method: string;
  path: string;
  decision: Decision;
  attack_type: AttackType | null;
  severity: string | null;
  confidence: number | null;
  fingerprint: string | null;
  latency_ms: number;
  user_agent: string | null;
  request_size: number | null;
  created_at: string;
}

export interface LogsResponse {
  items: LogItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface LogsParams {
  page?: string | number;
  page_size?: string | number;
  decision?: string;
  attack_type?: string;
}

// Rules API
export interface Rule {
  id: string;
  name: string;
  category: string;
  severity: Severity;
  priority: number;
  description: string;
  hit_count: number;
  version: number;
}

export interface RulesResponse {
  ruleset_version: string;
  rules: Rule[];
}

// Health API
export interface HealthResponse {
  status: string;
  postgres: string;
  redis: string;
  rules_loaded: number;
  ruleset_version: string;
  version: string;
  uptime_seconds: number;
}

// Metrics API
export interface MetricsResponse {
  requests_total: number;
  blocked_total: number;
  allowed_total: number;
  block_rate: number;
  sqli_total: number;
  xss_total: number;
  path_traversal_total: number;
  command_injection_total: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  latency_p99_ms: number;
  uptime_seconds: number;
  rules_loaded: number;
}
