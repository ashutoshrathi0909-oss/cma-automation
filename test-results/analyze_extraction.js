const fs = require('fs');
const data = JSON.parse(fs.readFileSync('test-results/MSL_extraction_output.json', 'utf8'));

const expected_pl = [
  { key: 'Sale of Products Domestic', amount: 213076, keywords: ['sale of products', 'domestic sales', 'sale-domestic'] },
  { key: 'Sale of Products Export', amount: 9906, keywords: ['export sales', 'export'] },
  { key: 'Interest Income', amount: 103.56, keywords: ['interest income', 'interest received'] },
  { key: 'Export Incentive / RoDTEP', amount: 86.06, keywords: ['rodtep', 'export incentive', 'duty drawback'] },
  { key: 'Insurance Claim Received', amount: 355.79, keywords: ['insurance claim'] },
  { key: 'Goods Purchased Indigenous', amount: 93468.53, keywords: ['goods purchased', 'raw material purchase', 'purchase indigenous'] },
  { key: 'Carriage Inwards', amount: 256.44, keywords: ['carriage inward', 'freight inward'] },
  { key: 'Salaries and Wages', amount: 12748.73, keywords: ['salary', 'wages', 'salaries'] },
  { key: 'Bonus', amount: 88.83, keywords: ['bonus'] },
  { key: 'PF Contribution', amount: 530.35, keywords: ['pf contribution', 'provident fund', "employer's contribution"] },
  { key: 'Staff Welfare', amount: 73.00, keywords: ['staff welfare'] },
  { key: 'Bank Charges', amount: 539.95, keywords: ['bank charges', 'bank commission'] },
  { key: 'Bank Interest CC/OD', amount: 1743.11, keywords: ['interest on cc', 'cash credit interest', 'bank interest', 'interest on od'] },
  { key: 'Other Charges (finance)', amount: 521.65, keywords: ['processing fee', 'loan processing', 'other finance charges'] },
  { key: 'Power Coal Fuel', amount: 3539.64, keywords: ['power', 'fuel', 'coal', 'electricity'] },
  { key: 'Stores and Spares', amount: 4429.82, keywords: ['stores', 'spares', 'consumables'] },
  { key: 'Job Work Charges', amount: 284.47, keywords: ['job work'] },
  { key: 'Rent', amount: 800.00, keywords: ['rent', 'lease rent'] },
  { key: 'R&M Plant & Machinery', amount: 157.18, keywords: ['repair', 'maintenance', 'plant', 'machinery'] },
  { key: 'R&M Others', amount: 657.10, keywords: ['repair', 'maintenance others', 'r&m'] },
  { key: 'Insurance', amount: 238.65, keywords: ['insurance'] },
  { key: 'Rates & Taxes', amount: 86.25, keywords: ['rates', 'taxes', 'rates and tax'] },
  { key: 'Audit Fees', amount: 135.00, keywords: ['audit fee', 'statutory audit'] },
  { key: 'Freight Outward', amount: 154.43, keywords: ['freight outward', 'freight charges'] },
  { key: 'Discount Allowed', amount: 673.55, keywords: ['discount'] },
  { key: 'Bad Debts Written Off', amount: 650.08, keywords: ['bad debt'] },
  { key: 'Exchange Rate Fluctuation', amount: 147.02, keywords: ['exchange', 'forex', 'foreign exchange'] },
  { key: 'Tour & Travel', amount: 163.49, keywords: ['travel', 'tour'] },
  { key: 'Consultancy Fees', amount: 1360.49, keywords: ['consultancy', 'professional fee'] },
  { key: 'General Expenses', amount: 212.60, keywords: ['general expenses', 'miscellaneous'] },
  { key: 'P&L on Sale of FA', amount: 336.09, keywords: ['profit on sale', 'sale of fa', 'sale of fixed'] },
  { key: 'Liability Written Off', amount: 100.00, keywords: ['liability written'] },
];

const expected_bs = [
  { key: 'Paid-up Capital', amount: 21609.46, keywords: ['share capital', 'paid up capital', 'equity shares'] },
  { key: 'General Reserve', amount: 750.00, keywords: ['general reserve'] },
  { key: 'Share Premium', amount: 12444.00, keywords: ['securities premium', 'share premium'] },
  { key: 'Provision for Gratuity', amount: 2171.62, keywords: ['gratuity', 'provision for gratuity'] },
  { key: 'CC IDBI Working Capital', amount: 14293.87, keywords: ['idbi', 'cash credit from idbi'] },
  { key: 'Current maturities TL', amount: 1409.66, keywords: ['current maturities', 'term loan'] },
  { key: 'Unsecured Loans Promoters', amount: 41768.22, keywords: ['unsecured loan', 'promoter'] },
  { key: 'Sundry Creditors', amount: 25432, keywords: ['sundry creditor', 'trade payable', 'creditors'] },
  { key: 'Stock in Trade', amount: 87874.07, keywords: ['stock', 'inventory', 'stock in trade'] },
  { key: 'Trade Receivables', amount: 43052.86, keywords: ['trade receivable', 'debtors', 'sundry debtor'] },
  { key: 'Security Deposits', amount: 1752.55, keywords: ['security deposit', 'deposit with govt'] },
  { key: 'Advance Income Tax', amount: 4832.27, keywords: ['advance tax', 'advance income tax'] },
  { key: 'GST Balance Govt Auth', amount: 1344.08, keywords: ['gst', 'government authorit', 'govt auth'] },
];

const allExpected = [...expected_pl, ...expected_bs];

function pct(a, b) { return b !== 0 ? Math.abs(Math.abs(a)-b)/b : 999; }

const report = [];
for (const exp of allExpected) {
  const byKey = data.filter(i => i.description && exp.keywords.some(k => i.description.toLowerCase().includes(k.toLowerCase())));
  let bestMatch = null;
  let bestPct = 999;
  for (const item of byKey) {
    const p = pct(item.amount, exp.amount);
    if (p < bestPct) { bestPct = p; bestMatch = item; }
  }

  let status, foundAmt, note;
  if (bestMatch) {
    if (bestPct < 0.02) {
      status = 'CORRECT';
      foundAmt = bestMatch.amount;
      note = bestMatch.description.replace(/\n/g,' ').substring(0,60);
    } else {
      const pctRupees = pct(bestMatch.amount, exp.amount * 1000);
      if (pctRupees < 0.02) {
        status = 'WRONG_UNIT';
        foundAmt = '' + bestMatch.amount + ' (full rupees, expected Rs.000: ' + exp.amount + ')';
        note = bestMatch.description.replace(/\n/g,' ').substring(0,60);
      } else {
        status = 'AMT_WRONG';
        foundAmt = '' + bestMatch.amount + ' vs expected ' + exp.amount;
        note = bestMatch.description.replace(/\n/g,' ').substring(0,60);
      }
    }
  } else {
    status = 'MISSING';
    foundAmt = null;
    note = '';
  }
  report.push({ key: exp.key, expectedAmt: exp.amount, status, foundAmt, note });
}

console.log('=== EXTRACTION QUALITY REPORT ===\n');
console.log('CORRECT (' + report.filter(r=>r.status==='CORRECT').length + '):');
report.filter(r=>r.status==='CORRECT').forEach(r => console.log('  [OK]   ' + r.key + ' = ' + r.foundAmt));
console.log('');
console.log('WRONG UNIT (extracted in full rupees):');
report.filter(r=>r.status==='WRONG_UNIT').forEach(r => console.log('  [UNIT] ' + r.key + ' | ' + r.foundAmt));
console.log('');
console.log('WRONG AMOUNT:');
report.filter(r=>r.status==='AMT_WRONG').forEach(r => console.log('  [AMT]  ' + r.key + ' | found: ' + r.foundAmt + ' | matched via: ' + r.note));
console.log('');
console.log('MISSING (not found by keyword):');
report.filter(r=>r.status==='MISSING').forEach(r => console.log('  [MISS] ' + r.key + ' (expected: ' + r.expectedAmt + ')'));
console.log('');
const counts = { CORRECT: 0, WRONG_UNIT: 0, AMT_WRONG: 0, MISSING: 0 };
report.forEach(r => counts[r.status]++);
console.log('SUMMARY: CORRECT=' + counts.CORRECT + ', WRONG_UNIT=' + counts.WRONG_UNIT + ', AMT_WRONG=' + counts.AMT_WRONG + ', MISSING=' + counts.MISSING + ' / ' + allExpected.length);
console.log('Total items extracted: ' + data.length);
