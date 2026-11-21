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
import {
  RECEIPT_WATERMARK_BASE64,
  MANAGER_SIGNATURE_BASE64,
  MANAGER_STAMP_BASE64,
  CEO_SIGNATURE_BASE64,
  CEO_STAMP_BASE64,
  RECEIPT_TEMPLATE_BASE64
} from './receiptAssets.js';

// --- OFFICIAL RED-ORANGE ELITE WASH BILL PAD HTML GENERATOR ---
function generateOfficialReceiptHtml({
  padTitle,
  billNo,
  refNo,
  formattedBillNo,
  dateStr,
  distName,
  distCode = '',
  distPhone = '',
  rawItems = [],
  total = 0,
  isForPdf = false
}) {
  const origin = (typeof window !== 'undefined' && window.location?.origin) ? window.location.origin : '';
  const watermarkUrl = origin ? `${origin}/assets/receipt/receipt-watermark-red.png` : RECEIPT_WATERMARK_BASE64;
  const managerSigUrl = origin ? `${origin}/assets/receipt/manager-signature.png` : MANAGER_SIGNATURE_BASE64;
  const managerStampUrl = origin ? `${origin}/assets/receipt/manager-stamp.png` : MANAGER_STAMP_BASE64;
  const ceoSigUrl = origin ? `${origin}/assets/receipt/ceo-signature.png` : CEO_SIGNATURE_BASE64;
  const ceoStampUrl = origin ? `${origin}/assets/receipt/ceo-stamp.png` : CEO_STAMP_BASE64;

  const MAX_ROWS = 13;
  let rowsHtml = '';
  for (let i = 0; i < MAX_ROWS; i++) {
    const item = rawItems[i];
    const srNo = item ? (i + 1) : '';
    const desc = item ? (item.description || item.name || '') : '';
    const qty = item ? (item.quantity ?? item.qty ?? '') : '';
    const price = item ? (item.unit_price ?? item.price ?? '') : '';
    const amount = item ? (item.amount ?? ((Number(qty) || 0) * (Number(price) || 0))) : '';

    rowsHtml += `
      <tr style="height:36px; border-bottom:1px solid #D83220;">
        <td style="text-align:center; font-weight:700; color:#111827; border-right:1px solid #D83220; padding:2px 4px; font-size:12px;">${srNo}</td>
        <td style="text-align:left; font-weight:700; color:#111827; border-right:1px solid #D83220; padding:2px 10px; font-size:12px; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; max-width:280px;">${desc}</td>
        <td style="text-align:center; font-weight:700; color:#111827; border-right:1px solid #D83220; padding:2px 4px; font-size:12px;">${qty !== '' ? Number(qty).toLocaleString('en-PK') : ''}</td>
        <td style="text-align:right; font-weight:700; color:#111827; border-right:1px solid #D83220; padding:2px 10px; font-size:12px;">${price !== '' ? Number(price).toLocaleString('en-PK') : ''}</td>
        <td style="text-align:right; font-weight:700; color:#111827; padding:2px 12px; font-size:12px;">${amount !== '' ? Number(amount).toLocaleString('en-PK') : ''}</td>
      </tr>
    `;
  }

  const containerStyle = isForPdf
    ? `position:relative; width:792px; height:1024px; max-width:792px; aspect-ratio:792/1024; background:#ffffff; margin:0; padding:32px 38px 24px 38px; overflow:hidden; box-sizing:border-box; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; display:flex; flex-direction:column; justify-content:space-between;`
    : `position:relative; width:100%; max-width:792px; aspect-ratio:792/1024; margin:0 auto; background:#ffffff; padding:32px 38px 24px 38px; overflow:hidden; box-sizing:border-box; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; display:flex; flex-direction:column; justify-content:space-between;`;

  const formattedTitle = padTitle === 'DELIVERY BILL PAD' ? 'D E L I V E R Y &nbsp; B I L L &nbsp; P A D' : 'B O O K I N G &nbsp; P A D';

  const bodyContent = `
    <div class="receipt-wrapper" style="${containerStyle}">
      <!-- Top Header -->
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
        <div style="flex:1;">
          <div style="font-size:27px; font-weight:900; color:#D83220; letter-spacing:0.02em; line-height:1.1; font-family:Arial, sans-serif;">
            ELITEWASH DETERGENT
          </div>
          <!-- 3 Parallel Red Lines flanking Chak No: 56/W.B. Vehari -->
          <div style="display:flex; align-items:center; gap:8px; margin:4px 0 6px 0;">
            <div style="display:flex; flex-direction:column; gap:2.5px; width:75px;">
              <div style="height:1.5px; background:#D83220;"></div>
              <div style="height:1.5px; background:#D83220;"></div>
              <div style="height:1.5px; background:#D83220;"></div>
            </div>
            <span style="font-size:15px; font-weight:800; color:#D83220; white-space:nowrap;">Chak No: 56/W.B. Vehari</span>
            <div style="display:flex; flex-direction:column; gap:2.5px; width:75px;">
              <div style="height:1.5px; background:#D83220;"></div>
              <div style="height:1.5px; background:#D83220;"></div>
              <div style="height:1.5px; background:#D83220;"></div>
            </div>
          </div>
          <!-- Contacts -->
          <div style="font-size:11.5px; color:#D83220; line-height:1.4;">
            <div><span style="font-weight:700;">Chief Executive Officer</span> &nbsp;0324-0106056</div>
            <div><span style="font-weight:700; font-style:italic; font-family:Georgia, serif;">Shoaib Mehmood</span> &nbsp;0300-2791243</div>
          </div>
        </div>

        <!-- Registration Box -->
        <div style="border:1.5px solid #D83220; border-radius:8px; padding:6px 12px; text-align:left; min-width:180px; background:#ffffff;">
          <div style="font-size:11px; font-weight:700; color:#D83220; line-height:1.35;">Registration No:</div>
          <div style="font-size:11px; font-weight:700; color:#D83220; line-height:1.35;">36603-0283828-3</div>
          <div style="font-size:11px; font-weight:700; color:#D83220; line-height:1.35; margin-top:2px;">Ref. No: J895834</div>
        </div>
      </div>

      <!-- Title Banner -->
      <div style="text-align:center; margin:4px 0 8px 0;">
        <span style="font-size:14px; font-weight:800; color:#D83220; letter-spacing:0.22em; text-transform:uppercase;">
          ${formattedTitle}
        </span>
      </div>

      <!-- Meta Bar: Bill No & Date -->
      <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:8px; font-size:12.5px;">
        <div>
          <span style="color:#D83220; font-weight:800; font-size:13px;">Bill No:</span>
          <span style="color:#111827; font-weight:800; font-size:13px; margin-left:6px;">${formattedBillNo}</span>
          <span style="color:#111827; font-weight:700; font-size:11px; margin-left:4px;">(${refNo})</span>
        </div>
        <div style="display:flex; align-items:flex-end;">
          <span style="color:#D83220; font-weight:800; font-size:13px; margin-right:6px;">Date:</span>
          <div style="min-width:130px; border-bottom:1.5px solid #D83220; padding-bottom:1px; text-align:center;">
            <span style="color:#111827; font-weight:800; font-size:12.5px;">${dateStr}</span>
          </div>
        </div>
      </div>

      <!-- Distributor Box: M/s underlined in red -->
      <div style="display:flex; align-items:flex-end; margin-bottom:10px; font-size:12.5px;">
        <span style="color:#D83220; font-weight:800; font-size:13px; margin-right:8px; white-space:nowrap;">M/s</span>
        <div style="flex:1; border-bottom:1.5px solid #D83220; padding-bottom:1px;">
          <span style="color:#111827; font-weight:800; font-size:12.5px;">${distName}${distCode ? ` (${distCode})` : ''}</span>
        </div>
      </div>

      <!-- Items Table Container with Watermark -->
      <div style="position:relative; flex:1; display:flex; flex-direction:column;">
        <!-- Watermark -->
        <div style="position:absolute; top:48%; left:50%; transform:translate(-50%, -50%); width:440px; height:440px; pointer-events:none; opacity:0.32; z-index:1; display:flex; align-items:center; justify-content:center;">
          <img src="${watermarkUrl}" alt="Watermark Logo" style="width:100%; height:100%; object-fit:contain;" />
        </div>

        <!-- Table -->
        <table style="width:100%; border-collapse:collapse; position:relative; z-index:2; border:1.5px solid #D83220;">
          <thead>
            <tr style="height:34px; background:#ffffff; border-bottom:2px solid #D83220;">
              <th style="width:10.25%; text-align:center; font-size:12px; font-weight:800; color:#D83220; border-right:1px solid #D83220; padding:2px 4px;">Sr. No:</th>
              <th style="width:40.72%; text-align:center; font-size:12px; font-weight:800; color:#D83220; border-right:1px solid #D83220; padding:2px 8px;">Description</th>
              <th style="width:9.83%; text-align:center; font-size:12px; font-weight:800; color:#D83220; border-right:1px solid #D83220; padding:2px 4px;">Qty</th>
              <th style="width:14.13%; text-align:center; font-size:12px; font-weight:800; color:#D83220; border-right:1px solid #D83220; padding:2px 6px;">Price</th>
              <th style="width:25.07%; text-align:center; font-size:12px; font-weight:800; color:#D83220; padding:2px 8px;">Amount</th>
            </tr>
          </thead>
          <tbody>
            ${rowsHtml}
          </tbody>
          <tfoot>
            <tr style="height:36px; border-top:1px solid #D83220;">
              <td style="border-right:1px solid #D83220;"></td>
              <td style="border-right:1px solid #D83220;"></td>
              <td style="border-right:1px solid #D83220;"></td>
              <td style="background:#D83220; text-align:center; border-right:1px solid #D83220; padding:2px 4px;">
                <span style="font-size:13px; font-weight:900; color:#ffffff; letter-spacing:0.05em;">TOTAL</span>
              </td>
              <td style="text-align:right; font-size:13px; font-weight:800; color:#111827; padding:2px 12px;">
                ${Number(total).toLocaleString('en-PK')}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      <!-- Signatures and Stamps Authorization Area -->
      <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-top:16px; padding:0 6px;">
        <!-- Manager Authorization (Left) -->
        <div style="width:250px; text-align:center; position:relative;">
          <div style="height:76px; position:relative; margin-bottom:-10px;">
            <!-- Manager Circular Stamp (Blue Ink) -->
            <img src="${managerStampUrl}" alt="Manager Stamp" style="position:absolute; left:95px; bottom:6px; width:80px; height:80px; object-fit:contain; mix-blend-mode:multiply; opacity:0.94;" />
            <!-- Ghazanfar Handwritten Signature -->
            <img src="${managerSigUrl}" alt="Manager Signature" style="position:absolute; left:0px; bottom:10px; width:140px; max-height:60px; object-fit:contain; mix-blend-mode:multiply; z-index:2;" />
          </div>
          <div style="border-top:1.5px solid #D83220; padding-top:5px;">
            <div style="font-size:12.5px; font-weight:800; color:#D83220;">Manager Signature</div>
          </div>
        </div>

        <!-- CEO Authorization (Right) -->
        <div style="width:250px; text-align:center; position:relative;">
          <div style="height:76px; position:relative; margin-bottom:-10px;">
            <!-- CEO Circular Stamp (Blue Ink) -->
            <img src="${ceoStampUrl}" alt="CEO Stamp" style="position:absolute; right:15px; bottom:6px; width:80px; height:80px; object-fit:contain; mix-blend-mode:multiply; opacity:0.94;" />
            <!-- Shoaib Mehmood Handwritten Signature -->
            <img src="${ceoSigUrl}" alt="CEO Signature" style="position:absolute; right:25px; bottom:8px; width:105px; max-height:62px; object-fit:contain; mix-blend-mode:multiply; z-index:2;" />
          </div>
          <div style="border-top:1.5px solid #D83220; padding-top:5px;">
            <div style="font-size:12.5px; font-weight:800; color:#D83220;">Chief Executive Officer</div>
          </div>
        </div>
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
  <title>${padTitle} - ${refNo}</title>
  <style>
    @page { size: portrait; margin: 0; }
    *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
    html, body {
      width: 100%; height: 100%; margin: 0; padding: 0; background: #ffffff; overflow: hidden;
      -webkit-print-color-adjust: exact; print-color-adjust: exact;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    }
    body { display: flex; justify-content: center; align-items: flex-start; }
    .receipt-wrapper {
      position: relative; width: 100%; height: 100vh; max-height: 100vh; aspect-ratio: 792 / 1024;
      background: #ffffff; margin: 0 auto; page-break-inside: avoid; break-inside: avoid;
    }
    @media screen {
      body { background: #f3f4f6; padding: 10px 0; }
      .receipt-wrapper { box-shadow: 0 4px 20px rgba(0,0,0,0.12); max-width: 792px; height: auto; }
    }
    @media print {
      html, body { width: 100%; height: 100%; margin: 0 !important; padding: 0 !important; overflow: hidden !important; }
      .receipt-wrapper { box-shadow: none !important; margin: 0 auto !important; height: 100vh !important; max-height: 100vh !important; page-break-after: avoid !important; break-after: avoid !important; }
    }
  </style>
</head>
<body>
  ${bodyContent}
  <script>
    window.onload = function() { setTimeout(function() { window.print(); }, 400); };
  </script>
</body>
</html>`;
}

// --- BOOKING PAD (OFFICIAL ELITEWASH DETERGENT BILL PAD) HTML TEMPLATE ---
export function getBookingPadHtml(booking, options = {}) {
  const refNo = booking.reference_number || booking.ref || "";
  const displayBillNo = booking.formattedBillNo || booking.sequential_no || booking.display_bill_no || booking.bill_no || (refNo.startsWith('BKG-') ? refNo.replace(/^BKG-0*/, '') : refNo);
  const formattedBillNo = displayBillNo ? String(displayBillNo).padStart(2, '0') : '01';
  const dateStr = booking.sale_date ? new Date(booking.sale_date).toLocaleDateString("en-PK") : new Date().toLocaleDateString("en-PK");
  const distName = booking.distributors?.name || booking.distributorName || "—";
  const distCode = booking.distributors?.code || "";
  const distPhone = booking.distributors?.phone || "";
  
  const rawItems = booking.items || (booking.sale_items || []).map(i => ({
    description: i.product_packaging?.name ? `Elite Wash Surf (${i.product_packaging.name})` : (i.description || i.name || "Elite Wash Surf"),
    quantity: i.quantity,
    price: i.unit_price,
    amount: (i.quantity || 0) * (i.unit_price || 0)
  }));

  const total = booking.total_amount || booking.totalAmount || 0;

  return generateOfficialReceiptHtml({
    padTitle: 'BOOKING PAD',
    billNo: refNo,
    refNo,
    formattedBillNo,
    dateStr,
    distName,
    distCode,
    distPhone,
    rawItems,
    total,
    isForPdf: options.isForPdf || false
  });
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

// --- SHARED DIRECT JSPDF RENDERER FOR OFFICIAL BILL PAD TEMPLATES ---
function renderOfficialReceiptToJsPdf(doc, {
  padTitle,
  billNo,
  refNo,
  formattedBillNo,
  dateStr,
  distName,
  rawItems = [],
  total = 0
}) {
  const pdfWidth = doc.internal.pageSize.getWidth();
  const pdfHeight = doc.internal.pageSize.getHeight();

  // White Background
  doc.setFillColor(255, 255, 255);
  doc.rect(0, 0, pdfWidth, pdfHeight, 'F');

  const marginX = 28.5;
  const rightMargin = 24;
  const tableWidth = pdfWidth - marginX - rightMargin;

  // 1. Header (Left: Brand Name, 3 parallel lines, Contacts)
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(20);
  doc.setTextColor(216, 50, 32);
  doc.text('ELITEWASH DETERGENT', marginX, 46);

  // 3 Parallel Red Lines flanking Chak No: 56/W.B. Vehari
  doc.setDrawColor(216, 50, 32);
  doc.setLineWidth(1.2);
  const leftLineW = 50;
  doc.line(marginX, 58, marginX + leftLineW, 58);
  doc.line(marginX, 60.5, marginX + leftLineW, 60.5);
  doc.line(marginX, 63, marginX + leftLineW, 63);

  doc.setFontSize(11);
  doc.text('Chak No: 56/W.B. Vehari', marginX + leftLineW + 6, 62);
  const subTextW = doc.getTextWidth('Chak No: 56/W.B. Vehari');
  const rightLineX = marginX + leftLineW + 6 + subTextW + 6;
  doc.line(rightLineX, 58, rightLineX + leftLineW, 58);
  doc.line(rightLineX, 60.5, rightLineX + leftLineW, 60.5);
  doc.line(rightLineX, 63, rightLineX + leftLineW, 63);

  // Contacts
  doc.setFontSize(8.5);
  doc.setFont('helvetica', 'bold');
  doc.text('Chief Executive Officer', marginX, 76);
  doc.setFont('helvetica', 'normal');
  doc.text('0324-0106056', marginX + 96, 76);

  doc.setFont('times', 'bolditalic');
  doc.text('Shoaib Mehmood', marginX, 88);
  doc.setFont('helvetica', 'normal');
  doc.text('0300-2791243', marginX + 85, 88);

  // Registration Box (Top Right)
  const regBoxW = 135;
  const regBoxH = 46;
  const regBoxX = pdfWidth - rightMargin - regBoxW;
  const regBoxY = 28;
  doc.setDrawColor(216, 50, 32);
  doc.setLineWidth(1.2);
  doc.setFillColor(255, 255, 255);
  doc.roundedRect(regBoxX, regBoxY, regBoxW, regBoxH, 4, 4, 'FD');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8);
  doc.setTextColor(216, 50, 32);
  doc.text('Registration No:', regBoxX + 8, regBoxY + 14);
  doc.text('36603-0283828-3', regBoxX + 8, regBoxY + 25);
  doc.text('Ref. No: J895834', regBoxX + 8, regBoxY + 38);

  // 2. Pad Title (Center)
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10.5);
  doc.setTextColor(216, 50, 32);
  const formattedTitle = padTitle === 'DELIVERY BILL PAD' ? 'D E L I V E R Y   B I L L   P A D' : 'B O O K I N G   P A D';
  doc.text(formattedTitle, pdfWidth / 2, 108, { align: 'center' });

  // 3. Meta Bar: Bill No (Left) & Date (Right)
  doc.setFontSize(9.5);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(216, 50, 32);
  doc.text('Bill No:', marginX, 130);
  doc.setTextColor(17, 24, 39); // BLACK
  doc.text(String(formattedBillNo) + ' (' + refNo + ')', marginX + 38, 130);

  doc.setTextColor(216, 50, 32);
  doc.text('Date:', pdfWidth - rightMargin - 120, 130);
  doc.setTextColor(17, 24, 39); // BLACK
  doc.text(String(dateStr), pdfWidth - rightMargin - 90, 130);
  doc.setDrawColor(216, 50, 32);
  doc.setLineWidth(1);
  doc.line(pdfWidth - rightMargin - 94, 133, pdfWidth - rightMargin, 133);

  // 4. Distributor Box: M/s underlined in red
  doc.setTextColor(216, 50, 32);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9.5);
  doc.text('M/s', marginX, 148);
  doc.setTextColor(17, 24, 39); // BLACK
  doc.text(String(distName), marginX + 22, 148);
  doc.setDrawColor(216, 50, 32);
  doc.setLineWidth(1);
  doc.line(marginX + 20, 151, pdfWidth - rightMargin, 151);

  // 5. Items Table with Watermark
  const tableX = marginX;
  const tableY = 160;
  const tw = tableWidth;
  const colW = [tw * 0.1025, tw * 0.4072, tw * 0.0983, tw * 0.1413, tw * 0.2507];
  const colX = [
    tableX,
    tableX + colW[0],
    tableX + colW[0] + colW[1],
    tableX + colW[0] + colW[1] + colW[2],
    tableX + colW[0] + colW[1] + colW[2] + colW[3],
    tableX + tw
  ];

  // Watermark in Table Center
  try {
    const wmW = 240;
    const wmH = 240;
    const wmX = tableX + (tw - wmW) / 2;
    const wmY = tableY + 80;
    doc.addImage(RECEIPT_WATERMARK_BASE64, 'PNG', wmX, wmY, wmW, wmH);
  } catch (e) {
    console.warn('Could not add watermark:', e);
  }

  // Header Row
  const headerH = 22;
  doc.setDrawColor(216, 50, 32);
  doc.setLineWidth(1.2);
  doc.setFillColor(255, 255, 255);
  doc.rect(tableX, tableY, tw, headerH, 'FD');
  doc.line(tableX, tableY + headerH, tableX + tw, tableY + headerH);

  // Header Column Dividers
  for (let c = 1; c < colX.length - 1; c++) {
    doc.line(colX[c], tableY, colX[c], tableY + headerH);
  }

  // Header Text
  doc.setTextColor(216, 50, 32);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8.5);
  doc.text('Sr. No:', colX[0] + colW[0] / 2, tableY + 14, { align: 'center' });
  doc.text('Description', colX[1] + colW[1] / 2, tableY + 14, { align: 'center' });
  doc.text('Qty', colX[2] + colW[2] / 2, tableY + 14, { align: 'center' });
  doc.text('Price', colX[3] + colW[3] / 2, tableY + 14, { align: 'center' });
  doc.text('Amount', colX[4] + colW[4] / 2, tableY + 14, { align: 'center' });

  // 13 Data Rows
  const ROW_START_Y = tableY + headerH;
  const ROW_HEIGHT = 24;
  const MAX_ROWS = 13;

  for (let i = 0; i < MAX_ROWS; i++) {
    const item = rawItems[i];
    const y = ROW_START_Y + (i * ROW_HEIGHT);

    // Horizontal Row Border
    doc.setDrawColor(216, 50, 32);
    doc.setLineWidth(0.8);
    doc.line(tableX, y + ROW_HEIGHT, tableX + tw, y + ROW_HEIGHT);

    // Vertical Column Borders
    for (let c = 1; c < colX.length - 1; c++) {
      doc.line(colX[c], y, colX[c], y + ROW_HEIGHT);
    }

    if (item) {
      const srNo = String(i + 1);
      const desc = String(item.description || item.name || '');
      const qty = item.quantity !== undefined && item.quantity !== null && item.quantity !== ''
        ? Number(item.quantity).toLocaleString('en-PK') : '';
      const price = item.unit_price !== undefined ? Number(item.unit_price).toLocaleString('en-PK')
        : (item.price ? Number(item.price).toLocaleString('en-PK') : '');
      const amount = item.amount !== undefined ? Number(item.amount).toLocaleString('en-PK')
        : (qty && price ? Number(Number(item.quantity) * Number(item.unit_price || item.price)).toLocaleString('en-PK') : '');

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(8.5);
      doc.setTextColor(17, 24, 39); // BLACK

      // Sr No
      doc.text(srNo, colX[0] + colW[0] / 2, y + 16, { align: 'center' });

      // Description
      const truncatedDesc = desc.length > 34 ? desc.substring(0, 32) + '...' : desc;
      doc.text(truncatedDesc, colX[1] + 8, y + 16);

      // Qty
      if (qty) doc.text(qty, colX[2] + colW[2] / 2, y + 16, { align: 'center' });

      // Price
      if (price) doc.text(price, colX[4] - 8, y + 16, { align: 'right' });

      // Amount
      if (amount) doc.text(amount, tableX + tw - 8, y + 16, { align: 'right' });
    }
  }

  // 6. 14th Row (Total Row)
  const totalY = ROW_START_Y + (MAX_ROWS * ROW_HEIGHT);
  // Column 1, 2, 3 vertical lines
  for (let c = 1; c <= 3; c++) {
    doc.line(colX[c], totalY, colX[c], totalY + ROW_HEIGHT);
  }

  // Column 4: Red filled box with white text TOTAL
  doc.setFillColor(216, 50, 32);
  doc.rect(colX[3], totalY, colW[3], ROW_HEIGHT, 'F');
  doc.line(colX[4], totalY, colX[4], totalY + ROW_HEIGHT);
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9.5);
  doc.text('TOTAL', colX[3] + colW[3] / 2, totalY + 16, { align: 'center' });

  // Column 5: Total Amount in BLACK
  doc.setTextColor(17, 24, 39); // BLACK
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9.5);
  doc.text(Number(total).toLocaleString('en-PK'), tableX + tw - 8, totalY + 16, { align: 'right' });

  // Outer Table Box
  doc.setDrawColor(216, 50, 32);
  doc.setLineWidth(1.2);
  doc.rect(tableX, tableY, tw, headerH + (MAX_ROWS + 1) * ROW_HEIGHT);

  // 7. Signatures & Stamps Authorization Area
  const authY = totalY + ROW_HEIGHT + 14;
  const colWidth = 170;

  // Manager Authorization (Left)
  const mgrLeft = marginX + 15;
  try {
    doc.addImage(MANAGER_STAMP_BASE64, 'JPEG', mgrLeft + 65, authY, 56, 56);
    doc.addImage(MANAGER_SIGNATURE_BASE64, 'PNG', mgrLeft, authY + 6, 95, 46);
  } catch (e) {
    console.warn('Error adding manager assets:', e);
  }
  doc.setDrawColor(216, 50, 32);
  doc.setLineWidth(1.2);
  doc.line(mgrLeft, authY + 54, mgrLeft + colWidth, authY + 54);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9);
  doc.setTextColor(216, 50, 32);
  doc.text('Manager Signature', mgrLeft + colWidth / 2, authY + 66, { align: 'center' });

  // CEO Authorization (Right)
  const ceoLeft = pdfWidth - rightMargin - 15 - colWidth;
  try {
    doc.addImage(CEO_STAMP_BASE64, 'JPEG', ceoLeft + 85, authY, 56, 56);
    doc.addImage(CEO_SIGNATURE_BASE64, 'PNG', ceoLeft + 65, authY + 4, 80, 48);
  } catch (e) {
    console.warn('Error adding CEO assets:', e);
  }
  doc.line(ceoLeft, authY + 54, ceoLeft + colWidth, authY + 54);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9);
  doc.setTextColor(216, 50, 32);
  doc.text('Chief Executive Officer', ceoLeft + colWidth / 2, authY + 66, { align: 'center' });

  return doc;
}


// --- DIRECT JSPDF RENDERER FOR OFFICIAL BILL PAD TEMPLATE ---
export function renderBookingPadToJsPdf(doc, booking) {
  const refNo = booking.reference_number || booking.ref || "BKG-ORDER";
  const displayBillNo = booking.formattedBillNo || booking.sequential_no || booking.display_bill_no || booking.bill_no || (refNo.startsWith('BKG-') ? refNo.replace(/^BKG-0*/, '') : refNo);
  const formattedBillNo = displayBillNo ? String(displayBillNo).padStart(2, '0') : '01';
  const dateStr = booking.sale_date ? new Date(booking.sale_date).toLocaleDateString("en-PK") : new Date().toLocaleDateString("en-PK");
  const distName = booking.distributors?.name || booking.distributorName || "—";
  
  const rawItems = booking.items || (booking.sale_items || []).map(i => ({
    description: i.product_packaging?.name ? `Elite Wash Surf (${i.product_packaging.name})` : (i.description || i.name || "Elite Wash Surf"),
    quantity: i.quantity,
    price: i.unit_price,
    amount: (i.quantity || 0) * (i.unit_price || 0)
  }));

  const total = booking.total_amount || booking.totalAmount || 0;

  return renderOfficialReceiptToJsPdf(doc, {
    padTitle: 'BOOKING PAD',
    billNo: refNo,
    refNo,
    formattedBillNo,
    dateStr,
    distName,
    rawItems,
    total
  });
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
  const padHeightPt = (1024 / 792) * 595.28;

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

// --- DISTRIBUTOR PAD (OFFICIAL PRINTED BILL OVERLAY) HTML TEMPLATE ---
export function getDistributorPadHtml(sale, options = {}) {
  const billNo       = sale.billNo || sale.reference_number || "";
  const displayBillNo = sale.display_bill_no || sale.bill_no || (billNo.startsWith('SAL-') ? billNo.replace(/^SAL-0*/, '') : billNo);
  const formattedBillNo = displayBillNo ? String(displayBillNo).padStart(2, '0') : '01';
  const dateStr     = sale.date || (sale.sale_date ? new Date(sale.sale_date).toLocaleDateString("en-PK") : new Date().toLocaleDateString("en-PK"));
  const distName  = sale.distributorName || sale.distributors?.name || "—";
  const distCode = sale.distributors?.code || "";
  const distPhone = sale.distributors?.phone || "";
  const rawItems     = sale.items || (sale.sale_items || []).map(i => ({
    description: i.product_packaging?.name ? `Elite Wash Surf (${i.product_packaging.name})` : (i.description || i.name || "Elite Wash Surf"),
    quantity: i.quantity,
    price: i.unit_price,
    amount: (i.quantity || 0) * (i.unit_price || 0)
  }));
  const total        = sale.totalAmount || sale.total_amount || 0;

  return generateOfficialReceiptHtml({
    padTitle: 'DELIVERY BILL PAD',
    billNo,
    refNo: billNo,
    formattedBillNo,
    dateStr,
    distName,
    distCode,
    distPhone,
    rawItems,
    total,
    isForPdf: options.isForPdf || false
  });
}

// --- PRINT DISTRIBUTOR DELIVERY PAD ---
export function printDistributorPad(sale) {
  const win = window.open("", "_blank");
  if (!win) {
    alert("Please allow popups to print delivery receipts.");
    return;
  }
  const html = getDistributorPadHtml(sale, { isForPdf: false });
  win.document.open();
  win.document.write(html);
  win.document.close();
}

// Backward-compatible alias
export const printSaleReceipt = printDistributorPad;

// --- DIRECT JSPDF RENDERER FOR DELIVERY PAD ---
export function renderDistributorPadToJsPdf(doc, sale) {
  const billNo = sale.billNo || sale.reference_number || "SAL-INVOICE";
  const displayBillNo = sale.display_bill_no || sale.bill_no || (billNo.startsWith('SAL-') ? billNo.replace(/^SAL-0*/, '') : billNo);
  const formattedBillNo = displayBillNo ? String(displayBillNo).padStart(2, '0') : '01';
  const dateStr = sale.date || (sale.sale_date ? new Date(sale.sale_date).toLocaleDateString("en-PK") : new Date().toLocaleDateString("en-PK"));
  const distName = sale.distributorName || sale.distributors?.name || "—";
  
  const rawItems = sale.items || (sale.sale_items || []).map(i => ({
    description: i.product_packaging?.name ? `Elite Wash Surf (${i.product_packaging.name})` : (i.description || i.name || "Elite Wash Surf"),
    quantity: i.quantity,
    price: i.unit_price,
    amount: (i.quantity || 0) * (i.unit_price || 0)
  }));
  const total = sale.totalAmount || sale.total_amount || 0;

  return renderOfficialReceiptToJsPdf(doc, {
    padTitle: 'DELIVERY BILL PAD',
    billNo,
    refNo: billNo,
    formattedBillNo,
    dateStr,
    distName,
    rawItems,
    total
  });
}

// --- GENERATE SIGNED DELIVERY PAD PDF ---
export async function generateDistributorPadPdf(sale, distributor = null) {
  const saleWithDist = {
    ...sale,
    distributors: sale.distributors || distributor || null
  };
  const billNo = saleWithDist.billNo || saleWithDist.reference_number || "SALE";
  const filename = `${billNo}.pdf`;
  const padWidthPt = 595.28;
  const padHeightPt = (1024 / 792) * 595.28;

  if (typeof document === 'undefined' || typeof window === 'undefined') {
    const doc = new jsPDF({ orientation: 'portrait', unit: 'pt', format: [padWidthPt, padHeightPt] });
    renderDistributorPadToJsPdf(doc, saleWithDist);
    const arrayBuffer = doc.output('arraybuffer');
    const blob = typeof Blob !== 'undefined' ? new Blob([arrayBuffer], { type: 'application/pdf' }) : null;
    const file = (typeof File !== 'undefined' && blob) ? new File([blob], filename, { type: 'application/pdf' }) : null;
    return { doc, blob, file, filename };
  }

  const container = document.createElement('div');
  container.style.position = 'fixed';
  container.style.left = '-9999px';
  container.style.top = '0';
  container.style.width = '668px';
  container.style.height = '1024px';
  container.style.background = '#ffffff';
  container.style.boxSizing = 'border-box';
  container.style.zIndex = '-9999';

  container.innerHTML = getDistributorPadHtml(saleWithDist, { isForPdf: true });
  document.body.appendChild(container);

  try {
    if (typeof container.querySelectorAll === 'function') {
      const images = container.querySelectorAll('img');
      await Promise.all(Array.from(images).map(img => {
        if (img.complete) return Promise.resolve();
        return new Promise(resolve => { img.onload = resolve; img.onerror = resolve; });
      }));
    }

    const canvas = await html2canvas(container, { scale: 2, useCORS: true, logging: false, backgroundColor: '#ffffff' });
    const doc = new jsPDF({ orientation: 'portrait', unit: 'pt', format: [padWidthPt, padHeightPt] });
    const imgData = canvas.toDataURL('image/jpeg', 0.95);
    doc.addImage(imgData, 'JPEG', 0, 0, padWidthPt, padHeightPt);

    const blob = doc.output('blob');
    const file = typeof File !== 'undefined' ? new File([blob], filename, { type: 'application/pdf' }) : null;
    return { doc, blob, file, filename };
  } catch (err) {
    console.warn('html2canvas render failed, falling back to direct jsPDF engine:', err);
    const doc = new jsPDF({ orientation: 'portrait', unit: 'pt', format: [padWidthPt, padHeightPt] });
    renderDistributorPadToJsPdf(doc, saleWithDist);
    const blob = doc.output('blob');
    const file = typeof File !== 'undefined' ? new File([blob], filename, { type: 'application/pdf' }) : null;
    return { doc, blob, file, filename };
  } finally {
    if (container.parentNode) document.body.removeChild(container);
  }
}

// --- SHARE DELIVERY PAD PDF ON WHATSAPP WORKFLOW ---
export async function shareDistributorPadOnWhatsApp({
  sale,
  distributor = null,
  targetWindow = null,
  onProgress = () => {},
  onSuccess = () => {},
  onError = () => {}
}) {
  try {
    const dist = (Array.isArray(sale.distributors) ? sale.distributors[0] : sale.distributors)
      || distributor
      || null;

    if (!dist) {
      if (targetWindow && !targetWindow.closed) { try { targetWindow.close(); } catch (_) {} }
      const msg = 'Cannot share receipt: No distributor is linked to this sale.';
      onError(msg);
      return { success: false, reason: 'missing_distributor', message: msg };
    }

    const formattedPhone = formatPakistaniPhoneForWhatsApp(dist.phone);
    if (!formattedPhone) {
      if (targetWindow && !targetWindow.closed) { try { targetWindow.close(); } catch (_) {} }
      const msg = `Cannot share receipt: Distributor ${dist.name || ''} has no valid registered phone number.`;
      onError(msg);
      return { success: false, reason: 'invalid_phone', message: msg };
    }

    const billNo = sale.billNo || sale.reference_number || 'SALE';
    const filename = `${billNo}.pdf`;
    const waUrl = `https://wa.me/${formattedPhone}`;

    if (targetWindow && !targetWindow.closed) {
      try { targetWindow.location.href = waUrl; } catch (navErr) { console.warn('Could not navigate tab:', navErr); }
    }

    onProgress('Generating official signed delivery receipt PDF...');
    const { blob, file } = await generateDistributorPadPdf(sale, dist);

    if (typeof navigator !== 'undefined' && navigator.canShare && file) {
      const shareData = { files: [file], title: `Delivery Bill - ${billNo}` };
      if (navigator.canShare(shareData)) {
        try {
          await navigator.share(shareData);
          if (targetWindow && !targetWindow.closed) { try { targetWindow.close(); } catch (_) {} }
          const successMsg = `Delivery bill PDF shared successfully with ${dist.name}.`;
          onSuccess(successMsg, { mode: 'native_share', filename, phone: formattedPhone });
          return { success: true, mode: 'native_share', filename, phone: formattedPhone };
        } catch (shareErr) {
          if (shareErr.name === 'AbortError') {
            if (targetWindow && !targetWindow.closed) { try { targetWindow.close(); } catch (_) {} }
            return { success: false, reason: 'cancelled', message: 'Share cancelled.' };
          }
        }
      }
    }

    if (typeof document !== 'undefined' && blob) {
      const downloadUrl = URL.createObjectURL(blob);
      const downloadLink = document.createElement('a');
      downloadLink.href = downloadUrl;
      downloadLink.download = filename;
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
      setTimeout(() => { if (typeof URL !== 'undefined' && URL.revokeObjectURL) URL.revokeObjectURL(downloadUrl); }, 3000);
    }

    let popupBlocked = false;
    if (!targetWindow || targetWindow.closed) {
      if (typeof window !== 'undefined') {
        const opened = window.open(waUrl, '_blank');
        if (!opened || opened.closed || typeof opened.closed === 'undefined') popupBlocked = true;
      }
    }

    const fallbackMsg = popupBlocked
      ? `Signed delivery receipt downloaded (${filename}). Click "Open WhatsApp Chat" below to send to ${dist.name}.`
      : `Signed delivery receipt downloaded (${filename}). WhatsApp chat opened with ${dist.name}. Please attach the downloaded PDF in WhatsApp.`;

    onSuccess(fallbackMsg, {
      mode: 'download_and_chat',
      filename,
      phone: formattedPhone,
      waUrl,
      distName: dist.name,
      popupBlocked,
      instructions: `The PDF document '${filename}' has been downloaded to your computer. In the opened WhatsApp tab, click the attachment icon (📎) → Document and select '${filename}'.`
    });

    return { success: true, mode: 'download_and_chat', filename, phone: formattedPhone, waUrl, distName: dist.name, popupBlocked };
  } catch (err) {
    console.error('Error in shareDistributorPadOnWhatsApp:', err);
    const errMsg = `Failed to generate or share delivery PDF: ${err.message}`;
    onError(errMsg);
    return { success: false, reason: 'error', message: errMsg };
  }
}

// --- PERSON PAYMENT VOUCHER (TASK 7: MANUFACTURER / WORKER PAYMENT PAD) ---
export function getPersonPaymentVoucherHtml({ entry, person, options = {} }) {
  const receiptUrl = (typeof window !== 'undefined' && window.location?.origin ? window.location.origin : '') + "/receipt.jpeg";
  const signatureUrl = (typeof window !== 'undefined' && window.location?.origin ? window.location.origin : '') + "/ceo-signature.png";
  const logoUrl = (typeof window !== 'undefined' && window.location?.origin ? window.location.origin : '') + "/elitewash-logo.jpg";

  const refNo = entry.reference_number || `PAY-${String(entry.id || '').substring(0, 8).toUpperCase()}`;
  const dateStr = entry.entry_date ? new Date(entry.entry_date).toLocaleDateString("en-PK") : new Date().toLocaleDateString("en-PK");
  const pName = person?.name || entry.persons?.name || "—";
  const pCode = person?.code || entry.persons?.code || "—";
  const pCat = person?.category || entry.persons?.category || "Worker / Manufacturer";
  const pPhone = person?.phone || entry.persons?.phone || "—";
  const pCnic = person?.cnic || entry.persons?.cnic || "—";
  const amount = Number(entry.amount || entry.debit || entry.credit || 0);
  const typeLabel = (entry.entry_type || 'Payment').replace(/_/g, ' ');
  const method = entry.payment_method || 'Cash';
  const tid = entry.tid ? ` (TID: ${entry.tid})` : '';
  const desc = entry.description || '—';
  const balance = entry.balance !== undefined && entry.balance !== null ? Number(entry.balance) : null;

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Payment Voucher - ${refNo}</title>
  <style>
    @page { size: portrait; margin: 12mm; }
    * { margin:0; padding:0; box-sizing:border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Space Grotesk", sans-serif; color: #111827; background: #fff; padding: 20px; max-width: 780px; margin: 0 auto; }
    .voucher-card { border: 2px solid #0e7c86; border-radius: 10px; padding: 24px; background: #fff; position: relative; }
    .header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #0e7c86; padding-bottom: 14px; margin-bottom: 18px; }
    .company-title { font-size: 22px; font-weight: 800; color: #0e7c86; letter-spacing: -0.01em; }
    .company-sub { font-size: 11.5px; color: #4b5563; margin-top: 2px; }
    .company-address { font-size: 11px; color: #6b7280; margin-top: 2px; }
    .voucher-badge { text-align: right; }
    .voucher-title { font-size: 17px; font-weight: 800; color: #111827; text-transform: uppercase; letter-spacing: 0.05em; }
    .voucher-ref { font-size: 12px; font-family: monospace; font-weight: 700; color: #0e7c86; margin-top: 3px; }
    .meta-box { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px; margin-bottom: 18px; }
    .meta-label { font-size: 10.5px; text-transform: uppercase; color: #6b7280; font-weight: 600; margin-bottom: 2px; }
    .meta-val { font-size: 13px; font-weight: 700; color: #111827; }
    .amount-highlight { background: #f0fdfa; border: 2px solid #0e7c86; border-radius: 8px; padding: 16px; text-align: center; margin-bottom: 18px; }
    .amount-label { font-size: 11px; text-transform: uppercase; color: #0e7c86; font-weight: 700; letter-spacing: 0.08em; }
    .amount-number { font-size: 30px; font-weight: 900; color: #0e7c86; margin: 4px 0; }
    .data-table { width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 12.5px; }
    .data-table td { padding: 9px 12px; border-bottom: 1px solid #e5e7eb; }
    .data-table td:first-child { width: 32%; color: #4b5563; font-weight: 600; }
    .data-table td:last-child { color: #111827; font-weight: 600; }
    .sig-row { display: flex; justify-content: space-between; align-items: flex-end; margin-top: 40px; padding-top: 10px; }
    .sig-block { width: 190px; text-align: center; }
    .sig-line { border-top: 1px solid #6b7280; padding-top: 6px; font-size: 11px; color: #4b5563; font-weight: 600; }
    .ceo-sig-img { max-height: 48px; width: auto; object-fit: contain; margin-bottom: 4px; }
    @media print { body { padding: 0; } .voucher-card { border-width: 1.5px; } }
  </style>
</head>
<body>
  <div class="voucher-card">
    <div class="header">
      <div>
        <div class="company-title">ELITE WASH</div>
        <div class="company-sub">Surf Stock &amp; Ledger Control System</div>
        <div class="company-address">Chak No: 56/W.B. Vehari &nbsp;·&nbsp; Ph: 0324-0106056 / 0300-2791243</div>
      </div>
      <div class="voucher-badge">
        <div class="voucher-title">PAYMENT VOUCHER</div>
        <div class="voucher-ref">${refNo}</div>
        <div style="font-size:11.5px;color:#6b7280;margin-top:2px;">Date: ${dateStr}</div>
      </div>
    </div>

    <div class="meta-box">
      <div>
        <div class="meta-label">Beneficiary / Person</div>
        <div class="meta-val">${pName} (${pCode})</div>
      </div>
      <div>
        <div class="meta-label">Category / Role</div>
        <div class="meta-val">${pCat}</div>
      </div>
      <div>
        <div class="meta-label">Phone &amp; CNIC</div>
        <div class="meta-val">${pPhone} ${pCnic !== '—' ? '· ' + pCnic : ''}</div>
      </div>
      <div>
        <div class="meta-label">Payment Channel</div>
        <div class="meta-val">${method}${tid}</div>
      </div>
    </div>

    <div class="amount-highlight">
      <div class="amount-label">Amount Paid / Disbursed</div>
      <div class="amount-number">Rs. ${amount.toLocaleString('en-PK')}</div>
      <div style="font-size:12px;color:#4b5563;">Status: <strong style="color:#059669;">Approved</strong></div>
    </div>

    <table class="data-table">
      <tr>
        <td>Transaction Type</td>
        <td>${typeLabel}</td>
      </tr>
      <tr>
        <td>Description / Purpose</td>
        <td>${desc}</td>
      </tr>
      ${entry.quantity > 0 && entry.rate > 0 ? `
      <tr>
        <td>Piece Details</td>
        <td>${entry.quantity} units @ Rs. ${entry.rate} / unit</td>
      </tr>` : ''}
      ${balance !== null ? `
      <tr>
        <td>Closing Balance With Person</td>
        <td><strong>Rs. ${Math.abs(balance).toLocaleString('en-PK')} ${balance > 0 ? '(Payable by Company)' : balance < 0 ? '(Advance Outstanding)' : '(Settled)'}</strong></td>
      </tr>` : ''}
    </table>

    <div class="sig-row">
      <div class="sig-block">
        <div class="sig-line">Prepared By (Accounts)</div>
      </div>
      <div class="sig-block">
        <div class="sig-line">Receiver's Signature / Thumb</div>
      </div>
      <div class="sig-block">
        <img src="${signatureUrl}" alt="CEO Signature" class="ceo-sig-img" />
        <div class="sig-line">Chief Executive Officer</div>
      </div>
    </div>
  </div>
  <script>
    window.onload = function() { setTimeout(function() { window.print(); }, 400); };
  </script>
</body>
</html>`;
}

// --- PRINT PERSON PAYMENT VOUCHER ---
export function printPersonPaymentVoucher({ entry, person }) {
  const win = window.open("", "_blank");
  if (!win) {
    alert("Please allow popups to print payment vouchers.");
    return;
  }
  const html = getPersonPaymentVoucherHtml({ entry, person });
  win.document.open();
  win.document.write(html);
  win.document.close();
}

// --- GENERATE PERSON PAYMENT VOUCHER PDF VIA JSPDF ---
export async function generatePersonPaymentVoucherPdf({ entry, person }) {
  const refNo = entry.reference_number || `PAY-${String(entry.id || '').substring(0, 8).toUpperCase()}`;
  const filename = `${refNo}.pdf`;
  const pName = person?.name || entry.persons?.name || "Worker";
  const pCode = person?.code || entry.persons?.code || "";
  const pCat = person?.category || entry.persons?.category || "Worker / Manufacturer";
  const amount = Number(entry.amount || entry.debit || entry.credit || 0);
  const dateStr = entry.entry_date ? new Date(entry.entry_date).toLocaleDateString("en-PK") : new Date().toLocaleDateString("en-PK");

  const doc = new jsPDF({ orientation: 'portrait', unit: 'pt', format: 'a4' });
  const pageWidth = doc.internal.pageSize.getWidth();

  // Outer border
  doc.setDrawColor(14, 124, 134);
  doc.setLineWidth(2);
  doc.roundedRect(30, 30, pageWidth - 60, 480, 8, 8, 'S');

  // Header
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(18);
  doc.setTextColor(14, 124, 134);
  doc.text('ELITE WASH', 45, 60);

  doc.setFontSize(9);
  doc.setTextColor(75, 85, 99);
  doc.setFont('helvetica', 'normal');
  doc.text('Surf Stock & Ledger Control System', 45, 73);
  doc.text('Chak No: 56/W.B. Vehari · Ph: 0324-0106056 / 0300-2791243', 45, 85);

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(13);
  doc.setTextColor(17, 24, 39);
  doc.text('PAYMENT VOUCHER', pageWidth - 45, 60, { align: 'right' });
  doc.setFontSize(9.5);
  doc.setTextColor(14, 124, 134);
  doc.text(refNo, pageWidth - 45, 74, { align: 'right' });
  doc.setTextColor(107, 114, 128);
  doc.setFont('helvetica', 'normal');
  doc.text(`Date: ${dateStr}`, pageWidth - 45, 87, { align: 'right' });

  // Divider
  doc.setDrawColor(14, 124, 134);
  doc.setLineWidth(1.5);
  doc.line(45, 98, pageWidth - 45, 98);

  // Beneficiary Info Box
  doc.setFillColor(249, 250, 251);
  doc.roundedRect(45, 110, pageWidth - 90, 60, 4, 4, 'F');
  doc.setDrawColor(229, 231, 235);
  doc.setLineWidth(1);
  doc.roundedRect(45, 110, pageWidth - 90, 60, 4, 4, 'S');

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8.5);
  doc.setTextColor(107, 114, 128);
  doc.text('BENEFICIARY / PERSON:', 55, 126);
  doc.text('CATEGORY / ROLE:', (pageWidth / 2) + 10, 126);
  doc.text('PHONE & CNIC:', 55, 154);
  doc.text('PAYMENT CHANNEL:', (pageWidth / 2) + 10, 154);

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10);
  doc.setTextColor(17, 24, 39);
  doc.text(`${pName} (${pCode})`, 55, 138);
  doc.text(pCat, (pageWidth / 2) + 10, 138);
  doc.text(`${person?.phone || '—'} · ${person?.cnic || '—'}`, 55, 164);
  doc.text(`${entry.payment_method || 'Cash'}${entry.tid ? ' (' + entry.tid + ')' : ''}`, (pageWidth / 2) + 10, 164);

  // Amount Highlight Box
  doc.setFillColor(240, 253, 250);
  doc.roundedRect(45, 185, pageWidth - 90, 65, 6, 6, 'F');
  doc.setDrawColor(14, 124, 134);
  doc.setLineWidth(1.5);
  doc.roundedRect(45, 185, pageWidth - 90, 65, 6, 6, 'S');

  doc.setFontSize(9);
  doc.setTextColor(14, 124, 134);
  doc.text('AMOUNT PAID / DISBURSED', pageWidth / 2, 202, { align: 'center' });
  doc.setFontSize(22);
  doc.text(`Rs. ${amount.toLocaleString('en-PK')}`, pageWidth / 2, 226, { align: 'center' });
  doc.setFontSize(8.5);
  doc.setTextColor(5, 150, 105);
  doc.text('Status: Approved & Verified', pageWidth / 2, 240, { align: 'center' });

  // Details Table
  autoTable(doc, {
    startY: 260,
    margin: { left: 45, right: 45 },
    theme: 'plain',
    styles: { fontSize: 9, cellPadding: 5, textColor: [31, 41, 55] },
    columnStyles: { 0: { fontStyle: 'bold', width: 140, textColor: [75, 85, 99] } },
    body: [
      ['Transaction Type', (entry.entry_type || 'Payment').replace(/_/g, ' ')],
      ['Description / Purpose', entry.description || '—'],
      ...(entry.quantity > 0 && entry.rate > 0 ? [['Piece Details', `${entry.quantity} units @ Rs. ${entry.rate} / unit`]] : []),
      ...(entry.balance !== undefined && entry.balance !== null ? [['Closing Balance', `Rs. ${Math.abs(Number(entry.balance)).toLocaleString('en-PK')} ${Number(entry.balance) > 0 ? '(Payable by Company)' : Number(entry.balance) < 0 ? '(Advance Outstanding)' : '(Settled)'}`]] : [])
    ]
  });

  // Signatures
  const sigY = 460;
  doc.setDrawColor(156, 163, 175);
  doc.setLineWidth(0.8);
  doc.line(55, sigY, 185, sigY);
  doc.line(pageWidth / 2 - 65, sigY, pageWidth / 2 + 65, sigY);
  doc.line(pageWidth - 185, sigY, pageWidth - 55, sigY);

  doc.setFontSize(8);
  doc.setTextColor(107, 114, 128);
  doc.text('Prepared By (Accounts)', 120, sigY + 12, { align: 'center' });
  doc.text("Receiver's Signature", pageWidth / 2, sigY + 12, { align: 'center' });
  doc.text('Chief Executive Officer', pageWidth - 120, sigY + 12, { align: 'center' });

  try {
    doc.addImage(CEO_SIGNATURE_BASE64, 'PNG', pageWidth - 165, sigY - 36, 90, 32);
  } catch (_) {}

  const blob = doc.output('blob');
  const file = typeof File !== 'undefined' ? new File([blob], filename, { type: 'application/pdf' }) : null;
  return { doc, blob, file, filename };
}

// --- SHARE PERSON PAYMENT VOUCHER ON WHATSAPP WORKFLOW ---
export async function sharePersonPaymentVoucherOnWhatsApp({
  entry,
  person,
  targetWindow = null,
  onProgress = () => {},
  onSuccess = () => {},
  onError = () => {}
}) {
  try {
    const p = person || entry.persons || null;
    if (!p) {
      if (targetWindow && !targetWindow.closed) { try { targetWindow.close(); } catch (_) {} }
      const msg = 'Cannot share voucher: No worker / person details available.';
      onError(msg);
      return { success: false, reason: 'missing_person', message: msg };
    }

    const formattedPhone = formatPakistaniPhoneForWhatsApp(p.phone);
    if (!formattedPhone) {
      if (targetWindow && !targetWindow.closed) { try { targetWindow.close(); } catch (_) {} }
      const msg = `Cannot share voucher: ${p.name || 'Worker'} has no valid registered phone number.`;
      onError(msg);
      return { success: false, reason: 'invalid_phone', message: msg };
    }

    const refNo = entry.reference_number || `PAY-${String(entry.id || '').substring(0, 8).toUpperCase()}`;
    const filename = `${refNo}.pdf`;
    const waUrl = `https://wa.me/${formattedPhone}`;

    if (targetWindow && !targetWindow.closed) {
      try { targetWindow.location.href = waUrl; } catch (navErr) { console.warn('Could not navigate tab:', navErr); }
    }

    onProgress('Generating official signed payment voucher PDF...');
    const { blob, file } = await generatePersonPaymentVoucherPdf({ entry, person: p });

    if (typeof navigator !== 'undefined' && navigator.canShare && file) {
      const shareData = { files: [file], title: `Payment Voucher - ${refNo}` };
      if (navigator.canShare(shareData)) {
        try {
          await navigator.share(shareData);
          if (targetWindow && !targetWindow.closed) { try { targetWindow.close(); } catch (_) {} }
          const successMsg = `Payment voucher PDF shared successfully with ${p.name}.`;
          onSuccess(successMsg, { mode: 'native_share', filename, phone: formattedPhone });
          return { success: true, mode: 'native_share', filename, phone: formattedPhone };
        } catch (shareErr) {
          if (shareErr.name === 'AbortError') {
            if (targetWindow && !targetWindow.closed) { try { targetWindow.close(); } catch (_) {} }
            return { success: false, reason: 'cancelled', message: 'Share cancelled.' };
          }
        }
      }
    }

    if (typeof document !== 'undefined' && blob) {
      const downloadUrl = URL.createObjectURL(blob);
      const downloadLink = document.createElement('a');
      downloadLink.href = downloadUrl;
      downloadLink.download = filename;
      document.body.appendChild(downloadLink);
      downloadLink.click();
      document.body.removeChild(downloadLink);
      setTimeout(() => { if (typeof URL !== 'undefined' && URL.revokeObjectURL) URL.revokeObjectURL(downloadUrl); }, 3000);
    }

    let popupBlocked = false;
    if (!targetWindow || targetWindow.closed) {
      if (typeof window !== 'undefined') {
        const opened = window.open(waUrl, '_blank');
        if (!opened || opened.closed || typeof opened.closed === 'undefined') popupBlocked = true;
      }
    }

    const fallbackMsg = popupBlocked
      ? `Signed payment voucher downloaded (${filename}). Click "Open WhatsApp Chat" below to send to ${p.name}.`
      : `Signed payment voucher downloaded (${filename}). WhatsApp chat opened with ${p.name}. Please attach the downloaded PDF in WhatsApp.`;

    onSuccess(fallbackMsg, {
      mode: 'download_and_chat',
      filename,
      phone: formattedPhone,
      waUrl,
      personName: p.name,
      popupBlocked,
      instructions: `The voucher PDF '${filename}' has been downloaded to your computer. In the opened WhatsApp tab, click 📎 Attachment → Document and select '${filename}'.`
    });

    return { success: true, mode: 'download_and_chat', filename, phone: formattedPhone, waUrl, personName: p.name, popupBlocked };
  } catch (err) {
    console.error('Error in sharePersonPaymentVoucherOnWhatsApp:', err);
    const errMsg = `Failed to generate or share payment voucher PDF: ${err.message}`;
    onError(errMsg);
    return { success: false, reason: 'error', message: errMsg };
  }
}

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


