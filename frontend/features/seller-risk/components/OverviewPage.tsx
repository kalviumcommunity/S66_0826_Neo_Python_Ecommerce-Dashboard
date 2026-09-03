import React from 'react';
import {
  TrendingDown,
  AlertCircle,
  Truck,
  Star,
  XCircle,
  Users,
  Download,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Legend,
  ReferenceLine,
} from 'recharts';
import { MarketplaceMetrics, PrimaryRiskDriver } from '../types';
import { formatCategoryName } from '../utils/csvExport';

interface OverviewPageProps {
  metrics: MarketplaceMetrics;
  onNavigateToDirectoryWithFilter?: (driverFilter?: PrimaryRiskDriver, categoryFilter?: string) => void;
  onOpenExportModal?: () => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  metrics,
  onNavigateToDirectoryWithFilter,
  onOpenExportModal,
}) => {
  const highRiskCount = metrics.highRiskSellers;
  const highRiskTrend = metrics.highRiskTrendPct;
  const riskTierData = metrics.riskTierDistribution;
  const categoryRiskData = metrics.topCategoriesByRisk.map((c) => ({
    ...c,
    formattedCategory: formatCategoryName(c.category),
  }));

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* Top Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="font-bold text-slate-900 text-xl tracking-tight">Operational Overview</h1>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Marketplace-wide seller health, category risk distributions, and operational anomaly detection.
          </p>
        </div>

        {onOpenExportModal && (
          <button
            onClick={onOpenExportModal}
            className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-[#35260E] text-white hover:bg-[#251a09] transition-colors flex items-center space-x-1.5 shadow-2xs self-start md:self-auto cursor-pointer"
            title="Export Marketplace and Seller Data to CSV"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Data (CSV/JSON)</span>
          </button>
        )}
      </div>

      {/* KPI Row (5 Cards) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Sellers */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs flex flex-col justify-between space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-semibold uppercase text-slate-400">Total Sellers</span>
            <div className="w-7 h-7 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold font-sans text-slate-900">{metrics.totalSellers.toLocaleString()}</div>
            <p className="text-[11px] text-slate-500 mt-0.5">Active merchants on platform</p>
          </div>
        </div>

        {/* High-Risk Sellers */}
        <div className={`p-4 rounded-xl border shadow-2xs flex flex-col justify-between space-y-2 transition-all ${
          highRiskCount > 0 ? 'bg-white border-rose-200' : 'bg-emerald-50/50 border-emerald-200'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-semibold uppercase text-slate-400">High-Risk Sellers</span>
            <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${
              highRiskCount > 0 ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'
            }`}>
              <AlertCircle className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="flex items-baseline space-x-2">
              <span className={`text-2xl font-bold font-sans ${highRiskCount > 0 ? 'text-rose-600' : 'text-emerald-700'}`}>
                {highRiskCount}
              </span>
              {highRiskCount > 0 && (
                <span className="inline-flex items-center text-xs font-mono font-semibold text-emerald-600">
                  <TrendingDown className="w-3.5 h-3.5 mr-0.5" />
                  {highRiskTrend}%
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {highRiskCount > 0 ? 'Risk score > 70 threshold' : '0 sellers exceed risk limit'}
            </p>
          </div>
        </div>

        {/* Avg Review Score */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs flex flex-col justify-between space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-semibold uppercase text-slate-400">Avg Review Score</span>
            <div className="w-7 h-7 rounded-lg bg-amber-500/10 text-amber-700 flex items-center justify-center">
              <Star className="w-4 h-4 fill-amber-500 text-amber-500" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold font-sans text-slate-900">{metrics.avgReviewScore} <span className="text-sm font-normal text-slate-400">/ 5.0</span></div>
            <p className="text-[11px] text-slate-500 mt-0.5">Across 100k+ customer orders</p>
          </div>
        </div>

        {/* Late Delivery Rate */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs flex flex-col justify-between space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-semibold uppercase text-slate-400">Late Delivery %</span>
            <div className="w-7 h-7 rounded-lg bg-orange-100 text-orange-700 flex items-center justify-center">
              <Truck className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold font-sans text-slate-900">{metrics.lateDeliveryRate}%</div>
            <p className="text-[11px] text-slate-500 mt-0.5">Carrier estimate delay</p>
          </div>
        </div>

        {/* Cancellation Rate */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs flex flex-col justify-between space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-semibold uppercase text-slate-400">Cancellation Rate</span>
            <div className="w-7 h-7 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center">
              <XCircle className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold font-sans text-slate-900">{metrics.cancellationRate}%</div>
            <p className="text-[11px] text-slate-500 mt-0.5">Merchant initiated cancels</p>
          </div>
        </div>
      </div>

      {/* 2x2 Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Line Chart - Avg Review Score Trend */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-slate-900 text-base">Avg Review Score Trend</h3>
              <p className="text-xs text-slate-500">Monthly progression (2016 – 2018) vs 4.0 target score</p>
            </div>
            <div className="flex items-center space-x-3 text-xs font-mono">
              <span className="flex items-center text-amber-700">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-600 mr-1.5 inline-block"></span> Score
              </span>
              <span className="flex items-center text-slate-400">
                <span className="w-2.5 h-0.5 bg-slate-400 mr-1.5 inline-block"></span> Target 4.0
              </span>
            </div>
          </div>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics.monthlyReviewScoreTrend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis domain={[3.5, 4.5]} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderRadius: '12px', borderColor: '#e2e8f0', fontSize: '12px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                  formatter={(val) => [`${val} Rating`, 'Average Score']}
                />
                <ReferenceLine y={4.0} stroke="#94a3b8" strokeDasharray="4 4" />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#35260E"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#35260E' }}
                  activeDot={{ r: 6, fill: '#35260E' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Bar Chart - Sellers per Risk Tier */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-slate-900 text-base">Sellers per Risk Tier</h3>
              <p className="text-xs text-slate-500">Distribution across Low (&lt;30), Medium (30-70), High (&gt;70) risk score brackets</p>
            </div>
            <span className="text-xs font-mono text-slate-400">3,095 Total</span>
          </div>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskTierData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="tier" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderRadius: '12px', borderColor: '#e2e8f0', fontSize: '12px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                  formatter={(value) => [`${value} Sellers`, 'Count']}
                />
                <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                  {riskTierData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 3: Donut Chart - Review Score Distribution */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-slate-900 text-base">Review Score Distribution</h3>
              <p className="text-xs text-slate-500">Share of 1★ to 5★ ratings across historical orders</p>
            </div>
            <span className="text-xs font-mono text-[11px] text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-semibold">
              77% Positive
            </span>
          </div>

          <div className="h-64 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={metrics.starDistribution}
                  dataKey="count"
                  nameKey="stars"
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={3}
                >
                  {metrics.starDistribution.map((entry, index) => {
                    const colors = ['#10B981', '#3B82F6', '#F59E0B', '#F97316', '#EF4444'];
                    return <Cell key={`star-${index}`} fill={colors[index % colors.length]} />;
                  })}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderRadius: '12px', borderColor: '#e2e8f0', fontSize: '12px' }}
                  formatter={(value) => [`${Number(value ?? 0).toLocaleString()} reviews`, 'Total']}
                />
                <Legend
                  layout="horizontal"
                  verticalAlign="bottom"
                  align="center"
                  formatter={(value) => <span className="text-xs font-mono text-slate-600">{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 4: Horizontal Bar Chart - Top Categories by Risk */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-slate-900 text-base">Top Categories by Risk</h3>
              <p className="text-xs text-slate-500">
                Click any bar to filter and view sellers in that category
              </p>
            </div>
            <span className="text-xs font-mono text-slate-400">Risk Meter (0-100)</span>
          </div>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                layout="vertical"
                data={categoryRiskData}
                margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis
                  dataKey="formattedCategory"
                  type="category"
                  tick={{ fontSize: 11, fill: '#334155', cursor: 'pointer' }}
                  width={140}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderRadius: '12px', borderColor: '#e2e8f0', fontSize: '12px' }}
                  formatter={(val, _name, item) => [
                    `${val} Avg Risk (${item.payload.highRiskSellerCount} Sellers)`,
                    'Category Risk',
                  ]}
                  labelFormatter={(label) => `Category: ${label} (Click to Filter)`}
                />
                <Bar
                  onClick={(_, index) => onNavigateToDirectoryWithFilter?.(undefined, categoryRiskData[index].category)}
                  dataKey="avgRiskScore"
                  fill="#35260E"
                  radius={[0, 6, 6, 0]}
                  barSize={16}
                  cursor="pointer"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
