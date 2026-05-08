import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { PURITY_XAU, PM_LABELS, BAG_OPTIONS, MOCK_CASH_BALANCE } from '../constants/index.js'
import { MOCK_CUSTOMERS, MOCK_LOCKS } from '../constants/mockData.js'
import { fmtRM, fmtWt, fmtWtRaw, dedNoteText, parseVal } from '../utils/formatters.js'
import { resolveGoldBuybackItemCode } from '../utils/goldBuybackHelpers.js'

// ── ITEM FACTORY ──
// gross_weight: physical scale weight — stored for bag stock tally reconciliation
// net_weight:   gross - deductions — SOURCE OF TRUTH for amount, XAU, GL, stock entries
const mkItem = (id, prefill = false) => ({
  id,
  desc: '',
  purity: prefill ? '916' : '',
  is_white_gold: false,
  item_code: prefill ? resolveGoldBuybackItemCode('916', [], false) : '',
  gross: 0,
  deds: [],       // [{ type, w, desc }]
  net: 0,
  rate: 0,
  amount: 0,
  lockId: null,   // references BLOK-DDMMYY-XXX document
  overageAck: false,
  bag: null,      // null = use document default bag
  warehouse: null // null = resolved by submit.py from bag/default
})

const getDocDateKey = () => {
  const d = new Date()
  const dd = String(d.getDate()).padStart(2, '0')
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const yy = String(d.getFullYear()).slice(-2)
  return `${dd}${mm}${yy}`
}

const buildDocNo = (seq) => `PUR-${getDocDateKey()}-${String(seq).padStart(3, '0')}`

export function useGoldBuyback() {
  // ── VIEW STATE ──
  const view = ref('draft') // 'draft' | 'review' | 'submitted'
  const status = ref('draft')
  const docSeq = ref(1)
  const docNo = ref(buildDocNo(docSeq.value))

  // ── FORM META ──
  const niH = ref(false)        // Not In Hand toggle
  const editTime = ref(false)
  const time = ref('')

  // ── CUSTOMER ──
  const cust = ref(null)
  const search = ref('')
  const showDD = ref(false)

  // ── PAYMENT ──
  const company = ref((frappe?.defaults?.get_default?.('company')) || frappe?.boot?.defaults?.company || 'Anygold Sdn. Bhd.')
  const pm = ref('')
  const bankAccounts = ref([]) // [{ value: account_name, label: "Maybank ..."}]
  const bankAccount = ref('')
  const paymentAccounts = ref({
    inventory: 'Wholesale Inventory',
    cash: 'Cash Account',
    custacct: 'Customer Account (AP/AR)'
  })
  const loadingPaymentAccounts = ref(false)
  let nextMixId = 3
  const mixRows = ref([
    { id: 1, mode: 'Cash', amount: '', bank_account: '' },
    { id: 2, mode: 'Bank Transfer', amount: '', bank_account: '' }
  ])

  // ── ITEMS ──
  let nextId = 2
  const lastAddedId = ref(null)
  const items = ref([mkItem(1, true)])

  // ── BAG ──
  const defBag = ref('WS-Main Bag')
  const bagOptions = ref([])    // warehouse doc names under "Wholesale Bags - AGSB"
  const purityOptions = ref([]) // [{purity_code, xau_coefficient}] from Purity Master

  // ── TOTALS ──
  const round = ref(false)
  const disc = ref('')
  const discDisp = ref('')

  // ── LOCKS ──
  const locks = ref([])
  const lockOpen = ref(false)
  const lockPop = ref(null)
  const bagPop = ref(null)

  // ── MODALS ──
  const dedModal = ref(null)
  const showNewCust = ref(false)
  const ovgModal = ref(false)

  // ── GL ──
  const glOpen = ref(false)

  // ── UI ──
  const validationErrors = ref([])
  const isMobile = ref(false)
  const mSec = ref({
    doc: false, cust: true, items: false,
    pay: false, tots: false, summ: false, gl: false
  })

  // ── TIMER ──
  let timerInterval = null
  const startTimer = () => {
    clearInterval(timerInterval)
    timerInterval = setInterval(() => {
      time.value = new Date().toTimeString().slice(0, 8)
    }, 1000)
    time.value = new Date().toTimeString().slice(0, 8)
  }

  watch(editTime, (val) => {
    if (val) startTimer()
    else clearInterval(timerInterval)
  })

  watch(company, () => {
    fetchCompanyPaymentSetup()
  })

  watch(bankAccount, () => {
    ensureDefaultBankInMixRows()
  })

  // ── MOBILE DETECTION ──
  const handleResize = () => { isMobile.value = window.innerWidth <= 768 }

  // ── OUTSIDE CLICK — close popovers/dropdowns ──
  const handleOutsideClick = (e) => {
    if (lockPop.value && !e.target.closest('.lock-popover') && !e.target.closest('.lock-icon-btn')) {
      lockPop.value = null
    }
    if (bagPop.value && !e.target.closest('.bag-mini-dd') && !e.target.closest('.bag-row-btn') && !e.target.closest('.m-bg-btn')) {
      bagPop.value = null
    }
    if (showDD.value && !e.target.closest('.search-wrapper')) {
      showDD.value = false
    }
  }

  const handleKeydown = (e) => {
    if (e.key === 'Escape') {
      lockPop.value = null
      bagPop.value = null
      showDD.value = false
      dedModal.value = null
    }
  }

  onMounted(() => {
    time.value = new Date().toTimeString().slice(0, 8)
    isMobile.value = window.innerWidth <= 768
    fetchCompanyPaymentSetup()
    fetchBagOptions()
    fetchPurityOptions()
    window.addEventListener('resize', handleResize)
    document.addEventListener('mousedown', handleOutsideClick)
    document.addEventListener('keydown', handleKeydown)
  })

  onUnmounted(() => {
    clearInterval(timerInterval)
    window.removeEventListener('resize', handleResize)
    document.removeEventListener('mousedown', handleOutsideClick)
    document.removeEventListener('keydown', handleKeydown)
  })

  const getBankAccountLabel = (accountName) => {
    if (!accountName) return 'Bank Account'
    const found = bankAccounts.value.find(b => b.value === accountName)
    return found?.label || accountName
  }

  const getModeAccountLabel = (mode, rowBankAccount = '') => {
    if (mode === 'Cash' || mode === 'cash') return paymentAccounts.value.cash || 'Cash Account'
    if (mode === 'Customer Account' || mode === 'custacct') return paymentAccounts.value.custacct || 'Customer Account (AP/AR)'
    if (mode === 'Bank Transfer' || mode === 'bank') {
      return getBankAccountLabel(rowBankAccount || bankAccount.value)
    }
    return mode || 'Account'
  }

  const ensureDefaultBankInMixRows = () => {
    const fallback = bankAccount.value || bankAccounts.value[0]?.value || ''
    if (!fallback) return
    mixRows.value = mixRows.value.map(r => {
      if (r.mode !== 'Bank Transfer') return r
      if (r.bank_account) return r
      return { ...r, bank_account: fallback }
    })
  }

  const fetchBagOptions = async () => {
    if (bagOptions.value.length) return
    try {
      const res = await frappe.call({
        method: 'frappe.client.get_list',
        args: {
          doctype: 'Warehouse',
          fields: ['name'],
          filters: { is_group: 0, parent_warehouse: 'Wholesale Bags - AGSB' },
          limit_page_length: 100
        }
      })
      bagOptions.value = (res.message || []).map(w => w.name)
      if (bagOptions.value.length) {
        const mainBag = bagOptions.value.find(b => b.toLowerCase().includes('main bag'))
        defBag.value = mainBag || bagOptions.value[0]
      }
    } catch (e) {
      console.warn('Failed to fetch bag options', e)
    }
  }

  const fetchPurityOptions = async () => {
    if (purityOptions.value.length) return
    try {
      const res = await frappe.call({
        method: 'anygold_custom.api.GoldBuyBack.items.get_purity_master'
      })
      purityOptions.value = res.message || []
    } catch (e) {
      console.warn('Failed to fetch purity options, using defaults', e)
    }
  }

  const refreshPurityList = async () => {
    try {
      const res = await frappe.call({
        method: 'anygold_custom.api.GoldBuyBack.items.get_purity_master'
      })
      purityOptions.value = res.message || []
    } catch (e) {
      console.warn('Failed to refresh purity options', e)
    }
  }

  const fetchCompanyPaymentSetup = async () => {
    loadingPaymentAccounts.value = true
    try {
      const r = await frappe.call({
        method: 'anygold_custom.api.GoldBuyBack.submit.get_company_payment_accounts',
        args: { company: company.value }
      })
      const data = r.message || {}

      paymentAccounts.value = {
        inventory: data.inventory_account || paymentAccounts.value.inventory,
        cash: data.cash_account || paymentAccounts.value.cash,
        custacct: data.customer_account || paymentAccounts.value.custacct
      }

      bankAccounts.value = (data.bank_accounts || []).map(acc => ({
        value: acc.value || acc.name,
        label: acc.label || acc.name || acc.value
      }))

      const preferred = data.default_bank_account || bankAccounts.value[0]?.value || ''
      if (!bankAccount.value || !bankAccounts.value.find(b => b.value === bankAccount.value)) {
        bankAccount.value = preferred
      }
      ensureDefaultBankInMixRows()
    } catch (e) {
      console.warn('Failed to fetch company payment setup', e)
    } finally {
      loadingPaymentAccounts.value = false
    }
  }

  // ════════════════════════════════════════
  // COMPUTED VALUES
  // ════════════════════════════════════════

  const totGross = computed(() => items.value.reduce((s, i) => s + (i.gross || 0), 0))
  const totNet   = computed(() => items.value.reduce((s, i) => s + (i.net || i.gross || 0), 0))
  const totAmt   = computed(() => items.value.reduce((s, i) => s + (i.amount || 0), 0))
  const discV    = computed(() => parseVal(disc.value))

  const gt = computed(() => {
    const raw = totAmt.value - discV.value
    return round.value ? Math.round(raw) : parseFloat(raw.toFixed(2))
  })

  const rawDiff   = computed(() => totAmt.value - discV.value)
  const roundHint = computed(() => {
    if (!round.value) return ''
    const diff = Math.round(rawDiff.value) - rawDiff.value
    return diff >= 0 ? `(+RM ${Math.abs(diff).toFixed(2)})` : `(-RM ${Math.abs(diff).toFixed(2)})`
  })

  // XAU CALCULATION
  // xau_per_item = net_weight × purity_factor (916 → 0.916, 9999 → 0.9999 etc.)
  // xau_avco = grand_total / total_xau  [RM per pure gram]
  const totXAU = computed(() =>
    items.value.reduce((s, i) => s + (i.net || i.gross || 0) * (PURITY_XAU[i.purity] || 0), 0)
  )

  const mixTot = computed(() =>
    mixRows.value.reduce((s, r) => s + (parseVal(r.amount)), 0)
  )
  const mixDiff = computed(() => mixTot.value - gt.value)

  const filtCust = computed(() => {
    if (!search.value) return MOCK_CUSTOMERS
    const q = search.value.toUpperCase()
    return MOCK_CUSTOMERS.filter(c => c.name.includes(q) || c.ic.includes(q))
  })

  // Customer Account amount for live balance projection
  // custacct standalone → full GT. Mix with Customer Account row → sum of those rows.
  // ⚠️ MRADUL: replace cust.advance with frappe.call get_party_balance result
  const custAcctAmt = computed(() => {
    if (pm.value === 'custacct') return gt.value
    if (pm.value === 'mix') {
      return mixRows.value
        .filter(r => r.mode === 'Customer Account')
        .reduce((s, r) => s + parseVal(r.amount), 0)
    }
    return 0
  })

  // Projected customer balance after this transaction
  const projectedBalance = computed(() => (cust.value?.advance || 0) - custAcctAmt.value)

  // ── GL ROWS (posts on Submit only) ──
  // DR: Wholesale Inventory = Grand Total (always)
  // CR: depends on payment method
  const glRows = computed(() => {
    if (gt.value <= 0) return []
    const debit = { acct: paymentAccounts.value.inventory || 'Wholesale Inventory', dr: fmtRM(gt.value), cr: '—' }
    if (pm.value === 'mix') {
      const credits = mixRows.value
        .filter(r => parseVal(r.amount) > 0)
        .map(r => ({
          acct: getModeAccountLabel(r.mode, r.bank_account),
          dr: '—',
          cr: fmtRM(parseVal(r.amount))
        }))
      return [debit, ...credits]
    }
    return pm.value
      ? [debit, { acct: getModeAccountLabel(pm.value === 'bank' ? 'Bank Transfer' : pm.value), dr: '—', cr: fmtRM(gt.value) }]
      : [debit]
  })

  // STOCK ENTRIES (posts on Submit only)
  // Stores both gross_weight AND net_weight per item per purity per warehouse.
  // gross_weight → physical bag stock tally (staff weighs purity groups on scale)
  // net_weight   → accounting, XAU, AVCO
  const stRows = computed(() =>
    items.value
      .filter(i => (i.net || i.gross || 0) > 0)
      .map(i => ({
        item: i.item_code || (i.purity ? `WS-${i.purity}-?` : '—'),
        wh:   i.warehouse || i.bag || defBag.value,
        xau:  ((i.net || i.gross || 0) * (PURITY_XAU[i.purity] || 0)).toFixed(3),
        nw:   fmtWt(i.net || i.gross || 0),
        gw:   fmtWt(i.gross || 0)
      }))
  )

  const summPay = computed(() => {
    if (pm.value !== 'mix') {
      return gt.value > 0 && pm.value
        ? [{ label: getModeAccountLabel(pm.value === 'bank' ? 'Bank Transfer' : pm.value), val: fmtRM(gt.value) }]
        : []
    }
    return mixRows.value
      .filter(r => parseVal(r.amount) > 0)
      .map(r => ({ label: getModeAccountLabel(r.mode, r.bank_account), val: fmtRM(parseVal(r.amount)) }))
  })

  const bagSummary = computed(() => {
    const overrides = items.value.filter(i => i.bag && i.bag !== defBag.value)
    if (!overrides.length) return [{ label: defBag.value, note: 'default' }]
    const lines = [{ label: defBag.value, note: 'default' }]
    const groups = {}
    overrides.forEach(i => {
      if (!groups[i.bag]) groups[i.bag] = []
      groups[i.bag].push(`${i.desc || 'Item'} ${i.purity} · ${(i.net || i.gross || 0).toFixed(3)}g`)
    })
    Object.entries(groups).forEach(([bag, list]) => lines.push({ label: bag, note: list.join(', ') }))
    return lines
  })

  const itemSummary = computed(() => {
    const n  = items.value.filter(i => i.gross > 0).length
    const tw = items.value.reduce((s, i) => s + (i.net || i.gross || 0), 0)
    if (!n) return null
    return `${n} item${n > 1 ? 's' : ''} · ${tw.toFixed(3)}g · RM ${fmtRM(gt.value)}`
  })

  // Rate lock remaining weight (excludes current item to avoid self-deduction)
  const getLockRem = (lockId, excludeId = null) => {
    const lk = locks.value.find(l => l.id === lockId)
    if (!lk) return 0
    const used = items.value.reduce((s, i) =>
      i.id !== excludeId && i.lockId === lockId ? s + (i.net || i.gross || 0) : s, 0
    )
    return lk.originalWt - used
  }

  const unresolved = computed(() =>
    items.value.filter(item => {
      if (!item.lockId || item.overageAck) return false
      const net = item.net || item.gross || 0
      if (net <= 0) return false
      return (net - getLockRem(item.lockId, item.id)) > 0.0005
    })
  )

  const custIsDealer = computed(() => cust.value?.type === 'Dealer')
  const showBag = computed(() => !niH.value)

  // ════════════════════════════════════════
  // SECTION TOGGLE (mobile)
  // ════════════════════════════════════════
  const togSec = (k) => { mSec.value[k] = !mSec.value[k] }

  // ════════════════════════════════════════
  // CUSTOMER METHODS
  // ════════════════════════════════════════

  // CUSTOMER / SUPPLIER PARTY LINK
  // Each gold contact is BOTH Customer + Supplier in ERPNext (linked via custom field).
  // Purchase uses Supplier party (AP ledger). UI shows "Customer" for staff familiarity.
  // ⚠️ MRADUL: on pickCust, call frappe.call get_party_balance to get live AR/AP
  const pickCust = (c) => {
    validationErrors.value = []
    cust.value = c
    search.value = ''
    showDD.value = false
    locks.value = (MOCK_LOCKS[c.name] || []).map(l => ({ ...l }))
    items.value = items.value.map(i => ({ ...i, lockId: null, rate: 0, amount: 0 }))
  }

  const saveCust = (d) => {
    const c = { name: d.name, ic: d.ic, type: d.type, mobile: d.mobile, bank: d.bank, acc: d.acc, advance: 0, locks: 0 }
    pickCust(c)
  }

  // ════════════════════════════════════════
  // ITEM METHODS
  // ════════════════════════════════════════

  const addItem = () => {
    const newId = nextId++
    lastAddedId.value = newId
    items.value.push(mkItem(newId))
    nextTick(() => { lastAddedId.value = null })
  }

  const removeItem = (id) => {
    if (items.value.length > 1) {
      items.value = items.value.filter(i => i.id !== id)
    }
  }

  const updItem = (id, field, val) => {
    items.value = items.value.map(item => {
      if (item.id !== id) return item
      const u = { ...item, [field]: val }
      if (field === 'purity') {
        u.item_code = resolveGoldBuybackItemCode(val, item.deds, item.is_white_gold)
        if (item.lockId) {
          const lk = locks.value.find(l => l.id === item.lockId)
          if (lk && lk.purity !== val) { u.lockId = null; u.rate = 0; u.amount = 0 }
        }
      }
      if (field === 'is_white_gold') {
        u.item_code = resolveGoldBuybackItemCode(item.purity, item.deds, val)
      }
      return u
    })
  }

  // 3-WAY CALC RULES
  // gross + rate  → amount = net × rate
  // rate + amount → gross derived so net = amount / rate
  // gross + amount→ rate = amount / net
  // all 3 filled, edit gross or rate → amount recalcs (rate stays if editing gross)
  // all 3 filled, edit amount        → rate recalcs (gross NEVER recalcs when all 3 filled)
  const recalc = (id, blurF, gv, rv, av) => {
    items.value = items.value.map(item => {
      if (item.id !== id) return item
      const deds = (item.deds || []).reduce((s, d) => s + (parseFloat(d.w) || 0), 0)
      const g = parseFloat(gv) || 0
      const r = parseFloat(rv) || 0
      const a = parseFloat(av) || 0
      const net = Math.max(0, g - deds)
      const u = { ...item, gross: g, net }

      if (!g && r > 0 && a > 0) {
        // rate + amount → derive gross
        const dn = parseFloat((a / r).toFixed(3))
        u.gross = parseFloat((dn + deds).toFixed(3)); u.net = dn; u.rate = r; u.amount = a
      } else if (g > 0 && r > 0 && !a) {
        // gross + rate → amount
        u.rate = r; u.amount = parseFloat((net * r).toFixed(2))
      } else if (g > 0 && a > 0 && !r) {
        // gross + amount → rate
        u.amount = a; u.rate = net > 0 ? parseFloat((a / net).toFixed(4)) : 0
      } else if (g > 0 && r > 0 && a > 0) {
        if (blurF === 'amount') {
          // edited amount → recalc rate
          u.amount = a; u.rate = net > 0 ? parseFloat((a / net).toFixed(4)) : r
        } else {
          // edited gross or rate → recalc amount
          u.rate = r; u.amount = parseFloat((net * r).toFixed(2))
        }
      }
      return u
    })
  }

  const clearDed = (id) => {
    items.value = items.value.map(item => {
      if (item.id !== id) return item
      const net = item.gross || 0
      const amt = item.rate > 0 ? parseFloat((net * item.rate).toFixed(2)) : item.amount
      return { ...item, deds: [], net, amount: amt, item_code: resolveGoldBuybackItemCode(item.purity, [], item.is_white_gold) }
    })
  }

  const applyDeds = (id, rows) => {
    items.value = items.value.map(item => {
      if (item.id !== id) return item
      const deds = rows.reduce((s, r) => s + (parseFloat(r.w) || 0), 0)
      const net = Math.max(0, (item.gross || 0) - deds)
      const amt = item.rate > 0 ? parseFloat((net * item.rate).toFixed(2)) : item.amount
      return { ...item, deds: rows, net, amount: amt, item_code: resolveGoldBuybackItemCode(item.purity, rows, item.is_white_gold) }
    })
  }

  // RATE LOCK LOGIC
  // Locks are stored in BLOK-DDMMYY-XXX documents (Buy). Sell = SLOK-DDMMYY-XXX (future).
  // When lock applied: rate + amount fields become read-only.
  // amount = net_weight × locked_rate (recalcs when gross/deductions change).
  // On Submit: ⚠️ MRADUL update BLOK document's used_weight += item.net_weight
  const applyLock = (id, lk) => {
    items.value = items.value.map(item => {
      if (item.id !== id) return item
      const net = item.net || item.gross || 0
      const amt = net > 0 ? parseFloat((net * lk.rate).toFixed(2)) : item.amount
      return { ...item, lockId: lk.id, rate: lk.rate, amount: amt, overageAck: false }
    })
    lockPop.value = null
  }

  const removeLock = (id) => {
    items.value = items.value.map(i =>
      i.id === id ? { ...i, lockId: null, rate: 0, amount: 0 } : i
    )
    lockPop.value = null
  }

  const keepRate = (id) => {
    items.value = items.value.map(i => i.id === id ? { ...i, overageAck: true } : i)
  }

  // Split excess: original item gross = remaining + totalDeds (so net = remaining)
  // New item line gets the excess weight with no lock
  const splitExcess = (id) => {
    const newId = nextId++
    const item = items.value.find(i => i.id === id)
    if (!item?.lockId) return
    const lk = locks.value.find(l => l.id === item.lockId)
    if (!lk) return
    const used = items.value.reduce((s, i) =>
      i.id !== id && i.lockId === item.lockId ? s + (i.net || i.gross || 0) : s, 0
    )
    const rem    = lk.originalWt - used
    const currNet = item.net || item.gross || 0
    const excess  = currNet - rem
    if (excess <= 0) return
    const totalDeds = (item.deds || []).reduce((s, d) => s + (parseFloat(d.w) || 0), 0)
    const newGross  = parseFloat((rem + totalDeds).toFixed(3))
    const newNet    = parseFloat(rem.toFixed(3))
    const newAmt    = parseFloat((newNet * item.rate).toFixed(2))
    const excessItem = {
      id: newId,
      desc: item.desc ? item.desc + ' (excess)' : '(excess)',
      purity: item.purity,
      item_code: resolveGoldBuybackItemCode(item.purity, [], item.is_white_gold), // excess has no deds
      gross: parseFloat(excess.toFixed(3)),
      net:   parseFloat(excess.toFixed(3)),
      deds: [], rate: 0, amount: 0,
      lockId: null, overageAck: false, bag: null, warehouse: null
    }
    const idx = items.value.findIndex(i => i.id === id)
    const updated = items.value.map(i =>
      i.id === id ? { ...i, gross: newGross, net: newNet, amount: newAmt, overageAck: false } : i
    )
    updated.splice(idx + 1, 0, excessItem)
    items.value = updated
  }

  // ── MIX ROW METHODS ──
  const addMixRow = () => {
    mixRows.value.push({ id: nextMixId++, mode: 'Cash', amount: '', bank_account: '' })
  }
  const removeMixRow = (id) => {
    mixRows.value = mixRows.value.filter(r => r.id !== id)
  }
  // Set both bag and warehouse for a single item row.
  // bag = warehouse = the Warehouse document name (they are the same thing in this system).
  // Pass null to clear back to default.
  const pickBagForItem = (id, bag, warehouse) => {
    items.value = items.value.map(item =>
      item.id === id ? { ...item, bag, warehouse } : item
    )
  }

  const updateMixRow = (id, field, val) => {
    mixRows.value = mixRows.value.map(r => {
      if (r.id !== id) return r
      const updated = { ...r, [field]: val }
      if (field === 'mode') {
        if (val === 'Bank Transfer') {
          updated.bank_account = updated.bank_account || bankAccount.value || bankAccounts.value[0]?.value || ''
        } else {
          updated.bank_account = ''
        }
      }
      return updated
    })
  }

  // ════════════════════════════════════════
  // DOCUMENT FLOW
  // Draft → Save (assigns PUR-DDMMYY-XXX series, ERPNext: PUR-.DD.MM.YY.-.###)
  // Review → read-only. Nothing posted.
  // Submit → GL posts, stock entries post, rate lock used_weight updates.
  //          Locked. Corrections via Cancel & Amend (creates PUR-xxx-1).
  // ════════════════════════════════════════

  const goReview = async () => {
    // Auto-delete fully empty lines silently
    items.value = items.value.filter(i => i.desc || (i.gross || 0) > 0 || (i.rate || 0) > 0)

    // Validation
    const errs = []
    if (!cust.value) errs.push('Customer is required.')
    if (!pm.value) errs.push('Payment Method is required.')
    if (pm.value === 'bank' && !bankAccount.value) errs.push('Bank account is required for Bank Transfer.')
    if (pm.value === 'mix') {
      const enteredRows = mixRows.value.filter(r => parseVal(r.amount) > 0)
      if (!enteredRows.length) errs.push('Enter at least one payment row for mixed payment.')
      if (Math.abs(mixDiff.value) >= 0.005) errs.push('Mixed payment total must match the invoice total.')
      const badBankRows = mixRows.value.filter(r => r.mode === 'Bank Transfer' && parseVal(r.amount) > 0 && !r.bank_account)
      if (badBankRows.length) errs.push('Please select bank account for all Bank Transfer rows in mixed payment.')
    }
    const filledItems = items.value.filter(i => i.desc || i.purity || (i.gross || 0) > 0 || (i.rate || 0) > 0)
    const partialItems = filledItems.filter(i => !i.desc || !(i.gross > 0) || !i.purity || !i.item_code)
    if (!filledItems.length) {
      errs.push('At least one item is required.')
    } else if (partialItems.length > 0) {
      errs.push(`${partialItems.length} item line(s) incomplete — each needs Description, Purity and Gross Weight.`)
    }
    if (errs.length > 0) { validationErrors.value = errs; return }
    validationErrors.value = []

    if (unresolved.value.length > 0) { ovgModal.value = true; return }

    // Fetch the next document number from the backend (preview — actual name assigned on submit)
    try {
      const res = await frappe.call({ method: 'anygold_custom.api.GoldBuyBack.submit.get_next_doc_no' })
      if (res.message) docNo.value = res.message
    } catch (_) { /* keep locally generated fallback */ }

    status.value = 'saved'
    view.value = 'review'
  }

  const confirmOvg = () => {
    items.value = items.value.map(i => i.lockId ? { ...i, overageAck: true } : i)
    ovgModal.value = false
    status.value = 'saved'
    view.value = 'review'
  }

  const goSubmit = async () => {
    try {
      // Prepare full form snapshot for backend persistence + accounting
      const submitItems = items.value
        .filter(i => (
          i.desc ||
          i.purity ||
          (i.gross || 0) > 0 ||
          (i.rate || 0) > 0 ||
          (i.amount || 0) > 0 ||
          (i.deds || []).length > 0
        ))
        .map(i => ({
          id: i.id,
          desc: i.desc,
          purity: i.purity,
          item_code: i.item_code || resolveGoldBuybackItemCode(i.purity, i.deds, i.is_white_gold),
          is_white_gold: i.is_white_gold || false,
          gross: i.gross || 0,
          net: i.net || i.gross || 0,
          deds: i.deds || [],
          rate: i.rate || 0,
          amount: i.amount || 0,
          lockId: i.lockId || null,
          overageAck: !!i.overageAck,
          bag: niH.value ? 'WS-Not In Hand' : (i.bag || defBag.value),
          warehouse: niH.value ? null : (i.warehouse || null)
        }))

      const submitMixRows = pm.value === 'mix'
        ? mixRows.value.map(r => ({
          ...r,
          amount: parseVal(r.amount),
          bank_account: r.mode === 'Bank Transfer' ? (r.bank_account || bankAccount.value || null) : null
        }))
        : []

      const submitData = {
        document_no: docNo.value,
        customer: cust.value,
        items: submitItems,
        payment_method: pm.value,
        mix_rows: submitMixRows,
        grand_total: gt.value,
        company: company.value,
        posting_date: new Date().toISOString().slice(0, 10),
        posting_time: time.value || new Date().toTimeString().slice(0, 8),
        bank_account: pm.value === 'bank' ? bankAccount.value : null,
        discount: disc.value,
        rounding: round.value,
        item_not_in_hand: niH.value,
        edit_posting_datetime: editTime.value,
        default_bag: niH.value ? 'WS-Not In Hand' : defBag.value,
        total_gross_weight: totGross.value,
        total_net_weight: totNet.value,
        total_amount: totAmt.value,
        total_xau: totXAU.value,
        customer_account_amount: custAcctAmt.value,
        projected_balance: projectedBalance.value,
        status: status.value
      }

      // Call the API
      const result = await frappe.call({
        method: "anygold_custom.api.GoldBuyBack.submit.submit_gold_buyback",
        args: {
          data: JSON.stringify(submitData)
        }
      })

      if (result.message.status === 'success') {
        // Update to the real backend-assigned document name (GBB-YYYY-NNNNN)
        if (result.message.submission) docNo.value = result.message.submission
        status.value = 'submitted'
        view.value = 'submitted'
        console.log('Submission successful:', result.message)
      } else {
        throw new Error(result.message.message || 'Submission failed')
      }
    } catch (error) {
      console.error('Submission error:', error)
      frappe.msgprint({
        title: 'Submission Error',
        message: error.message || 'Failed to submit gold buyback transaction',
        indicator: 'red'
      })
    }
  }

  const newPurchase = () => {
    const todayKey = getDocDateKey()
    const currentDateKey = docNo.value.split('-')[1]
    docSeq.value = currentDateKey === todayKey ? (docSeq.value + 1) : 1
    docNo.value = buildDocNo(docSeq.value)

    view.value = 'draft'; status.value = 'draft'
    niH.value = false; editTime.value = false
    cust.value = null; search.value = ''; pm.value = ''
    mixRows.value = [
      { id: 1, mode: 'Cash', amount: '', bank_account: '' },
      { id: 2, mode: 'Bank Transfer', amount: '', bank_account: bankAccount.value || bankAccounts.value[0]?.value || '' }
    ]
    nextMixId = 3; defBag.value = 'WS-Main Bag'
    items.value = [mkItem(1, true)]; nextId = 2
    round.value = false; disc.value = ''; discDisp.value = ''
    locks.value = []; lockOpen.value = false; glOpen.value = false
    validationErrors.value = []
    mSec.value = { doc: false, cust: true, items: false, pay: false, tots: false, summ: false, gl: false }
    time.value = new Date().toTimeString().slice(0, 8)
  }

  // ════════════════════════════════════════
  // EXPOSE
  // ════════════════════════════════════════
  return {
    // ── state refs ──
    view, status, docNo, niH, editTime, time,
    cust, search, showDD,
    company,
    pm, mixRows,
    bankAccounts, bankAccount, loadingPaymentAccounts,
    defBag, bagOptions, purityOptions, items, lastAddedId,
    round, disc, discDisp,
    locks, lockOpen, lockPop, bagPop,
    dedModal, showNewCust, ovgModal, glOpen,
    validationErrors, isMobile, mSec,

    // ── computed ──
    totGross, totNet, totAmt, gt, roundHint,
    totXAU, mixTot, mixDiff,
    filtCust, custAcctAmt, projectedBalance,
    glRows, stRows, summPay, bagSummary, itemSummary,
    unresolved, custIsDealer, showBag,

    // ── methods ──
    togSec,
    pickCust, saveCust,
    addItem, removeItem, updItem, recalc,
    clearDed, applyDeds,
    pickBagForItem,
    applyLock, removeLock, keepRate, splitExcess, getLockRem,
    addMixRow, removeMixRow, updateMixRow,
    goReview, confirmOvg, goSubmit, newPurchase,
    refreshPurityList,

    // ── helpers (exposed for child components) ──
    fmtRM, fmtWt, fmtWtRaw, dedNoteText,
    PURITY_XAU, PM_LABELS, BAG_OPTIONS, MOCK_CASH_BALANCE
  }
}
