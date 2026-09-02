import React, { useState } from 'react';
import { X, ShieldAlert, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react';
import { Seller } from '../types';

interface FlagModalProps {
  seller: Seller | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirmFlag: (sellerId: string, reason: string) => void;
}

export const FlagModal: React.FC<FlagModalProps> = ({
  seller,
  isOpen,
  onClose,
  onConfirmFlag,
}) => {
  const [reason, setReason] = useState('High delivery SLA breaches & customer review rating drops');
  const [priority, setPriority] = useState<'High' | 'Critical' | 'Medium'>('High');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDone, setIsDone] = useState(false);

  if (!isOpen || !seller) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);
      setIsDone(true);
      onConfirmFlag(seller.id, reason);
      setTimeout(() => {
        setIsDone(false);
        onClose();
      }, 1200);
    }, 1000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-rose-50/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-sm">Flag Seller for Investigation</h3>
              <p className="font-mono text-[11px] text-slate-500">{seller.shortId}</p>
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
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {isDone ? (
            <div className="py-6 text-center space-y-2">
              <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 mx-auto flex items-center justify-center">
                <CheckCircle className="w-6 h-6" />
              </div>
              <h4 className="font-bold text-slate-800 text-base">Seller Flagged Successfully</h4>
              <p className="text-xs text-slate-500 font-mono">
                Assigned to Marketplace Risk Audit Team.
              </p>
            </div>
          ) : (
            <>
              <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-3 flex items-start space-x-2.5">
                <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                <p className="text-xs text-amber-900 leading-relaxed">
                  Flagging this seller will place their payouts on temporary 48-hour compliance review and notify the merchant operational desk.
                </p>
              </div>

              <div>
                <label className="block text-xs font-mono font-semibold uppercase text-slate-500 mb-1.5">
                  Investigation Priority
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {(['Medium', 'High', 'Critical'] as const).map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => setPriority(p)}
                      className={`py-2 rounded-lg text-xs font-mono font-semibold border transition-all ${
                        priority === p
                          ? p === 'Critical'
                            ? 'bg-rose-100 text-rose-800 border-rose-300'
                            : 'bg-amber-100 text-amber-900 border-amber-300'
                          : 'bg-slate-50 text-slate-600 border-slate-200'
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono font-semibold uppercase text-slate-500 mb-1.5">
                  Investigation Reason / Notes
                </label>
                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  rows={3}
                  required
                  className="w-full text-xs p-3 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-rose-500/20 text-slate-800 font-sans"
                  placeholder="Describe specific risk indicators..."
                />
              </div>

              <div className="pt-2 border-t border-slate-100 flex items-center justify-end space-x-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 text-xs font-semibold rounded-lg bg-rose-600 text-white hover:bg-rose-700 transition-colors flex items-center space-x-1.5 shadow-xs"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Submitting...</span>
                    </>
                  ) : (
                    <span>Confirm Flag</span>
                  )}
                </button>
              </div>
            </>
          )}
        </form>
      </div>
    </div>
  );
};
