'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { MarketplaceMetrics, PageView, PrimaryRiskDriver, Seller } from './types';
import { loadDashboard, loadSellerDetail, loadSellerPage, SellerDirectoryFilters } from './data/api';
import { Sidebar } from './components/Sidebar';
import { OverviewPage } from './components/OverviewPage';
import { SellerDirectoryPage } from './components/SellerDirectoryPage';
import { ExportModal } from './components/ExportModal';
import { FlagModal } from './components/FlagModal';

export default function App() {
  const [activePage, setActivePage] = useState<PageView>('Overview');
  const [sellers, setSellers] = useState<Seller[]>([]);
  const [metrics, setMetrics] = useState<MarketplaceMetrics | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [sellerTotal, setSellerTotal] = useState(0);
  const [sellerPage, setSellerPage] = useState(1);
  const [sellerTotalPages, setSellerTotalPages] = useState(1);
  const [isSellerPageLoading, setIsSellerPageLoading] = useState(false);
  const [sellerCategories, setSellerCategories] = useState<string[]>([]);
  const [directoryFilters, setDirectoryFilters] = useState<SellerDirectoryFilters>({});
  const sellerRequestId = useRef(0);

  // Selected seller in Directory (null by default so panel only opens on selection)
  const [selectedSellerId, setSelectedSellerId] = useState<string | null>(null);

  // Driver & Category filter when navigating from Overview panel
  const [initialDriverFilter, setInitialDriverFilter] = useState<PrimaryRiskDriver | null>(null);
  const [initialCategoryFilter, setInitialCategoryFilter] = useState<string | null>(null);

  // Modal states
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [isFlagModalOpen, setIsFlagModalOpen] = useState(false);
  const [flagTargetSeller, setFlagTargetSeller] = useState<Seller | null>(null);

  useEffect(() => {
    let isCurrent = true;

    loadDashboard()
      .then((dashboard) => {
        if (!isCurrent) return;
        setMetrics(dashboard.metrics);
        setSellers(dashboard.sellers);
        setSellerTotal(dashboard.sellerTotal);
        setSellerPage(dashboard.sellerPage);
        setSellerTotalPages(dashboard.sellerTotalPages);
        setSellerCategories(dashboard.sellerFilterOptions.categories);
      })
      .catch((error: unknown) => {
        if (!isCurrent) return;
        setLoadError(error instanceof Error ? error.message : 'Unable to load dashboard data.');
      });

    return () => {
      isCurrent = false;
    };
  }, []);

  // Calculate high risk count dynamically
  const highRiskCount = sellers.filter((s) => s.riskScore >= 70).length;

  const handleNavigateToDirectoryWithFilter = (driver?: PrimaryRiskDriver, category?: string) => {
    setInitialDriverFilter(driver || null);
    setInitialCategoryFilter(category || null);
    setActivePage('SellerDirectory');
  };

  const handleOpenFlagModal = (seller: Seller) => {
    setFlagTargetSeller(seller);
    setIsFlagModalOpen(true);
  };

  const handleSelectSeller = async (seller: Seller) => {
    setSelectedSellerId(seller.id);
    try {
      const detailedSeller = await loadSellerDetail(seller);
      setSellers((current) => current.map((item) => (item.id === seller.id ? detailedSeller : item)));
    } catch (error) {
      console.error('Unable to load seller detail', error);
    }
  };

  const fetchSellerPage = useCallback(async (page: number, filters: SellerDirectoryFilters) => {
    if (page < 1) return;

    const requestId = ++sellerRequestId.current;
    setIsSellerPageLoading(true);
    setSelectedSellerId(null);
    try {
      const result = await loadSellerPage(page, filters);
      if (requestId !== sellerRequestId.current) return;
      setSellers(result.sellers);
      setSellerTotal(result.total);
      setSellerPage(result.page);
      setSellerTotalPages(result.totalPages);
    } catch (error) {
      if (requestId === sellerRequestId.current) {
        console.error('Unable to load seller page', error);
      }
    } finally {
      if (requestId === sellerRequestId.current) {
        setIsSellerPageLoading(false);
      }
    }
  }, []);

  const handleSellerPageChange = useCallback((page: number) => {
    void fetchSellerPage(page, directoryFilters);
  }, [directoryFilters, fetchSellerPage]);

  const handleDirectoryFiltersChange = useCallback((filters: SellerDirectoryFilters) => {
    setDirectoryFilters(filters);
    void fetchSellerPage(1, filters);
  }, [fetchSellerPage]);

  const handleConfirmFlag = (sellerId: string, reason: string) => {
    setSellers((prev) =>
      prev.map((s) =>
        s.id === sellerId
          ? {
              ...s,
              isFlagged: true,
              flagReason: reason,
              flaggedAt: new Date().toISOString().split('T')[0],
            }
          : s
      )
    );
  };

  const activeSelectedSeller = sellers.find((s) => s.id === selectedSellerId) || null;

  if (!metrics) {
    return (
      <main className="grid min-h-screen place-items-center bg-[#F7F7F8] p-6 text-center">
        <div className="max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xs">
          <h1 className="text-lg font-bold text-slate-900">Loading dashboard data…</h1>
          <p className="mt-2 text-sm text-slate-500">
            {loadError ?? 'Connecting to the Seller Trust & Safety API.'}
          </p>
          {loadError && (
            <p className="mt-4 text-xs text-slate-400">
              Set <code>NEXT_PUBLIC_API_URL</code> to your deployed API URL, or start the API locally on port 8000.
            </p>
          )}
        </div>
      </main>
    );
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#F7F7F8] font-sans antialiased text-[#1E293B]">
      {/* Sidebar */}
      <Sidebar
        activePage={activePage}
        onNavigate={(page) => {
          setActivePage(page);
          if (page === 'Overview') {
            setInitialDriverFilter(null);
            setInitialCategoryFilter(null);
          }
        }}
        highRiskCount={highRiskCount}
        totalSellersCount={metrics.totalSellers}
      />

      {/* Main View Area */}
      <main className="flex-1 overflow-y-auto min-w-0">
        {activePage === 'Overview' && (
          <OverviewPage
            metrics={{ ...metrics, highRiskSellers: highRiskCount }}
            onNavigateToDirectoryWithFilter={handleNavigateToDirectoryWithFilter}
            onOpenExportModal={() => setIsExportModalOpen(true)}
          />
        )}

        {activePage === 'SellerDirectory' && (
          <SellerDirectoryPage
            sellers={sellers}
            selectedSellerId={selectedSellerId}
            onSelectSeller={handleSelectSeller}
            onCloseInlinePanel={() => setSelectedSellerId(null)}
            onOpenFlagModal={handleOpenFlagModal}
            onOpenExportModal={() => setIsExportModalOpen(true)}
            initialDriverFilter={initialDriverFilter}
            initialCategoryFilter={initialCategoryFilter}
            totalSellers={sellerTotal}
            currentPage={sellerPage}
            totalPages={sellerTotalPages}
            isPageLoading={isSellerPageLoading}
            onPageChange={handleSellerPageChange}
            categories={sellerCategories}
            onFiltersChange={handleDirectoryFiltersChange}
          />
        )}
      </main>

      {/* Export Modal */}
      <ExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        title="Export Operational Data"
        defaultFilename="olist_seller_risk_export"
        sellers={sellers}
        selectedSeller={activeSelectedSeller}
      />

      {/* Flag Modal */}
      <FlagModal
        seller={flagTargetSeller}
        isOpen={isFlagModalOpen}
        onClose={() => setIsFlagModalOpen(false)}
        onConfirmFlag={handleConfirmFlag}
      />
    </div>
  );
}
