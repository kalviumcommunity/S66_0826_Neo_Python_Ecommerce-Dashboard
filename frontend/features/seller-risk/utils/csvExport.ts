import { Seller } from '../types';

/**
 * Formats snake_case or kebab-case category strings to title case
 * e.g. "office_furniture" -> "Office Furniture"
 */
export function formatCategoryName(category: string): string {
  if (!category) return 'Unknown';
  return category
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

/**
 * Escapes a cell value for standard CSV formatting (RFC 4180)
 */
function escapeCSV(value: unknown): string {
  if (value === null || value === undefined) {
    return '""';
  }
  const str = String(value);
  // If string contains comma, quote, or newline, escape quotes and wrap in quotes
  if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return `"${str}"`;
}

/**
 * Triggers a browser download of a CSV file with UTF-8 BOM for Excel compatibility
 */
export function downloadCSV(csvContent: string, filename: string): void {
  // UTF-8 BOM helps Excel open UTF-8 CSVs with special characters properly
  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename.endsWith('.csv') ? filename : `${filename}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Exports a list of sellers to CSV
 */
export function exportSellersToCSV(
  sellers: Seller[],
  filename: string = `olist_sellers_export_${new Date().toISOString().split('T')[0]}`,
  includeReviews: boolean = true
): void {
  const headers = [
    'Seller ID',
    'Short ID',
    'Category',
    'City',
    'State',
    'Risk Tier',
    'Risk Score (0-100)',
    'Primary Risk Driver',
    'Total Orders',
    'Avg Review Score (1-5)',
    'Late Delivery Rate (%)',
    'Cancellation Rate (%)',
    'On-Time Delivery Rate (%)',
    'Low Review Rate (%)',
    'Is Flagged',
    'Flag Reason',
    'Flagged Date',
  ];

  if (includeReviews) {
    headers.push('Sample Customer Reviews');
  }

  const rows = sellers.map((s) => {
    const row = [
      escapeCSV(s.id),
      escapeCSV(s.shortId),
      escapeCSV(formatCategoryName(s.category)),
      escapeCSV(s.city),
      escapeCSV(s.state),
      escapeCSV(s.riskTier),
      escapeCSV(s.riskScore),
      escapeCSV(s.primaryRiskDriver),
      escapeCSV(s.totalOrders),
      escapeCSV(s.avgReviewScore),
      escapeCSV(s.lateDeliveryRate),
      escapeCSV(s.cancellationRate),
      escapeCSV(s.onTimeDeliveryRate),
      escapeCSV(s.lowReviewRate),
      escapeCSV(s.isFlagged ? 'YES' : 'NO'),
      escapeCSV(s.flagReason || ''),
      escapeCSV(s.flaggedAt || ''),
    ];

    if (includeReviews) {
      const reviewSummary = (s.reviews || [])
        .map((r) => `[${r.rating}★ ${r.date}]: "${r.comment.replace(/"/g, "'")}"`)
        .join(' | ');
      row.push(escapeCSV(reviewSummary));
    }

    return row.join(',');
  });

  const csvContent = [headers.join(','), ...rows].join('\r\n');
  downloadCSV(csvContent, filename);
}

/**
 * Exports a single seller case audit file formatted specifically for attaching to a risk case
 */
export function exportSingleSellerCaseToCSV(seller: Seller): void {
  const dateStr = new Date().toISOString().split('T')[0];
  const filename = `case_attachment_seller_${seller.shortId.replace(/\./g, '')}_${dateStr}`;

  const lines: string[] = [];

  // Section 1: Case Summary Header
  lines.push('=== SELLER TRUST & RISK CASE ATTACHMENT REPORT ===');
  lines.push(`Generated Date,${escapeCSV(new Date().toISOString())}`);
  lines.push(`Seller ID,${escapeCSV(seller.id)}`);
  lines.push(`Category,${escapeCSV(formatCategoryName(seller.category))}`);
  lines.push(`Location,${escapeCSV(`${seller.city}, ${seller.state}`)}`);
  lines.push(`Current Risk Tier,${escapeCSV(seller.riskTier)}`);
  lines.push(`Current Risk Score,${escapeCSV(seller.riskScore)} / 100`);
  lines.push(`Primary Risk Driver,${escapeCSV(seller.primaryRiskDriver)}`);
  lines.push(`Compliance Flag Status,${escapeCSV(seller.isFlagged ? 'FLAGGED FOR INVESTIGATION' : 'NORMAL')}`);
  if (seller.isFlagged) {
    lines.push(`Flag Reason,${escapeCSV(seller.flagReason || 'N/A')}`);
    lines.push(`Flagged Date,${escapeCSV(seller.flaggedAt || 'N/A')}`);
  }
  lines.push('');

  // Section 2: Key Operational Metrics
  lines.push('=== KEY OPERATIONAL METRICS ===');
  lines.push('Metric,Value,Benchmark Target,Status');
  lines.push(`Total Processed Orders,${escapeCSV(seller.totalOrders)},N/A,${seller.totalOrders < 10 ? 'Low Volume Warning' : 'Adequate Volume'}`);
  lines.push(`Average Review Rating,${escapeCSV(seller.avgReviewScore)},>= 4.0,${seller.avgReviewScore < 3.5 ? 'Critical' : 'Normal'}`);
  lines.push(`Late Delivery Rate (%),${escapeCSV(seller.lateDeliveryRate)}%,< 10.0%,${seller.lateDeliveryRate > 15 ? 'Critical Breach' : 'Normal'}`);
  lines.push(`Order Cancellation Rate (%),${escapeCSV(seller.cancellationRate)}%,< 2.0%,${seller.cancellationRate > 5 ? 'High Cancellation' : 'Normal'}`);
  lines.push(`On-Time Delivery Rate (%),${escapeCSV(seller.onTimeDeliveryRate)}%,>= 90.0%,${seller.onTimeDeliveryRate < 85 ? 'Below Target' : 'Compliant'}`);
  lines.push(`Low Review Rate (1-2★ %),${escapeCSV(seller.lowReviewRate)}%,< 15.0%,${seller.lowReviewRate > 25 ? 'Elevated Negative Sentiment' : 'Normal'}`);
  lines.push('');

  // Section 3: Monthly Breakdown
  if (seller.monthlyPerformance && seller.monthlyPerformance.length > 0) {
    lines.push('=== MONTHLY PERFORMANCE TREND ===');
    lines.push('Month,Order Volume,Review Score,Low Review Count (1-2★),Delivery Delay %,Cancellation %');
    seller.monthlyPerformance.forEach((m) => {
      lines.push(`${escapeCSV(m.month)},${escapeCSV(m.orderVolume)},${escapeCSV(m.reviewScore)},${escapeCSV(m.lowReviewCount)},${escapeCSV(m.deliveryDelayPct)}%,${escapeCSV(m.cancellationPct)}%`);
    });
    lines.push('');
  }

  // Section 4: Delay Distribution
  if (seller.delayDistribution && seller.delayDistribution.length > 0) {
    lines.push('=== SHIPPING DELAY DISTRIBUTION ===');
    lines.push('Delay Window,Order Count');
    seller.delayDistribution.forEach((d) => {
      lines.push(`${escapeCSV(d.range)},${escapeCSV(d.count)}`);
    });
    lines.push('');
  }

  // Section 5: Risk Factor Contribution
  if (seller.riskFactorContribution && seller.riskFactorContribution.length > 0) {
    lines.push('=== RISK INDEX CONTRIBUTION ===');
    lines.push('Risk Factor,Weight Contribution (%)');
    seller.riskFactorContribution.forEach((f) => {
      lines.push(`${escapeCSV(f.factor)},${escapeCSV(f.percentage)}%`);
    });
    lines.push('');
  }

  // Section 6: Customer Reviews Log
  if (seller.reviews && seller.reviews.length > 0) {
    lines.push('=== CUSTOMER REVIEWS & FEEDBACK LOG ===');
    lines.push('Review ID,Order ID,Date,Rating (Stars),Sentiment,Product Category,Customer Comment');
    seller.reviews.forEach((r) => {
      lines.push(
        [
          escapeCSV(r.id),
          escapeCSV(r.orderId),
          escapeCSV(r.date),
          escapeCSV(r.rating),
          escapeCSV(r.sentiment),
          escapeCSV(r.productCategory),
          escapeCSV(r.comment),
        ].join(',')
      );
    });
  }

  const csvContent = lines.join('\r\n');
  downloadCSV(csvContent, filename);
}
