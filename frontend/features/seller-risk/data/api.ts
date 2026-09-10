import { MarketplaceMetrics, PrimaryRiskDriver, RiskTier, Seller } from '../types';

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000').replace(/\/$/, '');

type ApiSeller = {
  seller_id: string;
  category: string;
  location: { city: string; state: string };
  risk_score: number;
  risk_tier: 'LOW' | 'MEDIUM' | 'HIGH';
  primary_risk_driver: string;
  total_orders: number;
  average_rating: number;
  late_delivery_percentage: number;
  cancellation_rate: number;
  low_review_rate: number;
  risk_history: { period: string; risk_score: number }[];
};

type ApiSellerDetail = {
  seller_id: string;
  metrics: {
    cancellation_rate: number;
    average_rating: number;
    late_delivery_percentage: number;
  };
  risk_contributors: {
    delivery_delay_penalty: number;
    review_score_penalty: number;
    cancellation_penalty: number;
  };
  monthly_history: {
    period: string;
    orders: number;
    delivered_orders: number;
    avg_review: number;
    late_deliveries: number;
    canceled_orders: number;
    cancellation_rate: number;
    low_review_count: number;
  }[];
  reviews: {
    review_id: string;
    order_id: string;
    review_score: number;
    review_creation_date: string | null;
    review_comment_message: string | null;
    product_category: string;
  }[];
  delivery_delay_distribution: { range: string; count: number }[];
};

type ApiOverview = {
  total_sellers: number;
  high_risk_sellers: number;
  high_risk_change_percent: number;
  average_review_score: number;
  late_delivery_percentage: number;
  cancellation_rate: number;
};

const riskTierMap: Record<ApiSeller['risk_tier'], RiskTier> = {
  LOW: 'Low',
  MEDIUM: 'Medium',
  HIGH: 'High',
};

const driverMap: Record<string, PrimaryRiskDriver> = {
  'Delivery Delays': 'Late Delivery',
  'Negative Reviews': 'Low Reviews',
  Cancellations: 'High Cancellations',
};

async function fetchApi<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`API request failed (${response.status}) for ${path}`);
  }
  return response.json() as Promise<T>;
}

function toSeller(seller: ApiSeller): Seller {
  const riskTier = riskTierMap[seller.risk_tier];
  const driver = driverMap[seller.primary_risk_driver] ?? 'Late Delivery';

  return {
    id: seller.seller_id,
    shortId: `${seller.seller_id.slice(0, 8)}...${seller.seller_id.slice(-3)}`,
    city: seller.location.city,
    state: seller.location.state,
    category: seller.category,
    riskScore: seller.risk_score,
    riskTier,
    primaryRiskDriver: driver,
    totalOrders: seller.total_orders,
    avgReviewScore: seller.average_rating,
    lateDeliveryRate: seller.late_delivery_percentage,
    cancellationRate: seller.cancellation_rate,
    onTimeDeliveryRate: Math.max(0, Number((100 - seller.late_delivery_percentage).toFixed(2))),
    lowReviewRate: seller.low_review_rate,
    sparklineData: seller.risk_history.map((point) => point.risk_score),
    monthlyPerformance: [],
    riskFactorContribution: [],
    delayDistribution: [],
    reviews: [],
  };
}

function applySellerDetail(seller: Seller, detail: ApiSellerDetail): Seller {
  return {
    ...seller,
    avgReviewScore: detail.metrics.average_rating,
    lateDeliveryRate: detail.metrics.late_delivery_percentage,
    cancellationRate: detail.metrics.cancellation_rate,
    onTimeDeliveryRate: Math.max(0, Number((100 - detail.metrics.late_delivery_percentage).toFixed(2))),
    monthlyPerformance: detail.monthly_history.map((point) => ({
      month: point.period,
      orderVolume: point.orders,
      deliveriesDone: point.delivered_orders,
      lowReviewCount: point.low_review_count,
      reviewScore: point.avg_review,
      lateDeliveryCount: point.late_deliveries,
      cancelledOrderCount: point.canceled_orders,
    })),
    riskFactorContribution: [
      { factor: 'Late Delivery Rate', percentage: detail.metrics.late_delivery_percentage, color: '#EF4444' },
      { factor: 'Low Rating Rate', percentage: seller.lowReviewRate, color: '#F97316' },
      { factor: 'Cancellation Rate', percentage: detail.metrics.cancellation_rate, color: '#F59E0B' },
    ],
    delayDistribution: detail.delivery_delay_distribution,
    reviews: detail.reviews.map((review) => ({
      id: review.review_id,
      orderId: review.order_id,
      rating: review.review_score,
      date: review.review_creation_date?.slice(0, 10) ?? 'Unknown date',
      comment: review.review_comment_message || 'No written review was provided.',
      sentiment: review.review_score >= 4 ? 'Positive' : review.review_score <= 2 ? 'Negative' : 'Neutral',
      productCategory: review.product_category,
    })),
  };
}

export async function loadDashboard(): Promise<{
  metrics: MarketplaceMetrics;
  sellers: Seller[];
  sellerTotal: number;
  sellerPage: number;
  sellerTotalPages: number;
}> {
  const firstPage = await loadSellerPage(1);
  const sellers = firstPage.sellers;

  const [overview, trend, distribution, reviews, categories] = await Promise.all([
    fetchApi<ApiOverview>('/api/analytics/overview'),
    fetchApi<{ target_score: number; trend: { period: string; average_review_score: number }[] }>('/api/analytics/review-trend'),
    fetchApi<{ low: number; medium: number; high: number }>('/api/analytics/risk-distribution'),
    fetchApi<{ distribution: Record<'1_star' | '2_star' | '3_star' | '4_star' | '5_star', number> }>('/api/analytics/review-distribution'),
    fetchApi<{ categories: { category: string; risk_score: number; total_sellers: number; high_risk_seller_count: number }[] }>('/api/analytics/category-risk'),
  ]);

  const reviewTotal = Object.values(reviews.distribution).reduce((total, count) => total + count, 0);
  return {
    sellers,
    sellerTotal: firstPage.total,
    sellerPage: firstPage.page,
    sellerTotalPages: firstPage.totalPages,
    metrics: {
      totalSellers: overview.total_sellers,
      highRiskSellers: overview.high_risk_sellers,
      highRiskTrendPct: overview.high_risk_change_percent,
      avgReviewScore: overview.average_review_score,
      lateDeliveryRate: overview.late_delivery_percentage,
      cancellationRate: overview.cancellation_rate,
      monthlyReviewScoreTrend: trend.trend.map((point) => ({ month: point.period, score: point.average_review_score, target: trend.target_score })),
      riskTierDistribution: [
        { tier: 'Low', count: distribution.low, color: '#10B981' },
        { tier: 'Medium', count: distribution.medium, color: '#F59E0B' },
        { tier: 'High', count: distribution.high, color: '#EF4444' },
      ],
      starDistribution: ([5, 4, 3, 2, 1] as const).map((stars) => {
        const count = reviews.distribution[`${stars}_star`];
        return { stars: `${stars}★`, count, pct: Number(((count / Math.max(reviewTotal, 1)) * 100).toFixed(1)) };
      }),
      topCategoriesByRisk: categories.categories.slice(0, 8).map((category) => ({
        category: category.category,
        avgRiskScore: category.risk_score,
        totalSellerCount: category.total_sellers,
        highRiskSellerCount: category.high_risk_seller_count,
      })),
      primaryRiskDriversList: [],
    },
  };
}

export async function loadSellerPage(page: number): Promise<{
  sellers: Seller[];
  total: number;
  page: number;
  totalPages: number;
}> {
  const result = await fetchApi<{
    total: number;
    page: number;
    total_pages: number;
    sellers: ApiSeller[];
  }>(`/api/sellers?page=${page}&limit=10`);

  return {
    sellers: result.sellers.map(toSeller),
    total: result.total,
    page: result.page,
    totalPages: result.total_pages,
  };
}

export async function loadSellerDetail(seller: Seller): Promise<Seller> {
  const detail = await fetchApi<ApiSellerDetail>(`/api/sellers/${encodeURIComponent(seller.id)}`);
  return applySellerDetail(seller, detail);
}
