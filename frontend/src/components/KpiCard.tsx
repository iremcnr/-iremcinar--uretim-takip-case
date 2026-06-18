import type { LucideIcon } from 'lucide-react';
import clsx from 'clsx';

type KpiCardProps = {
  label: string;
  value: string | number;
  suffix?: string;
  icon: LucideIcon;
  trend?: string;
  variant?: 'indigo' | 'cyan' | 'amber' | 'rose';
};

const variants = {
  indigo: { icon: 'bg-indigo-50 text-indigo-600', accent: 'border-indigo-200' },
  cyan: { icon: 'bg-sky-50 text-sky-600', accent: 'border-sky-200' },
  amber: { icon: 'bg-amber-50 text-amber-600', accent: 'border-amber-200' },
  rose: { icon: 'bg-rose-50 text-rose-600', accent: 'border-rose-200' },
};

export default function KpiCard({ label, value, suffix = '', icon: Icon, trend, variant = 'indigo' }: KpiCardProps) {
  const v = variants[variant];
  return (
    <div className={clsx('rounded-xl border bg-white p-5 shadow-sm', v.accent)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
            {value}
            {suffix && <span className="ml-1 text-lg font-semibold text-slate-500">{suffix}</span>}
          </p>
          {trend && <p className="mt-1 text-xs text-slate-400">{trend}</p>}
        </div>
        <div className={clsx('rounded-lg p-2.5', v.icon)}>
          <Icon size={22} />
        </div>
      </div>
    </div>
  );
}
