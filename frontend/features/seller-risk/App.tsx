'use client';

import React, { useState } from 'react';
import { PageView, PrimaryRiskDriver, Seller } from './types';
import { marketplaceMetrics, mockSellers } from './data/mockOlistData';
import { Sidebar } from './components/Sidebar';
import { OverviewPage } from './components/OverviewPage';
import { SellerDirectoryPage } from './components/SellerDirectoryPage';
import { ExportModal } from './components/ExportModal';
import { FlagModal } from './components/FlagModal';

export default function App() {
  const [activePage, setActivePage] = useState<PageView>('Overview');
  const [sellers, setSellers] = useState<Seller[]>(mockSellers);

  // Selected seller in Directory (null by default so panel only opens on selection)
  const [selectedSellerId, setSelectedSellerId] = useState<string | null>(null);

  // Driver & Category filter when navigating from Overview panel
  const [initialDriverFilter, setInitialDriverFilter] = useState<PrimaryRiskDriver | null>(null);
  const [initialCategoryFilter, setInitialCategoryFilter] = useState<string | null>(null);

  // Modal states
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [isFlagModalOpen, setIsFlagModalOpen] = useState(false);
  const [flagTargetSeller, setFlagTargetSeller] = useState<Seller | null>(null);

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
        totalSellersCount={marketplaceMetrics.totalSellers}
      />

      {/* Main View Area */}
      <main className="flex-1 overflow-y-auto min-w-0">
        {activePage === 'Overview' && (
          <OverviewPage
            metrics={{
              ...marketplaceMetrics,
              highRiskSellers: highRiskCount,
            }}
            onNavigateToDirectoryWithFilter={handleNavigateToDirectoryWithFilter}
            onOpenExportModal={() => setIsExportModalOpen(true)}
          />
        )}

        {activePage === 'SellerDirectory' && (
          <SellerDirectoryPage
            sellers={sellers}
            selectedSellerId={selectedSellerId}
            onSelectSeller={(seller) => setSelectedSellerId(seller.id)}
            onCloseInlinePanel={() => setSelectedSellerId(null)}
            onOpenFlagModal={handleOpenFlagModal}
            onOpenExportModal={() => setIsExportModalOpen(true)}
            initialDriverFilter={initialDriverFilter}
            initialCategoryFilter={initialCategoryFilter}
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
