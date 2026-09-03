import React, { useState } from 'react';
import { X, Download, FileSpreadsheet, FileText, CheckCircle, Loader2, Info } from 'lucide-react';
import { Seller } from '../types';
import { exportSellersToCSV, exportSingleSellerCaseToCSV } from '../utils/csvExport';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  defaultFilename?: string;
  sellers?: Seller[];
  selectedSeller?: Seller | null;
}

export const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  title = 'Export Seller Data',
  defaultFilename = 'olist_seller_risk_export',
  sellers = [],
  selectedSeller = null,
}) => {
  const [format, setFormat] = useState<'csv' | 'json'>('csv');
  const [exportScope, setExportScope] = useState<'all' | 'current_seller'>(
    selectedSeller ? 'current_seller' : 'all'
  );
  const [includeReviews, setIncludeReviews] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [downloadedFileName, setDownloadedFileName] = useState('');

  if (!isOpen) return null;

  const handleExport = () => {
    setIsExporting(true);

    setTimeout(() => {
      try {
        const dateStr = new Date().toISOString().split('T')[0];

        if (format === 'csv') {
          if (exportScope === 'current_seller' && selectedSeller) {
            const fname = `case_attachment_seller_${selectedSeller.shortId.replace(/\./g, '')}_${dateStr}`;
            exportSingleSellerCaseToCSV(selectedSeller);
            setDownloadedFileName(`${fname}.csv`);
          } else {
            const fname = `${defaultFilename}_${dateStr}`;
            exportSellersToCSV(sellers, fname, includeReviews);
            setDownloadedFileName(`${fname}.csv`);
          }
        } else if (format === 'json') {
          const exportData = exportScope === 'current_seller' && selectedSeller ? selectedSeller : sellers;
          const jsonStr = JSON.stringify(exportData, null, 2);
          const blob = new Blob([jsonStr], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          const fname = `${defaultFilename}_${dateStr}.json`;
          link.href = url;
          link.download = fname;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
          setDownloadedFileName(fname);
        }
      } catch (err) {
        console.error('Export failed', err);
      } finally {
        setIsExporting(false);
        setIsSuccess(true);
        setTimeout(() => {
          setIsSuccess(false);
          onClose();
        }, 1500);
      }
    }, 400);
  };

  const sellerCount = exportScope === 'current_seller' && selectedSeller ? 1 : sellers.length;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-800 flex items-center justify-center">
              <Download className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-slate-800 text-base">{title}</h3>
              <p className="text-[11px] text-slate-500 font-mono">Ready for Case Attachments & Risk Audit</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5">
          {isSuccess ? (
            <div className="py-8 text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 mx-auto flex items-center justify-center">
                <CheckCircle className="w-6 h-6" />
              </div>
              <h4 className="font-bold text-slate-800 text-lg">Export Downloaded!</h4>
              <p className="text-xs text-slate-600 font-mono bg-slate-50 p-2 rounded border border-slate-200">
                {downloadedFileName}
              </p>
              <p className="text-xs text-slate-500">File has been saved and is ready to attach to your case.</p>
            </div>
          ) : (
            <>
              {/* Scope Selection (if single seller selected) */}
              {selectedSeller && (
                <div>
                  <label className="block text-xs font-mono font-semibold uppercase text-slate-500 mb-2">
                    Export Target Scope
                  </label>
                  <div className="grid grid-cols-2 gap-2.5">
                    <button
                      type="button"
                      onClick={() => setExportScope('current_seller')}
                      className={`p-3 rounded-xl border text-left transition-all ${
                        exportScope === 'current_seller'
                          ? 'border-amber-500 bg-amber-50/50 text-slate-900 font-semibold'
                          : 'border-slate-200 hover:border-slate-300 text-slate-600'
                      }`}
                    >
                      <div className="text-xs font-bold text-slate-900">Current Seller Case</div>
                      <div className="text-[11px] text-slate-500 font-mono truncate">{selectedSeller.shortId}</div>
                    </button>

                    <button
                      type="button"
                      onClick={() => setExportScope('all')}
                      className={`p-3 rounded-xl border text-left transition-all ${
                        exportScope === 'all'
                          ? 'border-amber-500 bg-amber-50/50 text-slate-900 font-semibold'
                          : 'border-slate-200 hover:border-slate-300 text-slate-600'
                      }`}
                    >
                      <div className="text-xs font-bold text-slate-900">All Listed Sellers</div>
                      <div className="text-[11px] text-slate-500 font-mono">{sellers.length} records</div>
                    </button>
                  </div>
                </div>
              )}

              {/* Format Selection */}
              <div>
                <label className="block text-xs font-mono font-semibold uppercase text-slate-500 mb-2">
                  File Format
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setFormat('csv')}
                    className={`p-3 rounded-xl border text-center transition-all flex flex-col items-center space-y-1.5 ${
                      format === 'csv'
                        ? 'border-amber-500 bg-amber-50/50 text-amber-900 font-semibold'
                        : 'border-slate-200 hover:border-slate-300 text-slate-600'
                    }`}
                  >
                    <FileSpreadsheet className="w-5 h-5 text-emerald-600" />
                    <span className="text-xs font-mono font-bold">CSV (.csv)</span>
                    <span className="text-[10px] text-slate-500">Excel / Case Attachment</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setFormat('json')}
                    className={`p-3 rounded-xl border text-center transition-all flex flex-col items-center space-y-1.5 ${
                      format === 'json'
                        ? 'border-amber-500 bg-amber-50/50 text-amber-900 font-semibold'
                        : 'border-slate-200 hover:border-slate-300 text-slate-600'
                    }`}
                  >
                    <FileText className="w-5 h-5 text-blue-600" />
                    <span className="text-xs font-mono font-bold">JSON (.json)</span>
                    <span className="text-[10px] text-slate-500">Raw API Structure</span>
                  </button>
                </div>
              </div>

              {/* Case Attachment Tip */}
              <div className="bg-slate-50 rounded-xl p-3 border border-slate-200 flex items-start space-x-2.5">
                <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                <p className="text-xs text-slate-600 leading-relaxed">
                  Export includes Seller ID, Category, Risk Score, SLA Delivery Breaches, Order Cancellations, and Customer Feedback records ({sellerCount} seller{sellerCount === 1 ? '' : 's'}).
                </p>
              </div>

              {/* Options */}
              <div className="pt-2 border-t border-slate-100 space-y-2">
                <label className="flex items-center space-x-2.5 text-xs text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeReviews}
                    onChange={(e) => setIncludeReviews(e.target.checked)}
                    className="rounded border-slate-300 text-amber-600 focus:ring-amber-500/30"
                  />
                  <span>Include raw review snippets & customer comment logs</span>
                </label>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        {!isSuccess && (
          <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end space-x-3">
            <button
              onClick={onClose}
              disabled={isExporting}
              className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleExport}
              disabled={isExporting}
              className="px-5 py-2 text-xs font-semibold rounded-lg bg-slate-900 text-white hover:bg-slate-800 transition-colors flex items-center space-x-2 shadow-xs cursor-pointer"
            >
              {isExporting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Exporting...</span>
                </>
              ) : (
                <>
                  <Download className="w-3.5 h-3.5" />
                  <span>Download CSV Export</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
