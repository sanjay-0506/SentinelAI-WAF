'use client';

import { usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { RefreshCw } from 'lucide-react';

const routeLabels: Record<string, string> = {
  '/': 'Overview',
  '/analytics': 'Analytics',
  '/events': 'Security Events',
  '/rules': 'Rule Engine',
  '/metrics': 'System Metrics',
};

export function Header() {
  const pathname = usePathname();
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [pulse, setPulse] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdated(new Date());
      setPulse(true);
      setTimeout(() => setPulse(false), 600);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const label = routeLabels[pathname] ?? 'Dashboard';

  return (
    <header className="fixed top-0 left-64 right-0 h-16 bg-zinc-950/80 backdrop-blur-md border-b border-zinc-800 flex items-center justify-between px-6 z-40">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm">
        <span className="text-zinc-500">AI-WAF</span>
        <span className="text-zinc-700">/</span>
        <span className="text-zinc-100 font-medium">{label}</span>
      </div>

      {/* Right Side */}
      <div className="flex items-center gap-4">
        {/* Last Updated */}
        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <RefreshCw
            className={`h-3.5 w-3.5 transition-all duration-300 ${pulse ? 'text-blue-400 rotate-180' : ''}`}
          />
          <span>Updated {format(lastUpdated, 'HH:mm:ss')}</span>
        </div>

        {/* LIVE Badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
          <div className="relative">
            <div className="h-2 w-2 rounded-full bg-emerald-400" />
            <div className="absolute inset-0 h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
          </div>
          <span className="text-xs font-semibold text-emerald-400 tracking-widest">
            LIVE
          </span>
        </div>
      </div>
    </header>
  );
}
