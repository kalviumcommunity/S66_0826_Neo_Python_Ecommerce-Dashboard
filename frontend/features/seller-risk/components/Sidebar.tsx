import React from 'react';
import { LayoutDashboard, Users, ShieldAlert, ChevronRight } from 'lucide-react';
import { PageView } from '../types';

interface SidebarProps {
  activePage: PageView;
  onNavigate: (page: PageView) => void;
  highRiskCount?: number;
  totalSellersCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activePage,
  onNavigate,
  highRiskCount = 0,
}) => {
  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between shrink-0 min-h-screen">
      <div>
        {/* Logo Section */}
        <div className="p-5 border-b border-slate-100 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-700 font-bold">
            <ShieldAlert className="w-5 h-5 text-amber-700" />
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <span className="font-bold text-slate-900 text-base tracking-tight">Neo</span>
              <span className="font-mono text-xs font-semibold px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200">
                TRUST
              </span>
            </div>
          </div>
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
    </aside>
  );
};
