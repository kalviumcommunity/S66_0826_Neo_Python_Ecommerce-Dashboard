import React from 'react';
import Image from 'next/image';
import { LayoutDashboard, Users, ChevronRight, Moon, Sun } from 'lucide-react';
import { PageView } from '../types';

interface SidebarProps {
  activePage: PageView;
  onNavigate: (page: PageView) => void;
  highRiskCount?: number;
  totalSellersCount?: number;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activePage,
  onNavigate,
  highRiskCount = 0,
  theme,
  onToggleTheme,
}) => {
  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between shrink-0 min-h-screen">
      <div>
        {/* Logo Section */}
        <div className="p-5 border-b border-slate-100 flex items-center">
          <Image
            src={theme === 'dark' ? '/neo-insight-symbol-dark.svg' : '/neo-insight-symbol-light.svg'}
            alt="Seller risk analytics logo"
            width={44}
            height={44}
            priority
            className="h-11 w-11 object-contain drop-shadow-sm"
          />
        </div>

        {/* Navigation Menu */}
        <div className="p-4 space-y-1.5">
          <div className="px-3 py-1.5 text-[11px] font-mono font-semibold uppercase tracking-wider text-slate-400">
            Navigation
          </div>

          <button
            onClick={() => onNavigate('Overview')}
            className={`w-[100%] flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
              activePage === 'Overview'
                ? 'bg-slate-100 text-slate-900 font-semibold border border-slate-200 shadow-2xs'
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
            }`}
          >
            <div className="flex items-center space-x-3">
              <LayoutDashboard className={`w-4 h-4 ${activePage === 'Overview' ? 'text-amber-700' : 'text-slate-400'}`} />
              <span>Overview</span>
            </div>
            {activePage === 'Overview' && <ChevronRight className="w-3.5 h-3.5 text-slate-400" />}
          </button>

          <button
            onClick={() => onNavigate('SellerDirectory')}
            className={`w-[100%] flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
              activePage === 'SellerDirectory'
                ? 'bg-slate-100 text-slate-900 font-semibold border border-slate-200 shadow-2xs'
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
            }`}
          >
            <div className="flex items-center space-x-3">
              <Users className={`w-4 h-4 ${activePage === 'SellerDirectory' ? 'text-amber-700' : 'text-slate-400'}`} />
              <span>Seller Directory</span>
            </div>
            {highRiskCount > 0 && (
              <span className="font-mono text-xs font-bold bg-rose-100 text-rose-700 px-2 py-0.5 rounded-full border border-rose-200">
                {highRiskCount}
              </span>
            )}
          </button>
        </div>
      </div>

      <div className="border-t border-slate-100 p-4">
        <button
          type="button"
          onClick={onToggleTheme}
          aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          className="flex w-full items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
        >
          <span className="flex items-center gap-3">
            {theme === 'light' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4 text-amber-500" />}
            {theme === 'light' ? 'Dark mode' : 'Light mode'}
          </span>
          <span className="theme-toggle-track relative h-6 w-10 shrink-0 rounded-full bg-slate-300 transition-colors dark:bg-slate-700">
            <span
              className={`theme-toggle-knob absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform ${
                theme === 'dark' ? 'translate-x-4' : 'translate-x-0'
              }`}
            />
          </span>
        </button>
      </div>
    </aside>
  );
};
