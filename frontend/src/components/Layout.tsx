import { NavLink, Outlet } from 'react-router-dom';
import { Activity, BarChart3, Database, Filter, ShieldCheck, Upload } from 'lucide-react';
import clsx from 'clsx';

const links = [
  { to: '/', label: 'Dashboard', icon: BarChart3 },
  { to: '/import', label: 'Veri İçe Aktarma', icon: Upload },
  { to: '/validation', label: 'Validasyon', icon: ShieldCheck },
  { to: '/records', label: 'Kayıtlar & Filtre', icon: Filter },
  { to: '/sync', label: 'API Senkronizasyon', icon: Database },
];

export default function Layout() {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-5 py-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
              <Activity size={20} />
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-widest text-indigo-600">MAGNA</p>
              <h1 className="text-sm font-bold leading-tight text-slate-800">OEE Takip Paneli</h1>
            </div>
          </div>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                clsx(
                  'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900',
                )
              }
            >
              <Icon size={18} className="shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-slate-100 px-5 py-4">
          <p className="text-xs text-slate-500">Injection Molding</p>
          <p className="text-[10px] text-slate-400">Üretim performans takibi</p>
        </div>
      </aside>

      <div className="ml-64 flex min-h-screen flex-1 flex-col">
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white px-8 py-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-500">
              Üretim Performans &nbsp;·&nbsp; <span className="font-medium text-slate-700">Canlı Dashboard</span>
            </p>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
              Sistem Aktif
            </span>
          </div>
        </header>
        <main className="flex-1 p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
