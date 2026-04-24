// ── NUMBER FORMATTERS ──

/** Format as RM currency string e.g. 1234.5 → "1,234.50" */
export const fmtRM = (n) => {
  const v = parseFloat(n) || 0
  return v.toLocaleString('en-MY', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

/** Format weight with 'g' suffix e.g. 10.5 → "10.500 g" */
export const fmtWt = (n) => {
  const v = parseFloat(n) || 0
  return v.toFixed(3) + ' g'
}

/** Format raw weight (no suffix) e.g. 10.5 → "10.500" */
export const fmtWtRaw = (n) => {
  const v = parseFloat(n) || 0
  return v.toFixed(3)
}

/** Format Malaysian mobile number e.g. "0123456789" → "012-345 6789" */
export const fmtMobileStr = (raw) => {
  if (!raw) return ''
  const s = String(raw).replace(/\D/g, '')
  if (s.length >= 10) return s.slice(0, 3) + '-' + s.slice(3, 6) + ' ' + s.slice(6)
  return raw
}

/** Generate deduction note text e.g. "Stones 0.500g · Spring 0.200g" */
export const dedNoteText = (deds) => {
  if (!deds || !deds.length) return ''
  return deds.map(d => `${d.type}${d.type === 'Others' && d.desc ? ' (' + d.desc + ')' : ''} ${parseFloat(d.w || 0).toFixed(3)}g`).join(' · ')
}

/** Parse a formatted value string to float (strips commas) */
export const parseVal = (s) => parseFloat((s || '').replace(/,/g, '')) || 0

/** Format on blur — weight or RM */
export const fmtOnBlur = (val, isWt) => {
  const v = parseFloat((val || '').replace(/,/g, ''))
  if (isNaN(v)) return val
  return isWt ? fmtWtRaw(v) : fmtRM(v)
}
