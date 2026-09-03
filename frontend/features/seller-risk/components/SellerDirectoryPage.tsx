import React, { useState, useMemo } from 'react';
import {
  Search,
  ShieldAlert,
  ArrowUpDown,
  AlertTriangle,
  RotateCcw,
  ChevronRight,
  Tag,
  Download,
  FileSpreadsheet,
} from 'lucide-react';
import { PrimaryRiskDriver, RiskTier, Seller } from '../types';
import { SellerDetailInlinePanel } from './SellerDetailInlinePanel';
import { formatCategoryName, exportSellersToCSV } from '../utils/csvExport';

interface SellerDirectoryPageProps {
  sellers: Seller[];
  selectedSellerId: string | null;
  onSelectSeller: (seller: Seller) => void;
  onCloseInlinePanel: () => void;
  onOpenFlagModal: (seller: Seller) => void;
  onOpenExportModal: () => void;
  initialDriverFilter?: PrimaryRiskDriver | null;
  initialCategoryFilter?: string | null;
}

export const SellerDirectoryPage: React.FC<SellerDirectoryPageProps> = ({
  sellers,
  selectedSellerId,
  onSelectSeller,
  onCloseInlinePanel,
  onOpenFlagModal,
  onOpenExportModal,
  initialDriverFilter = null,
  initialCategoryFilter = null,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>(initialCategoryFilter || 'All');
  const [selectedRiskTier, setSelectedRiskTier] = useState<RiskTier | 'All'>('All');
  const [selectedDriverFilter, setSelectedDriverFilter] = useState<PrimaryRiskDriver | 'All'>(
    initialDriverFilter || 'All'
  );
  const [sortBy, setSortBy] = useState<'risk_desc' | 'risk_asc' | 'orders_desc' | 'rating_asc'>('risk_desc');

  // Unique categories in dataset
  const categories = useMemo(() => {
    return Array.from(new Set(sellers.map((s) => s.category))).filter(Boolean).sort();
  }, [sellers]);

  const activeSeller = useMemo(
    () => sellers.find((s) => s.id === selectedSellerId) || null,
    [sellers, selectedSellerId]
  );

  // Filter & Sort Logic
  const filteredSellers = useMemo(() => {
    return sellers
      .filter((s) => {
        // Search matching
        const query = searchQuery.toLowerCase().trim();
        const matchesSearch =
          !query ||
          s.id.toLowerCase().includes(query) ||
          s.shortId.toLowerCase().includes(query) ||
          s.city.toLowerCase().includes(query) ||
          s.state.toLowerCase().includes(query) ||
          s.category.toLowerCase().includes(query);

        // Category matching
        const matchesCategory =
          selectedCategory === 'All' || s.category.toLowerCase() === selectedCategory.toLowerCase();

        // Risk tier matching
        const matchesRiskTier =
          selectedRiskTier === 'All' || s.riskTier === selectedRiskTier;

        // Risk driver matching
        const matchesDriver =
          selectedDriverFilter === 'All' || s.primaryRiskDriver === selectedDriverFilter;

        return matchesSearch && matchesCategory && matchesRiskTier && matchesDriver;
      })
      .sort((a, b) => {
        if (sortBy === 'risk_desc') return b.riskScore - a.riskScore;
        if (sortBy === 'risk_asc') return a.riskScore - b.riskScore;
        if (sortBy === 'orders_desc') return b.totalOrders - a.totalOrders;
        if (sortBy === 'rating_asc') return a.avgReviewScore - b.avgReviewScore;
        return 0;
      });
  }, [sellers, searchQuery, selectedCategory, selectedRiskTier, selectedDriverFilter, sortBy]);

  const handleResetFilters = () => {
    setSearchQuery('');
    setSelectedCategory('All');
    setSelectedRiskTier('All');
    setSelectedDriverFilter('All');
    setSortBy('risk_desc');
  };

  const handleDirectCSVExport = () => {
    const categorySuffix = selectedCategory !== 'All' ? `_${selectedCategory}` : '';
    const dateStr = new Date().toISOString().split('T')[0];
    const fname = `olist_sellers_case_export${categorySuffix}_${dateStr}`;
    exportSellersToCSV(filteredSellers, fname, true);
  };

  return (
    <div className="flex h-full w-full overflow-hidden bg-[#F7F7F8]">
      {/* Main Directory Area */}
      <div className="flex-1 p-6 space-y-5 overflow-y-auto min-w-0">
        {/* Header Title & Export Actions */}
        <div className="bg-white p-5 rounded-xl border border-[#E2E8F0] shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2.5">
              <h1 className="font-bold text-[#1E293B] text-xl tracking-tight">Seller Directory</h1>
              {selectedCategory !== 'All' && (
                <span className="font-mono text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-200">
                  Category: {formatCategoryName(selectedCategory)}
                </span>
              )}
            </div>
            <p className="text-xs text-[#64748B] mt-0.5">
              Filter by category, investigate merchant risk drivers, or export seller audit data to CSV for case attachments.
            </p>
          </div>

          {/* Export Action Buttons */}
          <div className="flex items-center space-x-2 shrink-0">
            <button
              onClick={handleDirectCSVExport}
              className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-[#35260E] text-white hover:bg-[#251a09] transition-colors flex items-center space-x-1.5 shadow-2xs cursor-pointer"
              title="Quick download filtered seller records to CSV"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export CSV ({filteredSellers.length})</span>
            </button>
            <button
              onClick={onOpenExportModal}
              className="px-3 py-2 text-xs font-semibold rounded-lg border border-[#E2E8F0] bg-[#F8FAFC] text-[#1E293B] hover:bg-[#F1F5F9] transition-colors flex items-center space-x-1.5"
              title="Open full export configuration options"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
              <span>Export Options</span>
            </button>
          </div>
        </div>

        {/* Filter Controls Bar */}
        <div className="bg-white p-4 rounded-xl border border-[#E2E8F0] shadow-2xs space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-[#94A3B8] pointer-events-none" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search Seller ID, City, State..."
                className="w-full pl-8 pr-3 py-2 text-xs rounded-lg border border-[#E2E8F0] bg-[#F8FAFC] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#35260E]/20 text-[#1E293B] font-sans"
              />
            </div>

            {/* Category Manager Filter */}
            <div className="relative">
              <Tag className="w-3.5 h-3.5 absolute left-3 top-3 text-[#94A3B8] pointer-events-none" />
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className={`w-full pl-8 pr-3 py-2 text-xs rounded-lg border border-[#E2E8F0] focus:outline-none focus:ring-2 focus:ring-[#35260E]/20 ${
                  selectedCategory !== 'All'
                    ? 'bg-amber-50/70 border-amber-300 text-amber-900 font-semibold'
                    : 'bg-[#F8FAFC] text-[#1E293B]'
                }`}
              >
                <option value="All">All Categories ({categories.length})</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {formatCategoryName(cat)}
                  </option>
                ))}
              </select>
            </div>

            {/* Risk Tier Filter */}
            <div className="relative">
              <ShieldAlert className="w-3.5 h-3.5 absolute left-3 top-3 text-[#94A3B8] pointer-events-none" />
              <select
                value={selectedRiskTier}
                onChange={(e) => setSelectedRiskTier(e.target.value as RiskTier | 'All')}
                className="w-full pl-8 pr-3 py-2 text-xs rounded-lg border border-[#E2E8F0] bg-[#F8FAFC] text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#35260E]/20"
              >
                <option value="All">All Risk Tiers</option>
                <option value="High">High Risk (&gt;70)</option>
                <option value="Medium">Medium Risk (30–70)</option>
                <option value="Low">Low Risk (&lt;30)</option>
              </select>
            </div>

            {/* Risk Driver Filter */}
            <div className="relative">
              <AlertTriangle className="w-3.5 h-3.5 absolute left-3 top-3 text-[#94A3B8] pointer-events-none" />
              <select
                value={selectedDriverFilter}
                onChange={(e) => setSelectedDriverFilter(e.target.value as PrimaryRiskDriver | 'All')}
                className="w-full pl-8 pr-3 py-2 text-xs rounded-lg border border-[#E2E8F0] bg-[#F8FAFC] text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#35260E]/20"
              >
                <option value="All">All Primary Risk Drivers</option>
                <option value="Late Delivery">Late Delivery</option>
                <option value="Low Reviews">Low Reviews</option>
                <option value="High Cancellations">High Cancellations</option>
                <option value="Slow SLA">Slow SLA</option>
                <option value="Price Anomaly">Price Anomaly</option>
              </select>
            </div>

            {/* Sort Dropdown */}
            <div className="relative">
              <ArrowUpDown className="w-3.5 h-3.5 absolute left-3 top-3 text-[#94A3B8] pointer-events-none" />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                className="w-full pl-8 pr-3 py-2 text-xs rounded-lg border border-[#E2E8F0] bg-[#F8FAFC] text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#35260E]/20"
              >
                <option value="risk_desc">Sort: Highest Risk Score</option>
                <option value="risk_asc">Sort: Lowest Risk Score</option>
                <option value="orders_desc">Sort: Most Total Orders</option>
                <option value="rating_asc">Sort: Lowest Review Rating</option>
              </select>
            </div>
          </div>

          {/* Active Filter Pill Tags */}
          {(searchQuery || selectedCategory !== 'All' || selectedRiskTier !== 'All' || selectedDriverFilter !== 'All') && (
            <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[#E2E8F0] text-xs text-[#64748B]">
              <span className="font-mono text-[11px] text-[#64748B]">Active filters:</span>
              {searchQuery && (
                <span className="font-mono text-[11px] bg-[#F1F5F9] text-[#1E293B] px-2 py-0.5 rounded border border-[#E2E8F0]">
                  Search: &quot;{searchQuery}&quot;
                </span>
              )}
              {selectedCategory !== 'All' && (
                <span className="font-mono text-[11px] bg-amber-100 text-amber-900 px-2 py-0.5 rounded border border-amber-300 font-semibold flex items-center gap-1">
                  <Tag className="w-3 h-3 text-amber-700" />
                  Category: {formatCategoryName(selectedCategory)}
                  <button
                    onClick={() => setSelectedCategory('All')}
                    className="ml-1 text-amber-700 hover:text-amber-900 font-bold"
                  >
                    ×
                  </button>
                </span>
              )}
              {selectedRiskTier !== 'All' && (
                <span className="font-mono text-[11px] bg-[#F1F5F9] text-[#1E293B] px-2 py-0.5 rounded border border-[#E2E8F0]">
                  Risk: {selectedRiskTier}
                </span>
              )}
              {selectedDriverFilter !== 'All' && (
                <span className="font-mono text-[11px] bg-[#F1F5F9] text-[#1E293B] px-2 py-0.5 rounded border border-[#E2E8F0]">
                  Driver: {selectedDriverFilter}
                </span>
              )}
              <button
                onClick={handleResetFilters}
                className="text-[#35260E] font-bold hover:underline flex items-center space-x-1 ml-auto cursor-pointer"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Reset Filters</span>
              </button>
            </div>
          )}
        </div>

        {/* Directory Table or Empty State */}
        {filteredSellers.length === 0 ? (
          <div className="bg-white rounded-xl border border-[#E2E8F0] p-12 text-center space-y-4 shadow-2xs">
            <div className="w-12 h-12 rounded-full bg-[#F8FAFC] text-[#64748B] mx-auto flex items-center justify-center">
              <Search className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <h3 className="font-bold text-[#1E293B] text-base">No Sellers Found</h3>
              <p className="text-xs text-[#64748B] max-w-sm mx-auto">
                No active merchants matched your current category, search string, or operational filter criteria.
              </p>
            </div>
            <button
              onClick={handleResetFilters}
              className="px-4 py-2 text-xs font-bold rounded-lg bg-[#35260E] text-white hover:bg-[#251a09] transition-colors inline-flex items-center space-x-2 cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset All Filters</span>
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-2xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-[#F8FAFC] text-[#64748B] font-mono text-[10px] uppercase border-b border-[#E2E8F0] tracking-wider">
                    <th className="p-3.5 font-bold">Seller ID</th>
                    <th className="p-3.5 font-bold">Category</th>
                    <th className="p-3.5 font-bold">Location</th>
                    <th className="p-3.5 font-bold text-center">Risk Tier</th>
                    <th className="p-3.5 font-bold">Primary Risk Driver</th>
                    <th className="p-3.5 font-bold text-right">Orders</th>
                    <th className="p-3.5 font-bold text-right">Avg Rating</th>
                    <th className="p-3.5 font-bold text-right">Late %</th>
                    <th className="p-3.5 font-bold text-center">Trend</th>
                    <th className="p-3.5"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E2E8F0] text-xs">
                  {filteredSellers.map((seller) => {
                    const isSelected = seller.id === selectedSellerId;

                    // Risk Badge Color matching Professional Polish HTML
                    let badgeClass = 'bg-green-100 text-green-700 font-bold';
                    if (seller.riskScore >= 70) {
                      badgeClass = 'bg-red-100 text-red-700 font-bold';
                    } else if (seller.riskScore >= 30) {
                      badgeClass = 'bg-amber-100 text-amber-700 font-bold';
                    }

                    return (
                      <tr
                        key={seller.id}
                        onClick={() => onSelectSeller(seller)}
                        className={`cursor-pointer transition-colors duration-150 ${
                          isSelected
                            ? 'bg-[#F1F5F9] border-l-4 border-l-[#35260E] font-medium'
                            : 'hover:bg-[#F8FAFC]'
                        }`}
                      >
                        {/* Seller ID */}
                        <td className="p-3.5 font-mono text-[#1E293B] font-bold text-xs whitespace-nowrap">
                          <div className="flex items-center space-x-1.5">
                            <span>{seller.shortId}</span>
                            {seller.isFlagged && (
                              <ShieldAlert className="w-3.5 h-3.5 text-red-600 shrink-0" aria-label="Flagged for investigation" />
                            )}
                          </div>
                        </td>

                        {/* Category */}
                        <td className="p-3.5 whitespace-nowrap">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedCategory(seller.category);
                            }}
                            className="font-mono text-[11px] text-slate-700 bg-slate-100 hover:bg-amber-100 hover:text-amber-900 px-2 py-0.5 rounded border border-slate-200 transition-colors"
                            title={`Filter strictly to ${formatCategoryName(seller.category)}`}
                          >
                            {formatCategoryName(seller.category)}
                          </button>
                        </td>

                        {/* Location */}
                        <td className="p-3.5 text-[#787778] whitespace-nowrap">
                          {seller.city}, <span className="font-mono text-[#64748B]">{seller.state}</span>
                        </td>

                        {/* Risk Tier */}
                        <td className="p-3.5 text-center whitespace-nowrap">
                          <span className={`font-mono text-[10px] uppercase px-2 py-0.5 rounded-full ${badgeClass}`}>
                            {seller.riskTier} ({seller.riskScore})
                          </span>
                        </td>

                        {/* Primary Risk Driver */}
                        <td className="p-3.5 whitespace-nowrap text-[#1E293B] font-medium">
                          {seller.primaryRiskDriver}
                        </td>

                        {/* Orders */}
                        <td className="p-3.5 text-right font-mono text-[#1E293B] whitespace-nowrap font-bold">
                          {seller.totalOrders.toLocaleString()}
                          {seller.totalOrders < 10 && (
                            <span className="text-[10px] text-amber-700 ml-1 font-sans" title="Low order volume (<10)">
                              (Sparse)
                            </span>
                          )}
                        </td>

                        {/* Rating */}
                        <td className="p-3.5 text-right font-mono font-bold whitespace-nowrap">
                          <span className={seller.avgReviewScore < 3.0 ? 'text-red-600' : 'text-[#1E293B]'}>
                            {seller.avgReviewScore} ★
                          </span>
                        </td>

                        {/* Late % */}
                        <td className="p-3.5 text-right font-mono whitespace-nowrap">
                          <span className={seller.lateDeliveryRate > 15 ? 'text-red-600 font-bold' : 'text-[#64748B]'}>
                            {seller.lateDeliveryRate}%
                          </span>
                        </td>

                        {/* Sparkline Trend Visual */}
                        <td className="p-3.5 text-center whitespace-nowrap">
                          <div className="inline-flex items-end space-x-0.5 h-4">
                            {seller.sparklineData.map((val, idx) => (
                              <div
                                key={idx}
                                className={`w-1 rounded-xs ${
                                  seller.riskScore >= 70
                                    ? 'bg-red-400'
                                    : seller.riskScore >= 30
                                    ? 'bg-amber-400'
                                    : 'bg-green-400'
                                }`}
                                style={{ height: `${Math.max(4, (val / 100) * 16)}px` }}
                              />
                            ))}
                          </div>
                        </td>

                        {/* Expand Chevron */}
                        <td className="p-3.5 text-right text-[#64748B]">
                          <ChevronRight className={`w-4 h-4 transition-transform ${isSelected ? 'translate-x-1 text-[#35260E]' : ''}`} />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Inline Seller Detail Drawer/Panel */}
      {activeSeller && (
        <SellerDetailInlinePanel
          seller={activeSeller}
          isOpen={!!activeSeller}
          onClose={onCloseInlinePanel}
          onOpenFlagModal={onOpenFlagModal}
          onOpenExportModal={onOpenExportModal}
        />
      )}
    </div>
  );
};
