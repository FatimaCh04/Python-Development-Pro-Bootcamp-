/**
 * Elite Wash - Export & Print Utilities
 * Generates real CSV, PDF (via jsPDF & printable window), and WhatsApp share links.
 */
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import html2canvas from 'html2canvas';

// --- CSV EXPORT ---
export function exportToCsv(filename, headers, rows) {
  if (!rows || rows.length === 0) {
    alert('No data to export.');
    return;
  }

  const escapeCell = (val) => {
    if (val === null || val === undefined) return '""';
    const str = String(val).replace(/"/g, '""');
    return `"${str}"`;
  };

  const headerRow = headers.map(escapeCell).join(',');
  const dataRows = rows.map(r => r.map(escapeCell).join(','));
  const csvContent = '\uFEFF' + [headerRow, ...dataRows].join('\r\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename.endsWith('.csv') ? filename : `${filename}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// --- PRINTABLE REPORT / WINDOW ---
export function printReport({ title, subtitle = '', dateRange = '', headers, rows, summaryBoxes = [] }) {
  const win = window.open('', '_blank');
  if (!win) {
    alert('Please allow popups to print reports.');
    return;
  }

  const summaryHtml = (summaryBoxes || []).map(b => `
    <div style="flex:1;min-width:140px;background:#f5f3ed;border:1px solid #e0ddd5;border-radius:6px;padding:10px 14px;">
      <div style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">${b.label}</div>
      <div style="font-size:16px;font-weight:700;color:#111827;">${b.value}</div>
    </div>
  `).join('');

  const tableHead = headers.map(h => `<th style="text-align:left;padding:8px 10px;border-bottom:2px solid #d1d5db;font-size:12px;font-weight:600;background:#f9fafb;">${h}</th>`).join('');
  const tableRows = rows.map(r => `
    <tr style="border-bottom:1px solid #e5e7eb;">
      ${r.map(c => `<td style="padding:8px 10px;font-size:12px;">${c !== null && c !== undefined ? c : '—'}</td>`).join('')}
    </tr>
  `).join('');

  const html = `
    <!DOCTYPE html>
    <html>
      <head>
        <title>${title} - Elite Wash</title>
        <style>
          @page { size: auto; margin: 15mm; }
          body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #1f2937; margin: 0; padding: 20px; }
          .header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #0e7c86; padding-bottom: 12px; margin-bottom: 16px; }
          .logo { font-size: 20px; font-weight: 700; color: #0e7c86; letter-spacing: -0.02em; }
          .sub { font-size: 11px; color: #6b7280; }
          .title { font-size: 18px; font-weight: 700; margin: 0 0 4px; }
          .dates { font-size: 12px; color: #4b5563; }
          .summary-grid { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
          table { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
          .signatures { display: flex; justify-content: space-between; margin-top: 50px; padding-top: 20px; }
          .sig-box { width: 200px; border-top: 1px solid #9ca3af; text-align: center; font-size: 11px; color: #4b5563; padding-top: 6px; }
        </style>
      </head>
      <body>
        <div class="header">
          <div>
            <div class="logo">ELITE WASH</div>
            <div class="sub">Surf Stock &amp; Ledger Control System</div>
          </div>
          <div style="text-align:right;">
            <div class="title">${title}</div>
            <div class="dates">${subtitle ? subtitle + ' · ' : ''}${dateRange ? dateRange + ' · ' : ''}Generated ${new Date().toLocaleDateString('en-PK')}</div>
          </div>
        </div>

        ${summaryBoxes && summaryBoxes.length > 0 ? `<div class="summary-grid">${summaryHtml}</div>` : ''}

        <table>
          <thead><tr>${tableHead}</tr></thead>
          <tbody>${tableRows}</tbody>
        </table>

        <div class="signatures">
          <div class="sig-box">Prepared By (Signature / Date)</div>
          <div class="sig-box">Verified &amp; Approved By</div>
        </div>

        <script>
          window.onload = function() { window.print(); };
        </script>
      </body>
    </html>
  `;

  win.document.open();
  win.document.write(html);
  win.document.close();
}

// --- PDF GENERATION VIA JSPDF ---
export function generatePdf({ title, subtitle = '', dateRange = '', headers, rows, summaryBoxes = [], filename = 'report.pdf' }) {
  if (!rows || rows.length === 0) {
    alert('No data to export to PDF.');
    return;
  }

  const doc = new jsPDF({
    orientation: rows[0] && rows[0].length > 5 ? 'landscape' : 'portrait',
    unit: 'pt',
    format: 'a4'
  });

  // Header
  doc.setFontSize(16);
  doc.setTextColor(14, 124, 134); // Teal
  doc.text('ELITE WASH', 40, 40);

  doc.setFontSize(9);
  doc.setTextColor(107, 114, 128);
  doc.text('Surf Stock & Ledger Control System', 40, 52);

  doc.setFontSize(14);
  doc.setTextColor(17, 24, 39);
  doc.text(title, doc.internal.pageSize.getWidth() - 40, 40, { align: 'right' });

  doc.setFontSize(9);
  doc.setTextColor(107, 114, 128);
  const metaText = `${subtitle ? subtitle + ' | ' : ''}${dateRange ? dateRange + ' | ' : ''}Generated: ${new Date().toLocaleDateString('en-PK')}`;
  doc.text(metaText, doc.internal.pageSize.getWidth() - 40, 52, { align: 'right' });

  // Divider
  doc.setDrawColor(14, 124, 134);
  doc.setLineWidth(1.5);
  doc.line(40, 60, doc.internal.pageSize.getWidth() - 40, 60);

  let startY = 75;

  // Summary boxes
  if (summaryBoxes && summaryBoxes.length > 0) {
    const boxWidth = (doc.internal.pageSize.getWidth() - 80 - ((summaryBoxes.length - 1) * 10)) / summaryBoxes.length;
    summaryBoxes.forEach((b, idx) => {
      const x = 40 + idx * (boxWidth + 10);
      doc.setFillColor(245, 243, 237);
      doc.roundedRect(x, startY, boxWidth, 36, 4, 4, 'F');
      doc.setFontSize(8);
      doc.setTextColor(107, 114, 128);
      doc.text(b.label.toUpperCase(), x + 8, startY + 14);
      doc.setFontSize(11);
      doc.setTextColor(17, 24, 39);
      doc.text(String(b.value), x + 8, startY + 28);
    });
    startY += 48;
  }

  // AutoTable
  autoTable(doc, {
    startY,
    head: [headers],
    body: rows,
    theme: 'grid',
    headStyles: {
      fillColor: [14, 124, 134],
      textColor: [255, 255, 255],
      fontSize: 9,
      fontStyle: 'bold'
    },
    styles: {
      fontSize: 8.5,
      cellPadding: 5,
      textColor: [31, 41, 55]
    },
    alternateRowStyles: {
      fillColor: [249, 250, 251]
    },
    margin: { left: 40, right: 40, bottom: 60 }
  });

  // Footer signatures
  const pageHeight = doc.internal.pageSize.getHeight();
  doc.setDrawColor(156, 163, 175);
  doc.setLineWidth(0.5);
  doc.line(60, pageHeight - 45, 220, pageHeight - 45);
  doc.line(doc.internal.pageSize.getWidth() - 220, pageHeight - 45, doc.internal.pageSize.getWidth() - 60, pageHeight - 45);

  doc.setFontSize(8);
  doc.setTextColor(107, 114, 128);
  doc.text('Prepared By (Signature / Date)', 140, pageHeight - 34, { align: 'center' });
  doc.text('Authorized Signatory', doc.internal.pageSize.getWidth() - 140, pageHeight - 34, { align: 'center' });

  doc.save(filename.endsWith('.pdf') ? filename : `${filename}.pdf`);
}

// --- PAKISTANI PHONE FORMATTING FOR WHATSAPP ---
export function formatPakistaniPhoneForWhatsApp(phone) {
  if (!phone) return null;
  let digits = String(phone).replace(/\D/g, '');
  if (!digits) return null;

  if (digits.startsWith('0092')) digits = digits.slice(4);
  else if (digits.startsWith('92')) digits = digits.slice(2);
  else if (digits.startsWith('0')) digits = digits.slice(1);

  if (digits.length === 10) return '92' + digits;

  const rawDigits = String(phone).replace(/\D/g, '');
  if (rawDigits.length === 12 && rawDigits.startsWith('92')) return rawDigits;
  if (rawDigits.length === 11 && rawDigits.startsWith('03')) return '92' + rawDigits.slice(1);
  if (rawDigits.length === 10 && rawDigits.startsWith('3')) return '92' + rawDigits;

  return null;
}

// --- WHATSAPP SHARE ---
export function shareOnWhatsApp({ title, lines = [], phone = '' }) {
  const formattedPhone = formatPakistaniPhoneForWhatsApp(phone);
  const header = `*ELITE WASHWO — ${title.toUpperCase()}*\nDate: ${new Date().toLocaleDateString('en-PK')}\n`;
  const body = lines.filter(Boolean).join('\n');
  const footer = `\n_Generated via Elite Wash ERP_`;
  const fullMessage = `${header}\n${body}${footer}`;

  const encoded = encodeURIComponent(fullMessage);
  const url = formattedPhone
    ? `https://wa.me/${formattedPhone}?text=${encoded}`
    : `https://wa.me/?text=${encoded}`;

  window.open(url, '_blank');
}


// --- EMBEDDED OFFICIAL BILL PAD ASSETS ---
import { RECEIPT_TEMPLATE_BASE64, CEO_SIGNATURE_BASE64 } from './receiptAssets.js';

// --- BOOKING PAD (OFFICIAL ELITEWASH DETERGENT BILL PAD) HTML TEMPLATE ---
export function getBookingPadHtml(booking, options = {}) {
  const { isForPdf = false } = options;
  const receiptUrl = (typeof window !== 'undefined' && window.location?.origin ? window.location.origin : '') + "/receipt.jpeg";
  const signatureUrl = (typeof window !== 'undefined' && window.location?.origin ? window.location.origin : '') + "/ceo-signature.png";

  const refNo = booking.reference_number || booking.ref || "";
  const dateStr = booking.sale_date ? new Date(booking.sale_date).toLocaleDateString("en-PK") : new Date().toLocaleDateString("en-PK");
  const distName = booking.distributors?.name || booking.distributorName || booking.customerName || "—";
  
  const rawItems = booking.items || (booking.sale_items || []).map(i => ({
    description: i.product_packaging?.name ? `Elite Wash Surf (${i.product_packaging.name})` : (i.description || i.name || "Elite Wash Surf"),
    quantity: i.quantity,
    price: i.unit_price,
    amount: (i.quantity || 0) * (i.unit_price || 0)
  }));

  const total = booking.total_amount || booking.totalAmount || 0;

  // Exact coordinates matching the official 668 x 1024 px ELITEWASH DETERGENT bill pad template:
  const ROW_START_PCT = 36.5;
  const ROW_HEIGHT_PCT = 3.65;
  const MAX_ROWS = 13;

  let rowsHtml = "";
  for (let i = 0; i < MAX_ROWS; i++) {
    const item   = rawItems[i];
    const top    = ROW_START_PCT + (i * ROW_HEIGHT_PCT);
    const srNo   = item ? (i + 1) : "";
    const desc   = item ? (item.description || item.name || "") : "";
    const qty    = item ? (item.quantity ?? item.qty ?? "") : "";
    const price  = item ? (item.unit_price ?? item.price ?? "") : "";
    const amount = item ? (item.amount ?? ((Number(qty) || 0) * (Number(price) || 0))) : "";

    rowsHtml += `
      <div style="position:absolute; top:${top}%; left:4.6%; width:9.3%; height:3.4%; font-size:12px; font-weight:700; display:flex; align-items:center; justify-content:center; color:#111;">${srNo}</div>
      <div style="position:absolute; top:${top}%; left:14.5%; width:36.0%; height:3.4%; font-size:12px; font-weight:600; display:flex; align-items:center; padding-left:6px; color:#111; overflow:hidden; white-space:nowrap; text-overflow:ellipsis;">${desc}</div>
      <div style="position:absolute; top:${top}%; left:51.5%; width:8.5%; height:3.4%; font-size:12px; font-weight:700; display:flex; align-items:center; justify-content:center; color:#111;">${qty !== '' ? Number(qty).toLocaleString('en-PK') : ''}</div>
      <div style="position:absolute; top:${top}%; left:60.5%; width:12.0%; height:3.4%; font-size:12px; font-weight:600; display:flex; align-items:center; justify-content:flex-end; padding-right:8px; color:#111;">${price !== '' ? Number(price).toLocaleString('en-PK') : ''}</div>
      <div style="position:absolute; top:${top}%; left:73.5%; width:21.5%; height:3.4%; font-size:12px; font-weight:700; display:flex; align-items:center; justify-content:flex-end; padding-right:12px; color:#111;">${amount !== '' ? Number(amount).toLocaleString('en-PK') : ''}</div>
    `;
  }

  const containerStyle = isForPdf
    ? `position:relative; width:100%; aspect-ratio:668/1024; background:#ffffff; margin:0; padding:0; overflow:hidden; box-sizing:border-box; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Space Grotesk", sans-serif;`
    : `position:relative; width:100%; max-width:668px; aspect-ratio:668/1024; margin:0 auto; background:#ffffff; overflow:hidden; box-sizing:border-box; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Space Grotesk", sans-serif;`;

  const bodyContent = `
    <div class="receipt-wrapper" style="position:relative; width:100%; height:100%; aspect-ratio:668/1024;">
      <img src="${receiptUrl}" alt="Elite Wash Official Bill Pad" style="width:100%; height:100%; display:block; object-fit:fill;" />
      <div class="overlay" style="position:absolute; top:0; left:0; width:100%; height:100%; pointer-events:none;">
        <!-- Bill No. -->
        <div style="position:absolute; top:24.3%; left:16.5%; font-size:13px; font-weight:700; color:#111827; letter-spacing:0.02em;">${refNo}</div>
        
        <!-- Date -->
        <div style="position:absolute; top:24.3%; left:77.5%; font-size:13px; font-weight:700; color:#111827;">${dateStr}</div>
        
        <!-- M/s Distributor Name -->
        <div style="position:absolute; top:29.2%; left:12.0%; width:82%; font-size:13.5px; font-weight:700; color:#111827; overflow:hidden; white-space:nowrap; text-overflow:ellipsis;">${distName}</div>
        
        <!-- Dynamic Line Items -->
        ${rowsHtml}
        
        <!-- Grand Total -->
        <div style="position:absolute; top:83.0%; left:73.5%; width:21.5%; height:3.4%; font-size:14px; font-weight:800; display:flex; align-items:center; justify-content:flex-end; padding-right:12px; color:#111827;">${Number(total).toLocaleString('en-PK')}</div>
        
        <!-- Authentic Handwritten CEO Signature above Chief Executive Officer line -->
        <img src="${signatureUrl}" alt="CEO Signature" class="ceo-sig-img" style="position:absolute; left:74.0%; top:84.8%; width:16.0%; max-height:8.5%; object-fit:contain;" />
      </div>
    </div>
  `;

  if (isForPdf) {
    return `<div style="${containerStyle}">${bodyContent}</div>`;
  }

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Official Bill Pad - ${refNo}</title>
  <style>
    @page {
      size: portrait;
      margin: 0;
    }
    *, *::before, *::after {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    html, body {
      width: 100%;
      height: 100%;
      margin: 0;
      padding: 0;
      background: #ffffff;
      overflow: hidden;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Space Grotesk", sans-serif;
    }
    body {
      display: flex;
      justify-content: center;
      align-items: flex-start;
    }
    .receipt-wrapper {
      position: relative;
      width: 100%;
      height: 100vh;
      max-height: 100vh;
      aspect-ratio: 668 / 1024;
      background: #ffffff;
      margin: 0 auto;
      page-break-inside: avoid;
      break-inside: avoid;
    }
    .receipt-wrapper img {
      width: 100%;
      height: 100%;
      display: block;
      object-fit: fill;
    }
    @media screen {
      body {
        background: #f3f4f6;
        padding: 10px 0;
      }
      .receipt-wrapper {
        box-shadow: 0 4px 20px rgba(0,0,0,0.12);
        max-width: 668px;
        height: auto;
      }
    }
    @media print {
      html, body {
        width: 100%;
        height: 100%;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
      }
      .receipt-wrapper {
        box-shadow: none !important;
        margin: 0 auto !important;
        height: 100vh !important;
        max-height: 100vh !important;
        page-break-after: avoid !important;
        break-after: avoid !important;
      }
    }
  </style>
</head>
<body>
  ${bodyContent}
  <script>
    window.onload = function() {
      setTimeout(function() { window.print(); }, 400);
    };
  </script>
</body>
</html>`;
}

// --- BOOKING PAD (PRINT WINDOW) ---
export function printBookingPad(booking) {
  const win = window.open("", "_blank");
  if (!win) {
    alert("Please allow popups to print official bill pad.");
    return;
  }
  const html = getBookingPadHtml(booking, { isForPdf: false });
  win.document.open();
  win.document.write(html);
  win.document.close();
}

// --- DIRECT JSPDF RENDERER FOR OFFICIAL BILL PAD TEMPLATE ---
export function renderBookingPadToJsPdf(doc, booking) {
  const refNo = booking.reference_number || booking.ref || "BKG-ORDER";
  const dateStr = booking.sale_date ? new Date(booking.sale_date).toLocaleDateString("en-PK") : new Date().toLocaleDateString("en-PK");
  const distName = booking.distributors?.name || booking.distributorName || booking.customerName || "—";
  
  const rawItems = booking.items || (booking.sale_items || []).map(i => ({
    description: i.product_packaging?.name ? `Elite Wash Surf (${i.product_packaging.name})` : (i.description || i.name || "Elite Wash Surf"),
    quantity: i.quantity,
    price: i.unit_price,
    amount: (i.quantity || 0) * (i.unit_price || 0)
  }));

  const total = booking.total_amount || booking.totalAmount || 0;

  const pdfWidth = doc.internal.pageSize.getWidth();
  const pdfHeight = doc.internal.pageSize.getHeight();

  // 1. Draw the official ELITEWASH DETERGENT bill pad template background
  try {
    doc.addImage(RECEIPT_TEMPLATE_BASE64, 'JPEG', 0, 0, pdfWidth, pdfHeight);
  } catch (err) {
    console.warn('Failed to embed background receipt image in jsPDF:', err);
  }

  // 2. Overlay dynamic text fields with exact coordinates
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9.5);
  doc.setTextColor(20, 20, 20);

  // Bill No. (left: 16.5%, y: 25.5%)
  doc.text(String(refNo), pdfWidth * 0.165, pdfHeight * 0.255);

  // Date (left: 77.5%, y: 25.5%)
  doc.text(String(dateStr), pdfWidth * 0.775, pdfHeight * 0.255);

  // M/s Distributor (left: 12.0%, y: 0.304)
  doc.setFontSize(10);
  doc.text(String(distName), pdfWidth * 0.120, pdfHeight * 0.304);

  // Item Table Rows
  const ROW_START_Y = pdfHeight * 0.380;
  const ROW_STEP_Y = pdfHeight * 0.0365;
  const MAX_ROWS = 13;

  for (let i = 0; i < Math.min(rawItems.length, MAX_ROWS); i++) {
    const item = rawItems[i];
    const y = ROW_START_Y + (i * ROW_STEP_Y);

    const srNo = String(i + 1);
    const desc = String(item.description || item.name || "");
    const qty = item.quantity !== undefined && item.quantity !== null && item.quantity !== ''
      ? Number(item.quantity).toLocaleString('en-PK')
      : '';
    const price = item.price !== undefined && item.price !== null && item.price !== ''
      ? Number(item.price).toLocaleString('en-PK')
      : (item.unit_price !== undefined ? Number(item.unit_price).toLocaleString('en-PK') : '');
    const amt = item.amount !== undefined && item.amount !== null && item.amount !== ''
      ? Number(item.amount).toLocaleString('en-PK')
      : (qty && price ? Number(Number(item.quantity) * Number(item.unit_price || item.price)).toLocaleString('en-PK') : '');

    // Sr No (center around 9.25%)
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(9);
    doc.text(srNo, pdfWidth * 0.0925, y, { align: 'center' });

    // Description (left at 14.8%)
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8.5);
    const truncatedDesc = desc.length > 34 ? desc.substring(0, 32) + '...' : desc;
    doc.text(truncatedDesc, pdfWidth * 0.148, y);

    // Qty (center at 55.75%)
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(9);
    if (qty) doc.text(qty, pdfWidth * 0.5575, y, { align: 'center' });

    // Price (right at 71.5%)
    doc.setFont('helvetica', 'normal');
    if (price) doc.text(price, pdfWidth * 0.715, y, { align: 'right' });

    // Amount (right at 94.0%)
    doc.setFont('helvetica', 'bold');
    if (amt) doc.text(amt, pdfWidth * 0.940, y, { align: 'right' });
  }

  // Grand Total (right at 94.0%, y: 84.8%)
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10.5);
  doc.text(Number(total).toLocaleString('en-PK'), pdfWidth * 0.940, pdfHeight * 0.848, { align: 'right' });

  // 3. Place Authentic Handwritten CEO Signature above Chief Executive Officer line
  try {
    const sigX = pdfWidth * 0.740;
    const sigY = pdfHeight * 0.850;
    const sigW = pdfWidth * 0.160;
    const sigH = pdfHeight * 0.075;
    doc.addImage(CEO_SIGNATURE_BASE64, 'PNG', sigX, sigY, sigW, sigH);
  } catch (sigErr) {
    console.warn('Failed to embed CEO signature image in jsPDF:', sigErr);
  }

  return doc;
}

// --- COMPLETE SIGNED PDF GENERATOR FOR OFFICIAL BILL PAD ---
export async function generateBookingPadPdf(booking, distributor = null) {
  const bookingWithDist = {
    ...booking,
    distributors: booking.distributors || distributor || null
  };
  const refNo = bookingWithDist.reference_number || bookingWithDist.ref || "BOOKING";
  const filename = `${refNo}.pdf`;

  // Custom PDF dimensions matching exactly 668 x 1024 px bill pad aspect ratio
  // 595.28 pt width (A4 width) -> 912.48 pt height (1024 / 668 * 595.28)
  const padWidthPt = 595.28;
  const padHeightPt = (1024 / 668) * 595.28;

  // Server / headless environment fallback (for automated unit tests)
  if (typeof document === 'undefined' || typeof window === 'undefined') {
    const doc = new jsPDF({
      orientation: 'portrait',
      unit: 'pt',
      format: [padWidthPt, padHeightPt]
    });
    renderBookingPadToJsPdf(doc, bookingWithDist);
    const arrayBuffer = doc.output('arraybuffer');
    const blob = typeof Blob !== 'undefined' ? new Blob([arrayBuffer], { type: 'application/pdf' }) : null;
    const file = (typeof File !== 'undefined' && blob) ? new File([blob], filename, { type: 'application/pdf' }) : null;
    return { doc, blob, file, filename };
  }

  // Browser rendering with html2canvas for 100% pixel-perfect receipt preservation
  const container = document.createElement('div');
  container.style.position = 'fixed';
  container.style.left = '-9999px';
  container.style.top = '0';
  container.style.width = '668px';
  container.style.height = '1024px';
  container.style.background = '#ffffff';
  container.style.boxSizing = 'border-box';
  container.style.zIndex = '-9999';

  container.innerHTML = getBookingPadHtml(bookingWithDist, { isForPdf: true });
  document.body.appendChild(container);

  try {
    if (typeof container.querySelectorAll === 'function') {
      const images = container.querySelectorAll('img');
      await Promise.all(Array.from(images).map(img => {
        if (img.complete) return Promise.resolve();
        return new Promise(resolve => {
          img.onload = resolve;
          img.onerror = resolve;
        });
      }));
    }

    const canvas = await html2canvas(container, {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: '#ffffff'
    });

    const doc = new jsPDF({
      orientation: 'portrait',
      unit: 'pt',
      format: [padWidthPt, padHeightPt]
    });

    const imgData = canvas.toDataURL('image/jpeg', 0.95);
    doc.addImage(imgData, 'JPEG', 0, 0, padWidthPt, padHeightPt);

    const blob = doc.output('blob');
    const file = typeof File !== 'undefined' ? new File([blob], filename, { type: 'application/pdf' }) : null;

    return { doc, blob, file, filename };
  } catch (err) {
    console.warn('html2canvas render failed, falling back to direct jsPDF engine:', err);
    const doc = new jsPDF({
      orientation: 'portrait',
      unit: 'pt',
      format: [padWidthPt, padHeightPt]
    });
    renderBookingPadToJsPdf(doc, bookingWithDist);
    const blob = doc.output('blob');
    const file = typeof File !== 'undefined' ? new File([blob], filename, { type: 'application/pdf' }) : null;
    return { doc, blob, file, filename };
  } finally {
    if (container.parentNode) {
      document.body.removeChild(container);
    }
  }
}

// --- SHARE BOOKING PDF ON WHATSAPP WORKFLOW ---
export async function shareBookingPadOnWhatsApp({
  booking,
  distributor = null,
  targetWindow = null,
  onProgress = () => {},
  onSuccess = () => {},
  onError = () => {}
}) {
  try {
    const dist = (Array.isArray(booking.distributors) ? booking.distributors[0] : booking.distributors)
      || distributor
      || null;

    if (!dist) {
      if (targetWindow && !targetWindow.closed) {
        try { targetWindow.close(); } catch (_) {}
      }
      const msg = 'Cannot share receipt: No distributor is linked to this booking.';
      onError(msg);
      return { success: false, reason: 'missing_distributor', message: msg };
    }

    const formattedPhone = formatPakistaniPhoneForWhatsApp(dist.phone);
    if (!formattedPhone) {
      if (targetWindow && !targetWindow.closed) {
        try { targetWindow.close(); } catch (_) {}
      }
      const msg = `Cannot share receipt: Distributor ${dist.name || ''} has no valid registered phone number.`;
      onError(msg);
      return { success: false, reason: 'invalid_phone', message: msg };
    }

    const refNo = booking.reference_number || booking.ref || 'BOOKING';
    const filename = `${refNo}.pdf`;

    // Direct distributor WhatsApp chat URL with NO text message parameter
    const waUrl = `https://wa.me/${formattedPhone}`;

    // If a tab was pre-opened in the click handler, navigate it immediately to WhatsApp
    if (targetWindow && !targetWindow.closed) {
      try {
        targetWindow.location.href = waUrl;
      } catch (navErr) {
        console.warn('Could not navigate pre-opened tab:', navErr);
      }
    }

    onProgress('Generating official signed PDF receipt...');

    // Generate the complete signed PDF
    const { blob, file } = await generateBookingPadPdf(booking, dist);

    // 1. Native File Sharing (e.g. mobile devices, Web Share API Level 2)
    // Only share the signed PDF document without any separate text summary message
    if (typeof navigator !== 'undefined' && navigator.canShare && file) {
      const shareData = {
        files: [file],
        title: `Booking Receipt - ${refNo}`
      };
      if (navigator.canShare(shareData)) {
        try {
          await navigator.share(shareData);
          if (targetWindow && !targetWindow.closed) {
            try { targetWindow.close(); } catch (_) {}
          }
          const successMsg = `Booking receipt PDF shared successfully with ${dist.name}.`;
          onSuccess(successMsg, { mode: 'native_share', filename, phone: formattedPhone });
          return { success: true, mode: 'native_share', filename, phone: formattedPhone };
        } catch (shareErr) {
          if (shareErr.name === 'AbortError') {
            if (targetWindow && !targetWindow.closed) {
              try { targetWindow.close(); } catch (_) {}
            }
            return { success: false, reason: 'cancelled', message: 'Share cancelled.' };
          }
          console.warn('Native file share failed, falling back to download + WhatsApp chat link:', shareErr);
        }
      }
    }

    // 2. Fallback: Download the PDF and ensure WhatsApp chat tab is opened
    if (typeof document !== 'undefined' && blob) {
      const downloadUrl = URL.createObjectURL(blob);
      const downloadLink = document.createElement('a');
      downloadLink.href = downloadUrl;
      downloadLink.download = filename;
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
      setTimeout(() => {
        if (typeof URL !== 'undefined' && typeof URL.revokeObjectURL === 'function') {
          URL.revokeObjectURL(downloadUrl);
        }
      }, 3000);
    }

    // If no tab was passed or pre-opened tab was blocked/closed, attempt window.open
    let popupBlocked = false;
    if (!targetWindow || targetWindow.closed) {
      if (typeof window !== 'undefined') {
        const opened = window.open(waUrl, '_blank');
        if (!opened || opened.closed || typeof opened.closed === 'undefined') {
          popupBlocked = true;
        }
      }
    }

    const fallbackMsg = popupBlocked
      ? `Signed PDF receipt downloaded (${filename}). Please click "Open WhatsApp Chat" below to chat with ${dist.name}.`
      : `Signed PDF receipt downloaded (${filename}). WhatsApp chat opened with ${dist.name}. Please attach the downloaded PDF in WhatsApp.`;

    onSuccess(fallbackMsg, {
      mode: 'download_and_chat',
      filename,
      phone: formattedPhone,
      waUrl,
      distName: dist.name,
      popupBlocked,
      instructions: `The PDF document '${filename}' has been downloaded to your computer. In the opened WhatsApp tab, click the attachment icon (📎) → Document and select '${filename}'.`
    });

    return {
      success: true,
      mode: 'download_and_chat',
      filename,
      phone: formattedPhone,
      waUrl,
      distName: dist.name,
      popupBlocked,
      message: fallbackMsg,
      instructions: `The PDF document '${filename}' has been downloaded to your computer. In the opened WhatsApp tab, click the attachment icon (📎) → Document and select '${filename}'.`
    };
  } catch (err) {
    console.error('Error in shareBookingPadOnWhatsApp:', err);
    const errMsg = `Failed to generate or share booking PDF: ${err.message}`;
    onError(errMsg);
    return { success: false, reason: 'error', message: errMsg };
  }
}

// --- DISTRIBUTOR PAD (OFFICIAL PRINTED BILL OVERLAY) ---
export function printDistributorPad(sale) {
  const win = window.open("", "_blank");
  if (!win) {
    alert("Please allow popups to print delivery receipts.");
    return;
  }

  const receiptUrl = window.location.origin + "/receipt.jpeg";
  const signatureUrl = window.location.origin + "/ceo-signature.png";

  const billNo       = sale.billNo || sale.reference_number || "";
  const saleDate     = sale.date || (sale.sale_date ? new Date(sale.sale_date).toLocaleDateString("en-PK") : new Date().toLocaleDateString("en-PK"));
  const distributor  = sale.distributorName || sale.customerName || sale.distributors?.name || "—";
  const rawItems     = sale.items || (sale.sale_items || []).map(i => ({
    description: i.product_packaging?.name ? `Elite Wash Surf (${i.product_packaging.name})` : (i.description || i.name || "Elite Wash Surf"),
    quantity: i.quantity,
    price: i.unit_price,
    amount: (i.quantity || 0) * (i.unit_price || 0)
  }));
  const total        = sale.totalAmount || sale.total_amount || 0;

  const ROW_START_PCT = 36.5;
  const ROW_HEIGHT_PCT = 3.65;
  const MAX_ROWS = 13;

  let rowsHtml = "";
  for (let i = 0; i < MAX_ROWS; i++) {
    const item   = rawItems[i];
    const top    = ROW_START_PCT + (i * ROW_HEIGHT_PCT);
    const srNo   = item ? (i + 1) : "";
    const desc   = item ? (item.description || item.name || "") : "";
    const qty    = item ? (item.quantity ?? item.qty ?? "") : "";
    const price  = item ? (item.unit_price ?? item.price ?? "") : "";
    const amount = item ? (item.amount ?? ((Number(qty) || 0) * (Number(price) || 0))) : "";

    rowsHtml += `
      <div style="position:absolute; top:${top}%; left:4.6%; width:9.3%; height:3.4%; font-size:12px; font-weight:700; display:flex; align-items:center; justify-content:center; color:#111;">${srNo}</div>
      <div style="position:absolute; top:${top}%; left:14.5%; width:36.0%; height:3.4%; font-size:12px; font-weight:600; display:flex; align-items:center; padding-left:6px; color:#111; overflow:hidden; white-space:nowrap; text-overflow:ellipsis;">${desc}</div>
      <div style="position:absolute; top:${top}%; left:51.5%; width:8.5%; height:3.4%; font-size:12px; font-weight:700; display:flex; align-items:center; justify-content:center; color:#111;">${qty !== '' ? Number(qty).toLocaleString('en-PK') : ''}</div>
      <div style="position:absolute; top:${top}%; left:60.5%; width:12.0%; height:3.4%; font-size:12px; font-weight:600; display:flex; align-items:center; justify-content:flex-end; padding-right:8px; color:#111;">${price !== '' ? Number(price).toLocaleString('en-PK') : ''}</div>
      <div style="position:absolute; top:${top}%; left:73.5%; width:21.5%; height:3.4%; font-size:12px; font-weight:700; display:flex; align-items:center; justify-content:flex-end; padding-right:12px; color:#111;">${amount !== '' ? Number(amount).toLocaleString('en-PK') : ''}</div>
    `;
  }

  const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Distributor Bill - ${billNo}</title>
  <style>
    @page {
      size: portrait;
      margin: 0;
    }
    *, *::before, *::after {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    html, body {
      width: 100%;
      height: 100%;
      margin: 0;
      padding: 0;
      background: #ffffff;
      overflow: hidden;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Space Grotesk", sans-serif;
    }
    body {
      display: flex;
      justify-content: center;
      align-items: flex-start;
    }
    .receipt-wrapper {
      position: relative;
      width: 100%;
      height: 100vh;
      max-height: 100vh;
      aspect-ratio: 668 / 1024;
      background: #ffffff;
      margin: 0 auto;
      page-break-inside: avoid;
      break-inside: avoid;
    }
    .receipt-wrapper img {
      width: 100%;
      height: 100%;
      display: block;
      object-fit: fill;
    }
    @media screen {
      body {
        background: #f3f4f6;
        padding: 10px 0;
      }
      .receipt-wrapper {
        box-shadow: 0 4px 20px rgba(0,0,0,0.12);
        max-width: 668px;
        height: auto;
      }
    }
    @media print {
      html, body {
        width: 100%;
        height: 100%;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
      }
      .receipt-wrapper {
        box-shadow: none !important;
        margin: 0 auto !important;
        height: 100vh !important;
        max-height: 100vh !important;
        page-break-after: avoid !important;
        break-after: avoid !important;
      }
    }
  </style>
</head>
<body>
  <div class="receipt-wrapper">
    <img src="${receiptUrl}" alt="Official Bill Pad" />
    <div class="overlay" style="position:absolute; top:0; left:0; width:100%; height:100%; pointer-events:none;">
      <!-- Bill No. -->
      <div style="position:absolute; top:24.3%; left:16.5%; font-size:13px; font-weight:700; color:#111827; letter-spacing:0.02em;">${billNo}</div>
      <!-- Date -->
      <div style="position:absolute; top:24.3%; left:77.5%; font-size:13px; font-weight:700; color:#111827;">${saleDate}</div>
      <!-- M/s Distributor -->
      <div style="position:absolute; top:29.2%; left:12.0%; width:82%; font-size:13.5px; font-weight:700; color:#111827; overflow:hidden; white-space:nowrap; text-overflow:ellipsis;">${distributor}</div>

      <!-- Item rows -->
      ${rowsHtml}

      <!-- Total value -->
      <div style="position:absolute; top:83.0%; left:73.5%; width:21.5%; height:3.4%; font-size:14px; font-weight:800; display:flex; align-items:center; justify-content:flex-end; padding-right:12px; color:#111827;">${Number(total).toLocaleString('en-PK')}</div>

      <!-- Authentic Handwritten CEO Signature above Chief Executive Officer line -->
      <img src="${signatureUrl}" alt="CEO Signature" style="position:absolute; left:74.0%; top:84.8%; width:16.0%; max-height:8.5%; object-fit:contain;" />
    </div>
  </div>
  <script>
    window.onload = function() { setTimeout(function() { window.print(); }, 400); };
  </script>
</body>
</html>`;

  win.document.open();
  win.document.write(html);
  win.document.close();
}

// Backward-compatible alias
export const printSaleReceipt = printDistributorPad;

// --- SETTLEMENT VOUCHER (COMMISSION SETTLEMENT RECEIPT) ---
export function printSettlementVoucher(settlement, distributor) {
  const win = window.open("", "_blank");
  if (!win) {
    alert("Please allow popups to print settlement vouchers.");
    return;
  }

  const logoUrl = window.location.origin + "/elitewash-logo.jpg";
  const refNo = settlement.id ? `SET-${String(settlement.id).substring(0, 8).toUpperCase()}` : "SET-NEW";
  const dateStr = settlement.settlement_date ? new Date(settlement.settlement_date).toLocaleDateString("en-PK") : new Date().toLocaleDateString("en-PK");
  const distName = distributor?.name || "—";
  const distCode = distributor?.code || "—";
  const distPhone = distributor?.phone || "—";
  const distCnic = distributor?.cnic || "—";
  const amount = Number(settlement.amount || 0);
  const typeLabel = settlement.settlement_type === 'Commission_Against_Outstanding' 
    ? 'Offset Against Sales Outstanding' 
    : settlement.settlement_type === 'Commission_Bank_Paid' 
    ? 'Bank Commission Paid' 
    : 'Cash Commission Paid';
  const paymentMethod = settlement.payment_method || (settlement.settlement_type === 'Commission_Cash_Paid' ? 'Cash' : settlement.settlement_type === 'Commission_Bank_Paid' ? 'Bank' : 'Adjustment');
  const status = settlement.status || 'Pending';
  const notes = settlement.notes || '—';

  const html = `<!DOCTYPE html>
<html>
<head>
  <title>Commission Settlement Voucher - ${refNo}</title>
  <style>
    * { margin:0; padding:0; box-sizing:border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #111827; padding: 30px; max-width: 800px; margin: 0 auto; }
    .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0e7c86; padding-bottom: 16px; margin-bottom: 20px; }
    .logo-box { display: flex; align-items: center; gap: 14px; }
    .logo-img { height: 50px; width: auto; object-fit: contain; }
    .company-name { font-size: 20px; font-weight: 700; color: #0e7c86; }
    .company-sub { font-size: 11px; color: #6b7280; }
    .voucher-title { font-size: 16px; font-weight: 700; text-align: right; color: #111827; }
    .voucher-sub { font-size: 12px; color: #6b7280; text-align: right; }
    .meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin-bottom: 24px; }
    .meta-item { font-size: 12.5px; }
    .meta-label { font-size: 11px; text-transform: uppercase; color: #6b7280; font-weight: 600; margin-bottom: 2px; }
    .meta-val { font-weight: 600; color: #111827; }
    .amount-box { background: #f0fdfa; border: 1.5px solid #0e7c86; border-radius: 8px; padding: 18px; text-align: center; margin-bottom: 24px; }
    .amount-label { font-size: 12px; text-transform: uppercase; color: #0e7c86; font-weight: 700; letter-spacing: 0.05em; }
    .amount-val { font-size: 28px; font-weight: 800; color: #0e7c86; margin: 4px 0; }
    .badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
    .badge-Approved { background: #dcfce7; color: #15803d; }
    .badge-Pending { background: #fef3c7; color: #b45309; }
    .badge-Cancelled { background: #fee2e2; color: #b91c1c; }
    .details-table { width: 100%; border-collapse: collapse; margin-bottom: 30px; font-size: 13px; }
    .details-table td { padding: 10px 12px; border-bottom: 1px solid #e5e7eb; }
    .details-table td:first-child { width: 35%; color: #4b5563; font-weight: 500; }
    .details-table td:last-child { font-weight: 600; color: #111827; }
    .sig-section { display: flex; justify-content: space-between; margin-top: 60px; padding-top: 20px; }
    .sig-line { width: 200px; border-top: 1px solid #9ca3af; text-align: center; font-size: 11px; color: #4b5563; padding-top: 6px; }
    @media print { body { padding: 10mm; } }
  </style>
</head>
<body>
  <div class="header">
    <div class="logo-box">
      <img src="${logoUrl}" alt="Elite Wash" class="logo-img" onerror="this.style.display='none'" />
      <div>
        <div class="company-name">ELITE WASH</div>
        <div class="company-sub">Surf Stock &amp; Ledger Control System</div>
      </div>
    </div>
    <div>
      <div class="voucher-title">COMMISSION SETTLEMENT VOUCHER</div>
      <div class="voucher-sub">Ref: ${refNo} &nbsp;|&nbsp; Date: ${dateStr}</div>
    </div>
  </div>

  <div class="meta-grid">
    <div class="meta-item">
      <div class="meta-label">Distributor Name &amp; Code</div>
      <div class="meta-val">${distName} (${distCode})</div>
    </div>
    <div class="meta-item">
      <div class="meta-label">Phone &amp; CNIC</div>
      <div class="meta-val">${distPhone} ${distCnic ? '· ' + distCnic : ''}</div>
    </div>
    <div class="meta-item">
      <div class="meta-label">Settlement Mode</div>
      <div class="meta-val">${typeLabel}</div>
    </div>
    <div class="meta-item">
      <div class="meta-label">Approval Status</div>
      <div><span class="badge badge-${status}">${status}</span></div>
    </div>
  </div>

  <div class="amount-box">
    <div class="amount-label">Settlement Amount</div>
    <div class="amount-val">Rs. ${amount.toLocaleString('en-PK')}</div>
    <div style="font-size:12px;color:#4b5563;">Method: ${paymentMethod}</div>
  </div>

  <table class="details-table">
    <tr>
      <td>Settlement Type</td>
      <td>${typeLabel}</td>
    </tr>
    <tr>
      <td>Payment Channel / Instrument</td>
      <td>${paymentMethod}</td>
    </tr>
    <tr>
      <td>Notes / Description</td>
      <td>${notes}</td>
    </tr>
    <tr>
      <td>System Verification</td>
      <td>Verified against immutable historical sales rates</td>
    </tr>
  </table>

  <div class="sig-section">
    <div class="sig-line">Prepared By (Accounts)</div>
    <div class="sig-line">Distributor Signature</div>
    <div class="sig-line">Manager / Super Admin Approval</div>
  </div>

  <script>
    window.onload = function() { setTimeout(function() { window.print(); }, 500); };
  </script>
</body>
</html>`;

  win.document.open();
  win.document.write(html);
  win.document.close();
}


