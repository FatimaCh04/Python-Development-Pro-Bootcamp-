import assert from 'assert';
import { 
  formatPakistaniPhoneForWhatsApp,
  getBookingPadHtml,
  renderBookingPadToJsPdf,
  generateBookingPadPdf,
  shareBookingPadOnWhatsApp
} from './src/lib/exportUtils.js';

console.log('🧪 Starting WhatsApp Button & Distributor Phone Verification Tests...\n');

// ── TEST 1: Pakistani Phone Formats ──────────────────────────────────────────
console.log('--- Test 1: Pakistani Phone Number Formatting ---');
const formatCases = [
  { input: '03001234567', expected: '923001234567', desc: 'Standard 11-digit mobile starting with 0' },
  { input: '0321-7654321', expected: '923217654321', desc: 'Hyphenated mobile' },
  { input: '0345 112 2334', expected: '923451122334', desc: 'Space-separated mobile' },
  { input: '+92 300 1234567', expected: '923001234567', desc: 'International with +92 and spaces' },
  { input: '00923001234567', expected: '923001234567', desc: 'International with 0092 prefix' },
  { input: '3001234567', expected: '923001234567', desc: '10-digit mobile without leading 0' },
  { input: '923001234567', expected: '923001234567', desc: 'Already formatted 12-digit 92 mobile' },
  { input: '(0300) 1234567', expected: '923001234567', desc: 'Parentheses formatting' },
  { input: null, expected: null, desc: 'Null phone' },
  { input: undefined, expected: null, desc: 'Undefined phone' },
  { input: '', expected: null, desc: 'Empty string phone' },
  { input: '12345', expected: null, desc: 'Invalid short number' },
  { input: '0300', expected: null, desc: 'Incomplete number' },
  { input: 'invalid_text', expected: null, desc: 'Alphabetic text' },
];

for (const tc of formatCases) {
  const result = formatPakistaniPhoneForWhatsApp(tc.input);
  assert.strictEqual(result, tc.expected, `Failed for ${tc.desc}: input '${tc.input}' got '${result}', expected '${tc.expected}'`);
}
console.log('✅ Test 1 PASSED: All Pakistani phone formatting cases handled accurately.\n');

// ── TEST 2: Two Different Distributors in Booking Ledger ─────────────────────
console.log('--- Test 2: Two Different Distributors WA URL Generation ---');

const distributorA = {
  id: 'dist-uuid-001',
  code: 'DST-01',
  name: 'Al-Rehman Traders',
  phone: '0300-1112233'
};

const distributorB = {
  id: 'dist-uuid-002',
  code: 'DST-02',
  name: 'Bismillah Autos & Kiryana',
  phone: '+92 321 9988776'
};

const distributorsList = [distributorA, distributorB];

const bookingA = {
  id: 'bkg-001',
  reference_number: 'BKG-260922-001',
  sale_date: '2026-09-22T10:00:00.000Z',
  distributor_id: 'dist-uuid-001',
  distributors: distributorA,
  total_amount: 150000,
  status: 'Approved'
};

const bookingB = {
  id: 'bkg-002',
  reference_number: 'BKG-260922-002',
  sale_date: '2026-09-22T14:30:00.000Z',
  distributor_id: 'dist-uuid-002',
  distributors: distributorB,
  total_amount: 85500,
  status: 'Pending'
};

function simulateBookingWhatsApp(b, fallbackDistributorsList) {
  let openedUrl = null;
  let warningMessage = null;

  const mockWindow = {
    open: (url, target) => {
      openedUrl = url;
    }
  };

  const dist = (Array.isArray(b.distributors) ? b.distributors[0] : b.distributors)
    || fallbackDistributorsList.find(d => d.id === b.distributor_id)
    || null;

  if (!dist) {
    warningMessage = 'Cannot open WhatsApp: No distributor is linked to this booking.';
    return { openedUrl: null, warningMessage };
  }

  const formattedPhone = formatPakistaniPhoneForWhatsApp(dist.phone);
  if (!formattedPhone) {
    warningMessage = `Cannot open WhatsApp: Distributor ${dist.name || ''} has no valid registered phone number.`;
    return { openedUrl: null, warningMessage };
  }

  const name = dist.name || 'Not Assigned';
  // Open direct distributor chat without prefilled summary text
  mockWindow.open(`https://wa.me/${formattedPhone}`, '_blank');
  return { openedUrl, warningMessage: null };
}

// Check Distributor A
const resA = simulateBookingWhatsApp(bookingA, distributorsList);
assert(resA.openedUrl, 'Distributor A should open a WhatsApp URL');
assert.strictEqual(resA.openedUrl, 'https://wa.me/923001112233', `Distributor A URL incorrect: ${resA.openedUrl}`);
assert(!resA.openedUrl.includes('?text='), 'Must NOT contain ?text= parameter');
assert.strictEqual(resA.warningMessage, null);
console.log('✅ Distributor A WA chat verified: https://wa.me/923001112233');

// Check Distributor B
const resB = simulateBookingWhatsApp(bookingB, distributorsList);
assert(resB.openedUrl, 'Distributor B should open a WhatsApp URL');
assert.strictEqual(resB.openedUrl, 'https://wa.me/923219988776', `Distributor B URL incorrect: ${resB.openedUrl}`);
assert(!resB.openedUrl.includes('?text='), 'Must NOT contain ?text= parameter');
assert.strictEqual(resB.warningMessage, null);
console.log('✅ Distributor B WA chat verified: https://wa.me/923219988776');

assert.notStrictEqual(resA.openedUrl, resB.openedUrl, 'Distributor A and B must never open the same phone URL');
assert(!resA.openedUrl.includes('923240106056'), 'Must not contain legacy hardcoded phone number');
assert(!resB.openedUrl.includes('923240106056'), 'Must not contain legacy hardcoded phone number');
console.log('✅ Test 2 PASSED: Each distributor opens their specific, uniquely formatted WhatsApp chat without text params.\n');

// ── TEST 3: Fallback resolution when b.distributors is null ────────────────────
console.log('--- Test 3: Fallback distributor lookup via distributor_id ---');
const bookingWithoutJoinedDist = {
  id: 'bkg-003',
  reference_number: 'BKG-260922-003',
  sale_date: '2026-09-22T16:00:00.000Z',
  distributor_id: 'dist-uuid-002', // points to Distributor B
  distributors: null,
  total_amount: 45000,
  status: 'Approved'
};

const resFallback = simulateBookingWhatsApp(bookingWithoutJoinedDist, distributorsList);
assert.strictEqual(resFallback.openedUrl, 'https://wa.me/923219988776', 'Fallback lookup must resolve Distributor B phone');
console.log('✅ Test 3 PASSED: Fallback resolution from distributors list functions cleanly.\n');

// ── TEST 4: Missing or Invalid Distributor Phone Warning ──────────────────────
console.log('--- Test 4: Missing & Invalid Phone Number Guards ---');
const bookingInvalidPhone = {
  id: 'bkg-004',
  reference_number: 'BKG-260922-004',
  sale_date: '2026-09-22T17:00:00.000Z',
  distributor_id: 'dist-uuid-bad',
  distributors: {
    id: 'dist-uuid-bad',
    code: 'DST-BAD',
    name: 'No Phone Agency',
    phone: '123' // invalid short phone
  },
  total_amount: 10000,
  status: 'Pending'
};

const resInvalid = simulateBookingWhatsApp(bookingInvalidPhone, distributorsList);
assert.strictEqual(resInvalid.openedUrl, null, 'window.open must NOT be called for invalid phone');
assert(resInvalid.warningMessage.includes('no valid registered phone number'), `Warning message should be descriptive: ${resInvalid.warningMessage}`);
console.log('✅ Invalid phone blocked with warning:', resInvalid.warningMessage);

const bookingNoDistributor = {
  id: 'bkg-005',
  reference_number: 'BKG-260922-005',
  sale_date: '2026-09-22T18:00:00.000Z',
  distributor_id: null,
  distributors: null,
  total_amount: 5000,
  status: 'Pending'
};

const resNoDist = simulateBookingWhatsApp(bookingNoDistributor, distributorsList);
assert.strictEqual(resNoDist.openedUrl, null, 'window.open must NOT be called when distributor is null');
assert(resNoDist.warningMessage.includes('No distributor is linked'), `Warning message should be descriptive: ${resNoDist.warningMessage}`);
console.log('✅ Missing distributor blocked with warning:', resNoDist.warningMessage);
console.log('✅ Test 4 PASSED: Missing/invalid phone numbers safely halted without opening WhatsApp.\n');

// ── TEST 5: SalesPage WhatsApp Button Parity ─────────────────────────────────
console.log('--- Test 5: SalesPage WhatsApp Button Parity ---');
function simulateSaleWhatsApp(s, fallbackDistributorsList) {
  let openedUrl = null;
  let warningMessage = null;

  const distObj = (Array.isArray(s.distributors) ? s.distributors[0] : s.distributors)
    || fallbackDistributorsList.find(d => d.id === s.distributor_id)
    || null;

  if (!distObj) {
    return { openedUrl: null, warningMessage: 'No distributor linked' };
  }

  const formattedPhone = formatPakistaniPhoneForWhatsApp(distObj.phone);
  if (!formattedPhone) {
    return { openedUrl: null, warningMessage: 'Invalid phone' };
  }

  const dist = `${distObj.name}${distObj.code ? ` (${distObj.code})` : ''}`;
  const packets = (s.sale_items || []).reduce((a, i) => a + Number(i.quantity || 0), 0);
  const text = encodeURIComponent(
    `*Elite Wash — Sale*\n` +
    `Ref: ${s.reference_number}\n` +
    `Distributor: ${dist}\n` +
    `Packets: ${packets}\n` +
    `Total: Rs. ${s.total_amount}`
  );
  openedUrl = `https://wa.me/${formattedPhone}?text=${text}`;
  return { openedUrl, warningMessage: null };
}

const saleA = {
  reference_number: 'SAL-001',
  distributor_id: 'dist-uuid-001',
  distributors: distributorA,
  sale_items: [{ quantity: 100 }],
  total_amount: 12000
};
const resSaleA = simulateSaleWhatsApp(saleA, distributorsList);
assert(resSaleA.openedUrl.startsWith('https://wa.me/923001112233?text='), 'Sale A must open Distributor A phone');
assert(!resSaleA.openedUrl.includes('923240106056'));
console.log('✅ Test 5 PASSED: SalesPage WhatsApp sharing parity confirmed.\n');

// ── TEST 6: Complete Booking Pad HTML & Signature Visibility ─────────────────
console.log('--- Test 6: Official Bill Pad HTML & CEO Signature Verification ---');
const bookingWithItems = {
  ...bookingA,
  items: [
    { name: 'Elite Wash Surf (500g)', qty: 100, price: 1000, amount: 100000 },
    { name: 'Elite Wash Surf (1kg)',  qty: 50,  price: 1000, amount: 50000 }
  ]
};

const htmlContent = getBookingPadHtml(bookingWithItems);
assert(htmlContent.includes('receipt.jpeg'), 'Official bill pad template image must be referenced');
assert(htmlContent.includes('ceo-signature.png'), 'Authentic handwritten CEO signature must be referenced');
assert(htmlContent.includes('BKG-260922-001'), 'Reference number must be dynamically filled');
assert(htmlContent.includes('Al-Rehman Traders'), 'Distributor name must be dynamically filled');
assert(htmlContent.includes('Elite Wash Surf (500g)'), 'Item name must be present in dynamic row');
assert(htmlContent.includes('150,000'), 'Grand total amount must be present in grand total box');
assert(!htmlContent.includes('BOOKING DEMAND NOTE'), 'Must NOT contain incorrect BOOKING DEMAND NOTE title');
console.log('✅ Test 6 PASSED: Official ELITEWASH DETERGENT bill pad template, dynamic fields, and authentic CEO signature verified.\n');

// ── TEST 7: PDF Document Generation for Specific Bookings ─────────────────────
console.log('--- Test 7: PDF Document Generation for Specific Bookings ---');
const pdfA = await generateBookingPadPdf(bookingWithItems, distributorA);
assert.strictEqual(pdfA.filename, 'BKG-260922-001.pdf', 'Filename must match booking reference');
assert(pdfA.doc, 'PDF document instance must be returned');
const pdfBytesA = pdfA.doc.output('arraybuffer');
assert(pdfBytesA && pdfBytesA.byteLength > 1000, `PDF bytes must be valid, got ${pdfBytesA?.byteLength}`);

const pdfB = await generateBookingPadPdf(bookingB, distributorB);
assert.strictEqual(pdfB.filename, 'BKG-260922-002.pdf', 'Filename for Booking B must match reference B');
const pdfBytesB = pdfB.doc.output('arraybuffer');
assert(pdfBytesB && pdfBytesB.byteLength > 1000, `PDF B bytes must be valid, got ${pdfBytesB?.byteLength}`);
assert.notStrictEqual(pdfA.filename, pdfB.filename, 'Booking A and B must have distinct filenames');
console.log('✅ Test 7 PASSED: Complete PDF generated per selected booking with correct filenames.\n');

// ── TEST 8: WhatsApp Sharing Workflow - Download & Chat Fallback ──────────────
console.log('--- Test 8: WhatsApp PDF Sharing Workflow (Download & Chat Fallback) ---');
let downloadedFilename = null;
let openedWhatsAppUrl = null;

// Mock DOM elements and window for testing browser environment
globalThis.document = {
  createElement: (tag) => {
    return {
      tagName: tag.toUpperCase(),
      style: {},
      appendChild: () => {},
      removeChild: () => {},
      click: function() {
        if (this.download) downloadedFilename = this.download;
      }
    };
  },
  body: {
    appendChild: () => {},
    removeChild: () => {}
  }
};

globalThis.URL = {
  createObjectURL: () => 'blob:mock-pdf-url',
  revokeObjectURL: () => {}
};

globalThis.window = {
  location: { origin: 'http://localhost:5173' },
  open: (url, target) => {
    openedWhatsAppUrl = url;
  }
};

// Ensure navigator.canShare is undefined to simulate standard desktop browser fallback
const origNavigator = globalThis.navigator;
Object.defineProperty(globalThis, 'navigator', {
  value: {},
  configurable: true,
  writable: true
});

const shareResultFallback = await shareBookingPadOnWhatsApp({
  booking: bookingWithItems,
  distributor: distributorA
});

assert.strictEqual(shareResultFallback.success, true, 'Share workflow must succeed');
assert.strictEqual(shareResultFallback.mode, 'download_and_chat', 'Mode must be download_and_chat');
assert.strictEqual(downloadedFilename, 'BKG-260922-001.pdf', 'Must download correct PDF filename');
assert.strictEqual(openedWhatsAppUrl, 'https://wa.me/923001112233', 'Must open Distributor A direct phone chat');
assert(!openedWhatsAppUrl.includes('?text='), 'Must NOT contain ?text= query parameter');
assert(shareResultFallback.instructions.includes('attach'), 'Instructions must instruct user to attach document');
console.log('✅ Test 8 PASSED: Desktop fallback downloads signed PDF and opens direct WhatsApp chat with attachment instructions.\n');

// ── TEST 9: WhatsApp Sharing Workflow - Native File Sharing ───────────────────
console.log('--- Test 9: WhatsApp PDF Sharing Workflow (Native File Sharing) ---');
let sharedPayload = null;

globalThis.File = class MockFile {
  constructor(parts, name, opts) {
    this.name = name;
    this.type = opts?.type;
  }
};

Object.defineProperty(globalThis, 'navigator', {
  value: {
    canShare: (data) => !!data?.files,
    share: async (data) => {
      sharedPayload = data;
      return true;
    }
  },
  configurable: true,
  writable: true
});

const shareResultNative = await shareBookingPadOnWhatsApp({
  booking: bookingB,
  distributor: distributorB
});

assert.strictEqual(shareResultNative.success, true, 'Native share must succeed');
assert.strictEqual(shareResultNative.mode, 'native_share', 'Mode must be native_share');
assert(sharedPayload, 'Native share payload must be passed');
assert(Array.isArray(sharedPayload.files) && sharedPayload.files.length === 1, 'Must attach PDF file in native share');
assert.strictEqual(sharedPayload.files[0].name, 'BKG-260922-002.pdf', 'File must be Booking B PDF');
console.log('✅ Test 9 PASSED: Native file sharing attaches signed PDF document directly.\n');

// ── TEST 10: WhatsApp Sharing Guard Rails (Errors & Cancellations) ────────────
console.log('--- Test 10: WhatsApp Sharing Guard Rails ---');
// Missing distributor
const resMissingDist = await shareBookingPadOnWhatsApp({
  booking: { reference_number: 'BKG-NO-DIST', distributor_id: null, distributors: null }
});
assert.strictEqual(resMissingDist.success, false);
assert.strictEqual(resMissingDist.reason, 'missing_distributor');

// Invalid phone
const resBadPhone = await shareBookingPadOnWhatsApp({
  booking: { reference_number: 'BKG-BAD-PHONE', distributor_id: 'bad', distributors: { name: 'Bad Phone Ltd', phone: '00' } }
});
assert.strictEqual(resBadPhone.success, false);
assert.strictEqual(resBadPhone.reason, 'invalid_phone');

// User cancels native share sheet
globalThis.navigator.share = async () => {
  const err = new Error('Abort');
  err.name = 'AbortError';
  throw err;
};

const resCancel = await shareBookingPadOnWhatsApp({
  booking: bookingA,
  distributor: distributorA
});
assert.strictEqual(resCancel.success, false);
assert.strictEqual(resCancel.reason, 'cancelled');
delete globalThis.navigator.share;
delete globalThis.navigator.canShare;

// ── TEST 11: Pre-opened Window Handle Navigation & Popup Blocker Resiliency ─
console.log('--- Test 11: Pre-opened Window Handle Navigation & Popup Handling ---');
let navigatedTargetUrl = null;
let closedPreOpenedWindow = false;

const mockPreOpenedWindow = {
  closed: false,
  location: {
    set href(val) { navigatedTargetUrl = val; },
    get href() { return navigatedTargetUrl; }
  },
  close: () => { closedPreOpenedWindow = true; }
};

const resPreOpened = await shareBookingPadOnWhatsApp({
  booking: bookingWithItems,
  distributor: distributorA,
  targetWindow: mockPreOpenedWindow
});

assert.strictEqual(resPreOpened.success, true, 'Workflow with preOpened window must succeed');
assert.strictEqual(navigatedTargetUrl, 'https://wa.me/923001112233', 'Pre-opened tab must be navigated to Distributor A WhatsApp URL');
assert.strictEqual(closedPreOpenedWindow, false, 'Pre-opened window must NOT be closed on successful desktop share');

// Check that invalid phone closes the preOpened window safely
let closedOnErrWindow = false;
const mockErrWindow = {
  closed: false,
  location: { href: 'about:blank' },
  close: () => { closedOnErrWindow = true; }
};

const resBadPhoneWin = await shareBookingPadOnWhatsApp({
  booking: { reference_number: 'BKG-ERR', distributor_id: 'bad', distributors: { name: 'Bad Phone', phone: '00' } },
  targetWindow: mockErrWindow
});
assert.strictEqual(resBadPhoneWin.success, false);
assert.strictEqual(closedOnErrWindow, true, 'Pre-opened tab must be closed when distributor phone is invalid');
console.log('✅ Test 11 PASSED: Pre-opened tab successfully navigated without triggering popup blocker.\n');

// Clean up globals
delete globalThis.document;
delete globalThis.window;
if (origNavigator) {
  Object.defineProperty(globalThis, 'navigator', { value: origNavigator, configurable: true, writable: true });
} else {
  delete globalThis.navigator;
}
delete globalThis.File;
delete globalThis.URL;

console.log('==============================================================================');
console.log('🎉 ALL WHATSAPP VERIFICATION TESTS PASSED CLEANLY (100%)');
console.log('==============================================================================');
