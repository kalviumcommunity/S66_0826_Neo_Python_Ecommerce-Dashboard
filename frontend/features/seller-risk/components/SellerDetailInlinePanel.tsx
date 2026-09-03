import React, { useState } from 'react';
import {
  X,
  ShieldAlert,
  AlertTriangle,
  Star,
  Truck,
  XCircle,
  MapPin,
  Package,
  Filter,
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
} from 'recharts';
import { DetailTab, Seller } from '../types';
import { CircularRiskMeter } from './CircularRiskMeter';
import { exportSingleSellerCaseToCSV, formatCategoryName } from '../utils/csvExport';

interface SellerDetailInlinePanelProps {
  seller: Seller | null;
  isOpen: boolean;
  onClose: () => void;
  onOpenFlagModal: (seller: Seller) => void;
  onOpenExportModal?: () => void;
}

export const SellerDetailInlinePanel: React.FC<SellerDetailInlinePanelProps> = ({
  seller,
  isOpen,
  onClose,
  onOpenFlagModal,
}) => {
  const [activeTab, setActiveTab] = useState<DetailTab>('Overview');
  const [selectedStarFilter, setSelectedStarFilter] = useState<number | 'All'>('All');
  const [exportedToast, setExportedToast] = useState(false);

  if (!isOpen || !seller) return null;

  const isInsufficientData = seller.totalOrders < 10;

  const handleExportCaseCSV = () => {
    exportSingleSellerCaseToCSV(seller);
    setExportedToast(true);
    setTimeout(() => setExportedToast(false), 2000);
  };

  // Filter reviews by star if needed
  const filteredReviews = selectedStarFilter === 'All'
    ? seller.reviews
    : seller.reviews.filter((r) => r.rating === selectedStarFilter);

  // Reviews distribution for donut
  const reviewStarCounts = [5, 4, 3, 2, 1].map((s) => ({
    stars: `${s}★`,
    count: seller.reviews.filter((r) => r.rating === s).length,
  }));

  return (
    <div className="bg-white border-l border-slate-200 shadow-2xl flex flex-col h-full overflow-hidden w-full lg:w-[620px] xl:w-[680px] shrink-0 transition-all duration-300">
      {/* Drawer Header */}
      <div className="p-5 border-b border-slate-100 bg-slate-50/50 space-y-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="font-mono font-bold text-slate-900 text-sm tracking-tight bg-slate-100 px-2.5 py-1 rounded-md border border-slate-200">
                {seller.id}
              </span>
              {seller.isFlagged && (
                <span className="font-mono text-[10px] font-bold uppercase bg-rose-100 text-rose-800 border border-rose-300 px-2 py-0.5 rounded-full flex items-center gap-1">
                  <ShieldAlert className="w-3 h-3 text-rose-600" /> Flagged
                </span>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 pt-0.5">
              <span className="flex items-center space-x-1">
                <MapPin className="w-3.5 h-3.5 text-slate-400" />
                <span>{seller.city}, {seller.state}</span>
              </span>
              <span className="text-slate-300">•</span>
              <span className="flex items-center space-x-1">
                <Package className="w-3.5 h-3.5 text-slate-400" />
                <span className="font-mono font-medium text-slate-700">{seller.totalOrders.toLocaleString()} Orders</span>
              </span>
              <span className="text-slate-300">•</span>
              <span className="font-mono text-slate-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded text-[11px] font-semibold">
                {formatCategoryName(seller.category)}
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors cursor-pointer"
            title="Close detail panel"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Gauge & Primary Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-1">
          <CircularRiskMeter score={seller.riskScore} size={76} strokeWidth={7} />

          <div className="flex items-center space-x-2 shrink-0">
            <button
              onClick={handleExportCaseCSV}
              className="px-3 py-2 rounded-xl text-xs font-semibold border border-slate-200 bg-white hover:bg-slate-50 text-slate-800 flex items-center space-x-1.5 transition-colors shadow-2xs cursor-pointer"
              title="Export this seller's operational data to CSV to attach to a case"
            >
              <Download className="w-3.5 h-3.5 text-emerald-600" />
              <span>{exportedToast ? 'CSV Downloaded!' : 'Export Case CSV'}</span>
            </button>

            <button
              onClick={() => onOpenFlagModal(seller)}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-2xs cursor-pointer ${
                seller.isFlagged
                  ? 'bg-rose-100 text-rose-800 border border-rose-300'
                  : 'bg-rose-600 hover:bg-rose-700 text-white'
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>{seller.isFlagged ? 'Flagged for Review' : 'Flag for Investigation'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Insufficient Data Banner (Edge State for < 10 orders) */}
      {isInsufficientData && (
        <div className="mx-5 mt-4 bg-amber-50 border border-amber-300/80 rounded-xl p-3.5 flex items-start space-x-3">
          <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-900 leading-normal">
            <p className="font-bold">Insufficient Order Data (&lt; 10 Orders)</p>
            <p className="text-[11px] text-amber-800 mt-0.5">
              This seller has processed only <span className="font-mono font-bold">{seller.totalOrders} total orders</span>. Risk score models have lower statistical confidence for sparse volume.
            </p>
          </div>
        </div>
      )}

      {/* Tab Strip */}
      <div className="px-5 border-b border-slate-200 bg-white flex items-center space-x-1 pt-2">
        {(['Overview', 'Performance', 'Reviews'] as DetailTab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all duration-150 ${
              activeTab === tab
                ? 'border-amber-700 text-slate-900 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content Body */}
      <div className="p-5 flex-1 overflow-y-auto space-y-5 bg-[#F7F7F8]/50">
        {/* ================= OVERVIEW TAB ================= */}
        {activeTab === 'Overview' && (
          <div className="space-y-5 animate-in fade-in duration-150">
            {/* 4 Stat Cards */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 shadow-2xs space-y-1">
                <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                  <span>On-Time Delivery</span>
                  <Truck className="w-3.5 h-3.5 text-emerald-600" />
                </div>
                <div className="text-xl font-bold font-sans text-slate-900">{seller.onTimeDeliveryRate}%</div>
                <p className="text-[10px] text-slate-400 font-mono">
                  Late Rate: <span className="text-rose-600 font-semibold">{seller.lateDeliveryRate}%</span>
                </p>
              </div>

              <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 shadow-2xs space-y-1">
                <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                  <span>Cancellation Rate</span>
                  <XCircle className="w-3.5 h-3.5 text-rose-500" />
                </div>
                <div className="text-xl font-bold font-sans text-slate-900">{seller.cancellationRate}%</div>
                <p className="text-[10px] text-slate-400 font-mono">Platform threshold: 2.0%</p>
              </div>

              <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 shadow-2xs space-y-1">
                <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                  <span>Avg Review Score</span>
                  <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
                </div>
                <div className="text-xl font-bold font-sans text-slate-900">{seller.avgReviewScore} <span className="text-xs text-slate-400 font-normal">/ 5.0</span></div>
                <p className="text-[10px] text-slate-400 font-mono">100k scale dataset</p>
              </div>

              <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 shadow-2xs space-y-1">
                <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                  <span>Low Review Rate</span>
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                </div>
                <div className="text-xl font-bold font-sans text-slate-900">{seller.lowReviewRate}%</div>
                <p className="text-[10px] text-slate-400 font-mono">1★ and 2★ rating share</p>
              </div>
            </div>

            {/* 90-Day Overlay Trend Chart */}
            <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-slate-900 text-xs uppercase font-mono tracking-wider">
                    Recent Trend Breakdown
                  </h4>
                  <p className="text-[11px] text-slate-500">Review Score vs. Delivery Delay % & Cancellation %</p>
                </div>
              </div>

              <div className="h-56 w-full pt-1">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={seller.monthlyPerformance} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                    <XAxis dataKey="month" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                    <YAxis yAxisId="left" domain={[1, 5]} tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                    <YAxis yAxisId="right" orientation="right" domain={[0, 40]} tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#ffffff', borderRadius: '8px', borderColor: '#e2e8f0', fontSize: '11px' }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '6px' }} />
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="reviewScore"
                      name="Review Score (1-5)"
                      stroke="#35260E"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="deliveryDelayPct"
                      name="Delay %"
                      stroke="#EF4444"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="cancellationPct"
                      name="Cancel %"
                      stroke="#F59E0B"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Risk Contribution Factors */}
            <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs space-y-3">
              <h4 className="font-bold text-slate-900 text-xs uppercase font-mono tracking-wider">
                Risk Index Contribution Breakdown
              </h4>
              <div className="space-y-2.5">
                {seller.riskFactorContribution.map((factor) => (
                  <div key={factor.factor} className="space-y-1">
                    <div className="flex justify-between text-xs font-medium text-slate-700">
                      <span>{factor.factor}</span>
                      <span className="font-mono font-semibold" style={{ color: factor.color }}>
                        {factor.percentage}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div
                        className="h-2 rounded-full transition-all duration-500"
                        style={{ width: `${factor.percentage}%`, backgroundColor: factor.color }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ================= PERFORMANCE TAB ================= */}
        {activeTab === 'Performance' && (
          <div className="space-y-5 animate-in fade-in duration-150">
            {/* Grouped Bar Chart: Order Volume vs Low Reviews */}
            <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs space-y-3">
              <div>
                <h4 className="font-bold text-slate-900 text-xs uppercase font-mono tracking-wider">
                  Monthly Volume vs. Low Reviews
                </h4>
                <p className="text-[11px] text-slate-500">Total orders processed vs 1★/2★ low review counts</p>
              </div>

              <div className="h-56 w-full pt-1">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={seller.monthlyPerformance} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                    <XAxis dataKey="month" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#ffffff', borderRadius: '8px', borderColor: '#e2e8f0', fontSize: '11px' }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px' }} />
                    <Bar dataKey="orderVolume" name="Total Orders" fill="#35260E" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="lowReviewCount" name="Low Reviews (1-2★)" fill="#EF4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Histogram: Delivery Delay Distribution */}
            <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs space-y-3">
              <div>
                <h4 className="font-bold text-slate-900 text-xs uppercase font-mono tracking-wider">
                  Delivery Delay Histogram
                </h4>
                <p className="text-[11px] text-slate-500">Distribution of order shipments relative to estimated delivery date</p>
              </div>

              <div className="h-48 w-full pt-1">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={seller.delayDistribution} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                    <XAxis dataKey="range" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#ffffff', borderRadius: '8px', borderColor: '#e2e8f0', fontSize: '11px' }}
                      formatter={(val) => [`${val} orders`, 'Volume']}
                    />
                    <Bar dataKey="count" fill="#64748B" radius={[4, 4, 0, 0]} barSize={24} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Comparison Card: Seller vs Category Average */}
            <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs space-y-3">
              <h4 className="font-bold text-slate-900 text-xs uppercase font-mono tracking-wider">
                Benchmark: Seller vs. Category Average ({seller.category})
              </h4>

              <div className="border border-slate-200 rounded-xl overflow-hidden text-xs">
                <table className="w-full text-left">
                  <thead className="bg-slate-50 text-slate-500 font-mono text-[10px] uppercase border-b border-slate-200">
                    <tr>
                      <th className="p-2.5">Metric</th>
                      <th className="p-2.5">This Seller</th>
                      <th className="p-2.5">Category Avg</th>
                      <th className="p-2.5">Variance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-sans">
                    <tr>
                      <td className="p-2.5 font-medium text-slate-800">On-Time Delivery Rate</td>
                      <td className="p-2.5 font-mono font-bold text-slate-900">{seller.onTimeDeliveryRate}%</td>
                      <td className="p-2.5 font-mono text-slate-500">93.2%</td>
                      <td className={`p-2.5 font-mono font-bold ${seller.onTimeDeliveryRate < 93.2 ? 'text-rose-600' : 'text-emerald-600'}`}>
                        {(seller.onTimeDeliveryRate - 93.2).toFixed(1)}%
                      </td>
                    </tr>
                    <tr>
                      <td className="p-2.5 font-medium text-slate-800">Cancellation Rate</td>
                      <td className="p-2.5 font-mono font-bold text-slate-900">{seller.cancellationRate}%</td>
                      <td className="p-2.5 font-mono text-slate-500">1.8%</td>
                      <td className={`p-2.5 font-mono font-bold ${seller.cancellationRate > 1.8 ? 'text-rose-600' : 'text-emerald-600'}`}>
                        +{(seller.cancellationRate - 1.8).toFixed(1)}%
                      </td>
                    </tr>
                    <tr>
                      <td className="p-2.5 font-medium text-slate-800">Average Review Rating</td>
                      <td className="p-2.5 font-mono font-bold text-slate-900">{seller.avgReviewScore}</td>
                      <td className="p-2.5 font-mono text-slate-500">4.12</td>
                      <td className={`p-2.5 font-mono font-bold ${seller.avgReviewScore < 4.12 ? 'text-rose-600' : 'text-emerald-600'}`}>
                        {(seller.avgReviewScore - 4.12).toFixed(2)}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ================= REVIEWS TAB ================= */}
        {activeTab === 'Reviews' && (
          <div className="space-y-5 animate-in fade-in duration-150">
            {/* Donut Chart: Star Rating Distribution */}
            <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="space-y-1">
                <h4 className="font-bold text-slate-900 text-xs uppercase font-mono tracking-wider">
                  Rating Distribution
                </h4>
                <p className="text-xs text-slate-500">
                  Avg Rating: <span className="font-mono font-bold text-amber-800">{seller.avgReviewScore} ★</span>
                </p>
              </div>

              <div className="w-40 h-32 shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={reviewStarCounts}
                      dataKey="count"
                      nameKey="stars"
                      cx="50%"
                      cy="50%"
                      innerRadius={30}
                      outerRadius={45}
                    >
                      {reviewStarCounts.map((_, index) => {
                        const colors = ['#10B981', '#3B82F6', '#F59E0B', '#F97316', '#EF4444'];
                        return <Cell key={`rcell-${index}`} fill={colors[index]} />;
                      })}
                    </Pie>
                    <Tooltip contentStyle={{ fontSize: '11px', borderRadius: '8px' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Filter Pills */}
            <div className="flex items-center space-x-1.5 overflow-x-auto pb-1">
              <span className="text-xs font-mono text-slate-400 mr-1 flex items-center gap-1">
                <Filter className="w-3 h-3" /> Filter:
              </span>
              {(['All', 5, 4, 3, 2, 1] as const).map((star) => (
                <button
                  key={star}
                  onClick={() => setSelectedStarFilter(star)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-mono font-semibold transition-all ${
                    selectedStarFilter === star
                      ? 'bg-slate-900 text-white shadow-2xs'
                      : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  {star === 'All' ? 'All Reviews' : `${star}★`}
                </button>
              ))}
            </div>

            {/* Scrollable List of Review Snippets */}
            <div className="space-y-3">
              {filteredReviews.length === 0 ? (
                <div className="p-8 text-center bg-white rounded-xl border border-slate-200 text-slate-400 text-xs font-mono">
                  No reviews match the selected {selectedStarFilter}★ rating filter.
                </div>
              ) : (
                filteredReviews.map((rev) => (
                  <div key={rev.id} className="p-4 bg-white rounded-xl border border-slate-200/80 shadow-2xs space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div className="flex items-center space-x-0.5 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded text-xs font-mono font-bold text-amber-800">
                          <span>{rev.rating}</span>
                          <Star className="w-3 h-3 fill-amber-500 text-amber-500" />
                        </div>

                        {/* Sentiment Tag Badge */}
                        <span
                          className={`font-mono text-[10px] font-bold px-2 py-0.5 rounded border ${
                            rev.sentiment === 'Positive'
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              : rev.sentiment === 'Negative'
                              ? 'bg-rose-50 text-rose-700 border-rose-200'
                              : 'bg-slate-100 text-slate-600 border-slate-200'
                          }`}
                        >
                          {rev.sentiment}
                        </span>
                      </div>

                      <span className="font-mono text-[11px] text-slate-400">{rev.date}</span>
                    </div>

                    <p className="text-xs text-slate-800 leading-relaxed font-sans">{rev.comment}</p>

                    <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] font-mono text-slate-400">
                      <span>Order ID: {rev.orderId.substring(0, 12)}...</span>
                      <span>{rev.productCategory}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
