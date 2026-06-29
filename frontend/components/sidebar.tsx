'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  BarChart3,
  Shield,
  BookOpen,
  Activity,
  ShieldAlert,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useHealth } from '@/hooks/use-stats';

const navItems = [
  { href: '/', label: 'Overview', icon: LayoutDashboard },
  { href: '/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/events', label: 'Events', icon: Shield },
  { href: '/rules', label: 'Rules', icon: BookOpen },
  { href: '/metrics', label: 'Metrics', icon: Activity },
];

export function Sidebar() {
  const pathname = usePathname();
  const { data: health } = useHealth();

  const isHealthy =
    health?.status === 'healthy' &&
    health?.postgres === 'ok' &&
    health?.redis === 'ok';

  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-zinc-950 border-r border-zinc-800 flex flex-col z-50">
      {/* Logo */}
      <div className="p-6 border-b border-zinc-800">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 group-hover:bg-blue-500/20 transition-colors">
            <ShieldAlert className="h-6 w-6 text-blue-400" />
          </div>
          <div>
            <span className="text-lg font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              AI-WAF
            </span>
            <p className="text-xs text-zinc-500">Dashboard</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3 px-3">
          Navigation
        </p>
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive =
            href === '/' ? pathname === '/' : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-zinc-800 text-white shadow-lg'
                  : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-100'
              )}
            >
              <Icon
                className={clsx(
                  'h-4 w-4 flex-shrink-0',
                  isActive ? 'text-blue-400' : 'text-zinc-500'
                )}
              />
              {label}
              {isActive && (
                <div className="ml-auto h-1.5 w-1.5 rounded-full bg-blue-400" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Health Status */}
      <div className="p-4 border-t border-zinc-800">
        <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-zinc-900/50 border border-zinc-800">
          <div className="relative flex-shrink-0">
            <div
              className={clsx(
                'h-2.5 w-2.5 rounded-full',
                isHealthy ? 'bg-emerald-400' : 'bg-red-400'
              )}
            />
            {isHealthy && (
              <div className="absolute inset-0 h-2.5 w-2.5 rounded-full bg-emerald-400 animate-ping opacity-75" />
            )}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-zinc-300">
              {health ? (isHealthy ? 'System Healthy' : 'Degraded') : 'Connecting...'}
            </p>
            {health && (
              <p className="text-xs text-zinc-500 truncate">
                v{health.version} · {health.rules_loaded} rules
              </p>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}
