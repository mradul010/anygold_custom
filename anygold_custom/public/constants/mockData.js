// ── MOCK CUSTOMERS ──
// Exact match to original HTML mockup
// cust.advance: positive = AR (they owe us), negative = AP (we owe them)
// ⚠️ MRADUL: replace with frappe.call get_party_balance
export const MOCK_CUSTOMERS = [
  { name: 'KAMAL HOSSIN',              ic: '900312-14-5678', type: 'Dealer',     mobile: '0123456789', bank: 'Maybank', acc: '1122334455', advance: 0,    locks: 5 },
  { name: 'FARHANA BINTI ZAINAL',      ic: '850601-08-3210', type: 'Individual', mobile: '0198765432', bank: '',        acc: '',           advance: 0,    locks: 0 },
  { name: 'AHMAD KHAIRUL FAHMI',       ic: '780910-05-1234', type: 'Dealer',     mobile: '0112233445', bank: 'CIMB',   acc: '8600123456', advance: 5000, locks: 7 },
  { name: 'SOW WENG KEAN',             ic: '720505-10-1234', type: 'Individual', mobile: '0177654321', bank: '',        acc: '',           advance: 0,    locks: 0 },
  { name: 'NUR NABILLAH BINTI KHOSIM', ic: '921114-08-5432', type: 'Individual', mobile: '0134567890', bank: '',        acc: '',           advance: 0,    locks: 0 },
]

// ── MOCK RATE LOCKS ──
// Exact match to original HTML mockup
// Lock series: LOK-XXX (mock). Production: BLOK-DDMMYY-XXX
// Each lock has a time field for "Locked On" column display
export const MOCK_LOCKS = {
  'AHMAD KHAIRUL FAHMI': [
    { id: 'LOK-001', purity: '916',  rate: 550, originalWt: 50,  usedWt: 0, status: 'Active',   time: '04/04 at 09:00am' },
    { id: 'LOK-002', purity: '750',  rate: 320, originalWt: 30,  usedWt: 0, status: 'Expiring', time: '04/04 at 11:30am' },
    { id: 'LOK-003', purity: '916',  rate: 548, originalWt: 20,  usedWt: 0, status: 'Overdue',  time: '04/04 at 2:15pm'  },
    { id: 'LOK-004', purity: '916',  rate: 545, originalWt: 100, usedWt: 0, status: 'Active',   time: '04/04 at 3:00pm'  },
    { id: 'LOK-005', purity: '999',  rate: 580, originalWt: 40,  usedWt: 0, status: 'Active',   time: '04/04 at 4:15pm'  },
    { id: 'LOK-006', purity: '750',  rate: 318, originalWt: 60,  usedWt: 0, status: 'Expiring', time: '05/04 at 08:30am' },
    { id: 'LOK-007', purity: '916',  rate: 551, originalWt: 35,  usedWt: 0, status: 'Active',   time: '05/04 at 09:45am' },
  ],
  'KAMAL HOSSIN': [
    { id: 'LOK-010', purity: '916',  rate: 552, originalWt: 25, usedWt: 0, status: 'Active',   time: '05/04 at 11:00am' },
    { id: 'LOK-011', purity: '916',  rate: 549, originalWt: 40, usedWt: 0, status: 'Active',   time: '05/04 at 01:00pm' },
    { id: 'LOK-012', purity: '750',  rate: 315, originalWt: 20, usedWt: 0, status: 'Expiring', time: '05/04 at 03:30pm' },
    { id: 'LOK-013', purity: '9999', rate: 595, originalWt: 15, usedWt: 0, status: 'Active',   time: '06/04 at 10:00am' },
    { id: 'LOK-014', purity: '916',  rate: 547, originalWt: 80, usedWt: 0, status: 'Overdue',  time: '06/04 at 11:00am' },
  ],
}
