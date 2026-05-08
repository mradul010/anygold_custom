/**
 * Resolve the ERPNext Item Code for a Gold Buyback line.
 *
 * WS-{purity}-WG   → white gold (overrides deduction suffix)
 * WS-{purity}-EBTS → yellow gold with deductions
 * WS-{purity}-N    → yellow gold, clean
 *
 * This is the single source of truth for item code logic on the frontend.
 * Call it whenever purity, deductions, or isWhiteGold changes.
 */
export function resolveGoldBuybackItemCode(purity, deds, isWhiteGold = false) {
  if (!purity) return ''
  if (isWhiteGold) return `WS-${purity}-WG`
  const suffix = deds && deds.length > 0 ? 'EBTS' : 'N'
  return `WS-${purity}-${suffix}`
}
