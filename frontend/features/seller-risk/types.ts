export type RiskTier = 'Low' | 'Medium' | 'High';

export type PrimaryRiskDriver = 'Late Delivery' | 'Low Reviews' | 'High Cancellations' | 'Slow SLA' | 'Price Anomaly';

export interface Seller {
  id: string;
  shortId: string;
  city: string;
  state: string;
  category: string;
  riskScore: number; // 0 - 100
  riskTier: RiskTier;
  primaryRiskDriver: PrimaryRiskDriver;
  totalOrders: number;
  avgReviewScore: number;
  lateDeliveryRate: number; // percentage e.g. 12.4
  cancellationRate: number; // percentage e.g. 3.1
  onTimeDeliveryRate: number; // percentage e.g. 87.6
  lowReviewRate: number; // percentage e.g. 24.5
  sparklineData: number[]; // e.g. 6 data points for recent trend
  isFlagged?: boolean;
  flagReason?: string;
  flaggedAt?: string;
  monthlyPerformance: {
    month: string; // e.g. "Jan", "Feb"
    orderVolume: number;
    lowReviewCount: number;
    reviewScore: number;
    deliveryDelayPct: number;
    cancellationPct: number;
  }[];
  riskFactorContribution: {
    factor: string;
    percentage: number;
    color: string;
  }[];
  delayDistribution: {
    range: string; // e.g., "Early", "On-Time", "1-3 Days Late", "4-7 Days Late", ">7 Days Late"
    count: number;
  }[];
  reviews: {
    id: string;
    orderId: string;
    rating: number;
    date: string;
    comment: string;
    sentiment: 'Positive' | 'Neutral' | 'Negative';
    productCategory: string;
  }[];
}

export interface MarketplaceMetrics {
  totalSellers: number;
  highRiskSellers: number;
  highRiskTrendPct: number; // e.g. -3.2
  avgReviewScore: number;
  lateDeliveryRate: number;
  cancellationRate: number;
  
  monthlyReviewScoreTrend: {
    month: string;
    score: number;
    target: number;
  }[];
  
  riskTierDistribution: {
    tier: RiskTier;
    count: number;
    color: string;
  }[];

  starDistribution: {
    stars: string; // "1★", "2★", etc.
    count: number;
    pct: number;
  }[];

  topCategoriesByRisk: {
    category: string;
    avgRiskScore: number;
    highRiskSellerCount: number;
  }[];

  primaryRiskDriversList: {
    driver: PrimaryRiskDriver;
    percentage: number;
    affectedSellers: number;
    description: string;
  }[];
}

export type DetailTab = 'Overview' | 'Performance' | 'Reviews';
export type PageView = 'Overview' | 'SellerDirectory';
