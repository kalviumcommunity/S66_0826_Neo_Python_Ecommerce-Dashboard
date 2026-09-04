import React, { useState } from 'react';
import {
  TrendingDown,
  TrendingUp,
  AlertCircle,
  Truck,
  Star,
  XCircle,
  Users,
  Download,
  Layers,
  Info,
  ChevronDown,
  ChevronUp,
  Filter,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
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
  // Progressive Disclosure States
  const [viewMode, setViewMode] = useState<'full' | 'executive'>('full');
  const [showPyramidGuide, setShowPyramidGuide] = useState(false);
  const [isLevel4Expanded, setIsLevel4Expanded] = useState(false);

  const highRiskCount = metrics.highRiskSellers;
  const highRiskTrend = metrics.highRiskTrendPct;
  const riskTierData = metrics.riskTierDistribution;
  const categoryRiskData = metrics.topCategoriesByRisk.map((c) => ({
    ...c,
    formattedCategory: formatCategoryName(c.category),
  }));

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* Top Header Bar & Progressive Disclosure Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs">
        <div>
          <div className="flex items-center space-x-2.5">
            <h1 className="font-bold text-slate-900 text-xl tracking-tight">Operational Overview</h1>
            <span className="inline-flex items-center text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
              Information Pyramid Design
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Hierarchical decision architecture: status KPIs (L1), longitudinal trends (L2), segment risks (L3), and granular drill-downs (L4).
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 self-start md:self-auto">
          {/* Progressive Disclosure Toggle: Executive vs Full */}
          <div className="inline-flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200/80 text-xs">
            <button
              onClick={() => setViewMode('executive')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer ${
                viewMode === 'executive'
                  ? 'bg-white text-slate-900 font-semibold shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
              title="Focus on Level 1 (KPIs) and Level 2 (Trends) only to prevent cognitive overload"
            >
              Executive View
            </button>
            <button
              onClick={() => setViewMode('full')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer ${
                viewMode === 'full'
                  ? 'bg-white text-slate-900 font-semibold shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
              title="Full multi-level information pyramid with segment breakdowns and drill-downs"
            >
              Full Analytical View
            </button>
          </div>

          <button
            onClick={() => setShowPyramidGuide(!showPyramidGuide)}
            className="px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 transition-colors flex items-center space-x-1.5 cursor-pointer"
            title="View information pyramid design principles"
          >
            <Layers className="w-3.5 h-3.5 text-slate-500" />
            <span>Architecture</span>
            {showPyramidGuide ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>

          {onOpenExportModal && (
            <button
              onClick={onOpenExportModal}
              className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-[#35260E] text-white hover:bg-[#251a09] transition-colors flex items-center space-x-1.5 shadow-2xs cursor-pointer"
              title="Export Marketplace and Seller Data to CSV/JSON"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Data</span>
            </button>
          )}
        </div>
      </div>

      {/* Information Pyramid Methodology Guide (Progressive Disclosure) */}
      {showPyramidGuide && (
        <div className="bg-slate-900 text-slate-100 p-5 rounded-2xl border border-slate-800 shadow-md animate-in fade-in duration-200">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-2">
              <Info className="w-4 h-4 text-amber-400" />
              <h3 className="font-semibold text-sm tracking-tight text-white">Dashboard Thinking: The 4-Level Information Pyramid</h3>
            </div>
            <button
              onClick={() => setShowPyramidGuide(false)}
              className="text-xs text-slate-400 hover:text-white"
            >
              Close
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-3 text-xs text-slate-300">
            <div className="bg-slate-800/80 p-3 rounded-xl border border-slate-700">
              <span className="font-bold text-amber-400 block mb-1">Level 1: Status (KPIs)</span>
              <p className="text-[11px] text-slate-300 leading-relaxed">
                Answers: <em>&quot;Are we on track?&quot;</em> Maximum 5 core metrics scanned in seconds with explicit benchmarks and targets.
              </p>
            </div>
            <div className="bg-slate-800/80 p-3 rounded-xl border border-slate-700">
              <span className="font-bold text-sky-400 block mb-1">Level 2: Trends</span>
              <p className="text-[11px] text-slate-300 leading-relaxed">
                Answers: <em>&quot;Is it getting better or worse?&quot;</em> Longitudinal time-series curves comparing actuals against target lines.
              </p>
            </div>
            <div className="bg-slate-800/80 p-3 rounded-xl border border-slate-700">
              <span className="font-bold text-emerald-400 block mb-1">Level 3: Segments</span>
              <p className="text-[11px] text-slate-300 leading-relaxed">
                Answers: <em>&quot;Which parts need attention?&quot;</em> Categorical risk tiers and product category cross-sections.
              </p>
            </div>
            <div className="bg-slate-800/80 p-3 rounded-xl border border-slate-700">
              <span className="font-bold text-rose-400 block mb-1">Level 4: Detail</span>
              <p className="text-[11px] text-slate-300 leading-relaxed">
                Answers: <em>&quot;Show me everything.&quot;</em> Progressive disclosure of granular seller records, filters, and raw data export.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* LEVEL 1: STATUS (KPIs) - "Are we on track?" (Max 5 Metrics with Context)  */}
      {/* ========================================================================= */}
      <section className="space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-amber-500"></span>
            <h2 className="text-xs font-mono font-bold uppercase text-slate-500 tracking-wider">
              Level 1: Platform Health &amp; Executive Status
            </h2>
          </div>
          <span className="text-[11px] text-slate-400">Context-first metrics: target benchmarks, delta indicators, and status badges</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* KPI 1: Total Sellers */}
          <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs flex flex-col justify-between space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-semibold uppercase text-slate-400">Total Sellers</span>
              <div className="w-7 h-7 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center">
                <Users className="w-4 h-4" />
              </div>
            </div>
            <div>
              <div className="text-2xl font-bold font-sans text-slate-900">{metrics.totalSellers.toLocaleString()}</div>
              <div className="flex items-center justify-between mt-1 text-[11px]">
                <span className="text-slate-500">Active merchant base</span>
                <span className="inline-flex items-center text-emerald-700 font-medium font-mono">
                  <TrendingUp className="w-3 h-3 mr-0.5" /> +4.2% YoY
                </span>
              </div>
            </div>
          </div>

          {/* KPI 2: High-Risk Sellers (With Target & Alert Metaphor) */}
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
                <span className="inline-flex items-center text-[10px] font-semibold px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200">
                  Target &lt; 20
                </span>
              </div>
              <div className="flex items-center justify-between mt-1 text-[11px]">
                <span className="text-slate-500">Score &gt; 70 threshold</span>
                <span className="inline-flex items-center text-emerald-600 font-mono font-semibold">
                  <TrendingDown className="w-3 h-3 mr-0.5" />
                  {highRiskTrend}% MoM
                </span>
              </div>
            </div>
          </div>

          {/* KPI 3: Avg Review Score (With Target Reference Context) */}
          <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs flex flex-col justify-between space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-semibold uppercase text-slate-400">Avg Review Score</span>
              <div className="w-7 h-7 rounded-lg bg-amber-500/10 text-amber-700 flex items-center justify-center">
                <Star className="w-4 h-4 fill-amber-500 text-amber-500" />
              </div>
            </div>
            <div>
              <div className="flex items-baseline space-x-2">
                <div className="text-2xl font-bold font-sans text-slate-900">{metrics.avgReviewScore} <span className="text-sm font-normal text-slate-400">/ 5.0</span></div>
                <span className="inline-flex items-center text-[10px] font-semibold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="w-2.5 h-2.5 mr-0.5" /> On Target (≥4.0)
                </span>
              </div>
              <div className="flex items-center justify-between mt-1 text-[11px]">
                <span className="text-slate-500">100k+ customer orders</span>
                <span className="text-emerald-600 font-mono font-medium">+0.05 vs Q2</span>
              </div>
            </div>
          </div>

          {/* KPI 4: Late Delivery Rate (With Target Context) */}
          <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs flex flex-col justify-between space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-semibold uppercase text-slate-400">Late Delivery %</span>
              <div className="w-7 h-7 rounded-lg bg-orange-100 text-orange-700 flex items-center justify-center">
                <Truck className="w-4 h-4" />
              </div>
            </div>
            <div>
              <div className="flex items-baseline space-x-2">
                <div className="text-2xl font-bold font-sans text-slate-900">{metrics.lateDeliveryRate}%</div>
                <span className="inline-flex items-center text-[10px] font-semibold px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
                  Target &lt; 8.0%
                </span>
              </div>
              <div className="flex items-center justify-between mt-1 text-[11px]">
                <span className="text-slate-500">Carrier estimate delay</span>
                <span className="text-emerald-600 font-mono font-medium">-0.4% MoM</span>
              </div>
            </div>
          </div>

          {/* KPI 5: Cancellation Rate */}
          <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs flex flex-col justify-between space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-semibold uppercase text-slate-400">Cancellation Rate</span>
              <div className="w-7 h-7 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center">
                <XCircle className="w-4 h-4" />
              </div>
            </div>
            <div>
              <div className="flex items-baseline space-x-2">
                <div className="text-2xl font-bold font-sans text-slate-900">{metrics.cancellationRate}%</div>
                <span className="inline-flex items-center text-[10px] font-semibold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Within Limits
                </span>
              </div>
              <div className="flex items-center justify-between mt-1 text-[11px]">
                <span className="text-slate-500">Merchant initiated</span>
                <span className="text-slate-400 font-mono font-medium">Target &lt; 1.5%</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* LEVEL 2: TRENDS - "Is it getting better or worse?" (Longitudinal Charts)  */}
      {/* ========================================================================= */}
      <section className="space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-sky-500"></span>
            <h2 className="text-xs font-mono font-bold uppercase text-slate-500 tracking-wider">
              Level 2: Longitudinal Trends
            </h2>
          </div>
          <span className="text-[11px] text-slate-400">Time-series trajectories evaluating directional health</span>
        </div>

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

          {/* Chart 2: Donut Chart - Review Score Distribution */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-900 text-base">Customer Satisfaction Breakdown</h3>
                <p className="text-xs text-slate-500">Share of 1★ to 5★ ratings across historical orders</p>
              </div>
              <span className="text-xs font-mono text-[11px] text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-semibold">
                77% Positive (4-5★)
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
        </div>
      </section>

      {/* Progressive Disclosure Section for Full Analytical View */}
      {viewMode === 'full' && (
        <>
          {/* ========================================================================= */}
          {/* LEVEL 3: SEGMENTS - "Which parts of the business need attention?"        */}
          {/* ========================================================================= */}
          <section className="space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <h2 className="text-xs font-mono font-bold uppercase text-slate-500 tracking-wider">
                  Level 3: Segment &amp; Cohort Breakdown
                </h2>
              </div>
              <span className="text-[11px] text-slate-400">Dimensional analysis highlighting concentrated problem areas</span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Chart 3: Bar Chart - Sellers per Risk Tier */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-slate-900 text-base">Sellers per Risk Tier</h3>
                    <p className="text-xs text-slate-500">Low (&lt;30), Medium (30-70), and High (&gt;70) risk cohorts</p>
                  </div>
                  <span className="text-xs font-mono text-slate-400">3,095 Total Merchants</span>
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

              {/* Chart 4: Horizontal Bar Chart - Top Categories by Risk */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-slate-900 text-base">Top Categories by Risk</h3>
                    <p className="text-xs text-slate-500">
                      Click any bar to drill down directly into that product category
                    </p>
                  </div>
                  <span className="text-xs font-mono text-slate-400">Risk Scale (0-100)</span>
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
          </section>

          {/* ========================================================================= */}
          {/* LEVEL 4: DETAIL - "Show me everything" (Drill-downs, Filters, and Export) */}
          {/* ========================================================================= */}
          <section className="space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                <h2 className="text-xs font-mono font-bold uppercase text-slate-500 tracking-wider">
                  Level 4: Detailed Drill-Down &amp; Audit Tools
                </h2>
              </div>
              <button
                onClick={() => setIsLevel4Expanded(!isLevel4Expanded)}
                className="text-xs font-medium text-slate-600 hover:text-slate-900 flex items-center space-x-1 cursor-pointer"
              >
                <span>{isLevel4Expanded ? 'Collapse Drill-Down Panel' : 'Expand Granular Slices'}</span>
                {isLevel4Expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs space-y-4">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-100 pb-4">
                <div>
                  <h3 className="font-semibold text-slate-900 text-sm">Targeted Root-Cause Drill-Down</h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Navigate straight from macro metrics to filtered seller cohorts across primary risk dimensions.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onNavigateToDirectoryWithFilter?.('Late Delivery')}
                    className="px-2.5 py-1.5 text-xs font-medium rounded-lg bg-orange-50 text-orange-700 border border-orange-200 hover:bg-orange-100 flex items-center space-x-1 transition-colors cursor-pointer"
                  >
                    <Truck className="w-3 h-3" />
                    <span>Filter: Late Deliveries</span>
                  </button>
                  <button
                    onClick={() => onNavigateToDirectoryWithFilter?.('Low Reviews')}
                    className="px-2.5 py-1.5 text-xs font-medium rounded-lg bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100 flex items-center space-x-1 transition-colors cursor-pointer"
                  >
                    <Star className="w-3 h-3" />
                    <span>Filter: Bad Reviews</span>
                  </button>
                  <button
                    onClick={() => onNavigateToDirectoryWithFilter?.('High Cancellations')}
                    className="px-2.5 py-1.5 text-xs font-medium rounded-lg bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 flex items-center space-x-1 transition-colors cursor-pointer"
                  >
                    <AlertTriangle className="w-3 h-3" />
                    <span>Filter: Cancellations</span>
                  </button>
                </div>
              </div>

              {isLevel4Expanded && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1 animate-in fade-in duration-150">
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1.5">
                    <span className="text-[11px] font-mono font-semibold uppercase text-slate-400">Risk Threshold Rule</span>
                    <p className="text-xs text-slate-700">
                      Sellers with risk score &gt; 70 are flagged as High-Risk based on weighted delivery delays (40%), 1-star review frequency (35%), and order cancellations (25%).
                    </p>
                  </div>
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1.5">
                    <span className="text-[11px] font-mono font-semibold uppercase text-slate-400">Regional Outlier Monitoring</span>
                    <p className="text-xs text-slate-700">
                      Delivery delays correlate strongly with non-SP interstate routes. Check state-level postal transit times in the directory drill-down.
                    </p>
                  </div>
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1.5">
                    <span className="text-[11px] font-mono font-semibold uppercase text-slate-400">Data Export &amp; Auditing</span>
                    <p className="text-xs text-slate-700">
                      Export full CSV or JSON cohorts for compliance archiving, operational standup discussions, or custom offline analysis.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </section>
        </>
      )}
    </div>
  );
};
