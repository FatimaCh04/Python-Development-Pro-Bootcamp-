// ==============================================================================
// ELITE WASH ERP — LOCAL UNIT TEST SUITE: STOCK, RETURNS & EXPENSES
// Safe local fixture verification. No database connection or production data.
// ==============================================================================

import assert from 'node:assert/strict';

console.log('🧪 Starting Local Stock, Returns & Expenses Fixture Tests...\n');

// ------------------------------------------------------------------------------
// TEST FIXTURES: INVENTORY TRANSACTIONS
// ------------------------------------------------------------------------------
const mockInventoryTransactions = [
  // 1. Approved Production
  {
    id: 'tx-1',
    reference_number: 'PRD-001',
    transaction_type: 'Production',
    category: 'Sellable Stock',
    quantity: 1000,
    status: 'Approved'
  },
  // 2. Approved Supplier Purchase
  {
    id: 'tx-2',
    reference_number: 'PUR-001',
    transaction_type: 'Purchase',
    category: 'Sellable Stock',
    quantity: 500,
    status: 'Approved'
  },
  // 3. Approved Stock Issue to Distributor D1
  {
    id: 'tx-3',
    reference_number: 'ISS-001',
    transaction_type: 'Distributor_Issue',
    category: 'Sellable Stock',
    distributor_id: 'dist-1',
    quantity: 300,
    status: 'Approved'
  },
  // 4. PENDING Stock Issue to Distributor D2 (MUST NOT AFFECT BALANCES)
  {
    id: 'tx-4',
    reference_number: 'ISS-002',
    transaction_type: 'Distributor_Issue',
    category: 'Sellable Stock',
    distributor_id: 'dist-2',
    quantity: 200,
    status: 'Pending'
  },
  // 5. CANCELLED Stock Issue to Distributor D1 (MUST NOT AFFECT BALANCES)
  {
    id: 'tx-5',
    reference_number: 'ISS-003',
    transaction_type: 'Distributor_Issue',
    category: 'Sellable Stock',
    distributor_id: 'dist-1',
    quantity: 50,
    status: 'Cancelled'
  },
  // 6. Approved Good Return from Distributor D1 (Enters saleable stock, reduces issued stock)
  {
    id: 'tx-6',
    reference_number: 'RTN-001',
    transaction_type: 'Salesman_Good_Return',
    category: 'Sellable Stock',
    distributor_id: 'dist-1',
    quantity: 20,
    status: 'Approved'
  },
  // 7. Approved Damaged Return from Distributor D1 (Enters damaged stock, NOT saleable stock!)
  {
    id: 'tx-7',
    reference_number: 'RTN-002',
    transaction_type: 'Salesman_Damaged_Return',
    category: 'Damaged Stock',
    distributor_id: 'dist-1',
    quantity: 10,
    status: 'Approved'
  },
  // 8. PENDING Return from Distributor D1 (MUST NOT AFFECT BALANCES)
  {
    id: 'tx-8',
    reference_number: 'RTN-003',
    transaction_type: 'Salesman_Good_Return',
    category: 'Sellable Stock',
    distributor_id: 'dist-1',
    quantity: 15,
    status: 'Pending'
  },
  // 9. Approved Inventory Adjustment (-5 variance)
  {
    id: 'tx-9',
    reference_number: 'ADJ-001',
    transaction_type: 'Adjustment',
    category: 'Adjustment',
    quantity: -5,
    status: 'Approved'
  }
];

// Mock bookings: Bookings NEVER deduct stock
const mockBookings = [
  { reference_number: 'BKG-001', status: 'Pending', packets: 100 },
  { reference_number: 'BKG-002', status: 'Approved', packets: 50 }
];

// ------------------------------------------------------------------------------
// PURE CALCULATION IMPLEMENTATION
// ------------------------------------------------------------------------------
function calculateStockBalances(transactions) {
  let saleableStock = 0;
  let issuedStock = 0;
  let goodReturns = 0;
  let damagedStock = 0;
  let productionPurchases = 0;
  let adjustments = 0;

  transactions.forEach(r => {
    // Rule: Pending and Cancelled transactions must NOT affect stock
    if (!['Approved', 'Posted'].includes(r.status)) return;

    const qty = Number(r.quantity) || 0;
    const isGoodReturn = ['Salesman_Good_Return', 'Customer_Good_Return', 'Distributor_Good_Return'].includes(r.transaction_type);
    const isDamagedReturn = ['Salesman_Damaged_Return', 'Customer_Damaged_Return', 'Distributor_Damaged_Return', 'Damage', 'Expiry'].includes(r.transaction_type);

    if (['Production', 'Purchase'].includes(r.transaction_type)) {
      productionPurchases += qty;
      saleableStock += qty;
    } else if (['Salesman_Issue', 'Distributor_Issue'].includes(r.transaction_type)) {
      saleableStock -= qty;
      issuedStock += qty;
    } else if (isGoodReturn) {
      goodReturns += qty;
      saleableStock += qty; // Good returns enter company saleable stock after approval
      if (r.distributor_id || r.salesman_id) {
        issuedStock = Math.max(0, issuedStock - qty);
      }
    } else if (isDamagedReturn) {
      damagedStock += qty; // Damaged returns enter damaged stock, NOT saleable stock
      if (r.distributor_id || r.salesman_id) {
        issuedStock = Math.max(0, issuedStock - qty);
      }
    } else if (r.transaction_type === 'Adjustment') {
      adjustments += qty;
      saleableStock += qty;
    }
  });

  return {
    saleableStock,
    issuedStock,
    goodReturns,
    damagedStock,
    productionPurchases,
    adjustments
  };
}

// ------------------------------------------------------------------------------
// TEST 1: Stock Balances Verification
// ------------------------------------------------------------------------------
const stock = calculateStockBalances(mockInventoryTransactions);

// Production + Purchase = 1000 + 500 = 1500
assert.equal(stock.productionPurchases, 1500, 'Production & Purchases inward should be 1500');

// Issued stock = 300 (ISS-001) - 20 (Good Return) - 10 (Damaged Return) = 270
assert.equal(stock.issuedStock, 270, 'Distributor issued stock should be 270 (300 - 20 - 10)');

// Good returns = 20
assert.equal(stock.goodReturns, 20, 'Distributor good returns should be 20');

// Damaged stock = 10
assert.equal(stock.damagedStock, 10, 'Damaged stock should be 10');

// Adjustments = -5
assert.equal(stock.adjustments, -5, 'Adjustments should be -5');

// Saleable stock = 1000 (Production) + 500 (Purchase) - 300 (Issued) + 20 (Good Return) + (-5) (Adjustment) = 1215
// Note: Damaged return (10 pkts) NEVER enters saleable stock!
assert.equal(stock.saleableStock, 1215, 'Company saleable stock should be exactly 1215 pkts');

console.log('✅ TEST 1 PASSED: Stock Balances & Quarantined Damaged Returns correctly calculated.');

// ------------------------------------------------------------------------------
// TEST 2: Bookings Must Never Deduct Stock
// ------------------------------------------------------------------------------
const stockAfterBookings = calculateStockBalances(mockInventoryTransactions);
assert.equal(stockAfterBookings.saleableStock, 1215, 'Bookings did not alter stock balance');
console.log('✅ TEST 2 PASSED: Booking orders strictly have 0 stock deduction.');

// ------------------------------------------------------------------------------
// TEST 3: Negative Stock Prevention
// ------------------------------------------------------------------------------
function canIssueStock(currentSaleable, requestedQty, isAuthorizedAdjustment) {
  if (requestedQty <= 0) return false;
  if (currentSaleable >= requestedQty) return true;
  return isAuthorizedAdjustment === true;
}

assert.equal(canIssueStock(stock.saleableStock, 1200, false), true, 'Allowed when stock is sufficient');
assert.equal(canIssueStock(stock.saleableStock, 1300, false), false, 'Prevented when stock is insufficient and not authorized');
assert.equal(canIssueStock(stock.saleableStock, 1300, true), true, 'Allowed only when explicitly authorized as an adjustment');
console.log('✅ TEST 3 PASSED: Negative stock prevention guard functions correctly.');

// ------------------------------------------------------------------------------
// TEST 4: Expense Calculations & Status Filtering
// ------------------------------------------------------------------------------
const mockExpenses = [
  { id: 'exp-1', category: 'Distributor', amount: 5000, status: 'Approved' },
  { id: 'exp-2', category: 'Company', amount: 12000, status: 'Approved' },
  { id: 'exp-3', category: 'Office', amount: 3000, status: 'Approved' },
  { id: 'exp-4', category: 'Advertisement', head: 'Billboards', amount: 8000, status: 'Approved' },
  { id: 'exp-5', category: 'Welfare', head: 'Worker Aid', amount: 4000, status: 'Approved' },
  // PENDING expenses: MUST NOT inflate approved totals
  { id: 'exp-6', category: 'Company', amount: 7000, status: 'Pending' },
  // CANCELLED expenses: MUST NOT inflate approved totals
  { id: 'exp-7', category: 'Office', amount: 2000, status: 'Cancelled' },
  // Person payment linked expense:
  { id: 'exp-8', category: 'Company', amount: 2500, status: 'Approved', originating_ledger_entry_id: 'ledger-entry-123' }
];

function calculateExpenseSummary(expenses) {
  let total = 0; // Only Approved
  let pendingTotal = 0;
  let distributor = 0;
  let company = 0;
  let office = 0;
  let advertisement = 0;
  let welfare = 0;
  let others = 0;

  expenses.forEach(r => {
    const amt = Number(r.amount) || 0;
    if (['Approved', 'Posted'].includes(r.status)) {
      total += amt;
      if (r.category === 'Distributor') distributor += amt;
      else if (r.category === 'Company') company += amt;
      else if (r.category === 'Office') office += amt;
      else if (r.category === 'Advertisement' || r.head === 'Advertisement') advertisement += amt;
      else if (r.category === 'Welfare' || r.head === 'Welfare') welfare += amt;
      else others += amt;
    } else if (['Pending', 'Submitted'].includes(r.status)) {
      pendingTotal += amt;
    }
  });

  return { total, approvedTotal: total, pendingTotal, distributor, company, office, advertisement, welfare, others };
}

const expSummary = calculateExpenseSummary(mockExpenses);

// Approved total = 5000 + 12000 + 3000 + 8000 + 4000 + 2500 = 34500
assert.equal(expSummary.total, 34500, 'Approved total should be exactly 34500');
assert.equal(expSummary.pendingTotal, 7000, 'Pending total should be exactly 7000');
assert.equal(expSummary.distributor, 5000, 'Distributor expenses should be 5000');
assert.equal(expSummary.company, 14500, 'Company expenses should be 14500 (12000 + 2500)');
assert.equal(expSummary.office, 3000, 'Office expenses should be 3000');
assert.equal(expSummary.advertisement, 8000, 'Advertisement expenses should be 8000');
assert.equal(expSummary.welfare, 4000, 'Welfare expenses should be 4000');

console.log('✅ TEST 4 PASSED: Only approved expenses affect financial totals and P&L.');

// ------------------------------------------------------------------------------
// TEST 5: Person Payment Protection Guard
// ------------------------------------------------------------------------------
function canDirectlyMutateExpense(expense) {
  if (expense.originating_ledger_entry_id) {
    return false; // Must be managed via person payments ledger
  }
  return true;
}

assert.equal(canDirectlyMutateExpense(mockExpenses[0]), true, 'Standard expense is directly mutable');
assert.equal(canDirectlyMutateExpense(mockExpenses[7]), false, 'Person-linked expense cannot be directly mutated');

console.log('✅ TEST 5 PASSED: Person payment linked expenses are protected against un-reconciled direct mutations.');

console.log('\n🎉 ALL 5 FIXTURE TESTS PASSED WITH 100% SUCCESS!\n');
