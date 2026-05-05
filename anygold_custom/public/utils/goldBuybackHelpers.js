/**
 * Resolve the ERPNext Item Code for a Gold Buyback line.
 *
 * WS-{purity}-N    → clean item, no deductions
 * WS-{purity}-EBTS → item with impurities / deductions
 *
 * This is the single source of truth for item code logic on the frontend.
 * Call it whenever purity changes or deductions are added/removed.
 */
export function resolveGoldBuybackItemCode(purity, deds) {
  if (!purity) return ''
  const suffix = deds && deds.length > 0 ? 'EBTS' : 'N'
  return `WS-${purity}-${suffix}`
}
