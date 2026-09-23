/**
 * Elite Washwo - Export & Print Utilities
 * Generates real CSV, PDF (via jsPDF & printable window), and WhatsApp share links.
 */
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

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
        <title>${title} - Elite Washwo</title>
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
            <div class="logo">ELITE WASHWO</div>
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
  doc.text('ELITE WASHWO', 40, 40);

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

// --- WHATSAPP SHARE ---
export function shareOnWhatsApp({ title, lines = [], phone = '' }) {
  const cleanPhone = (phone || '').replace(/[^0-9]/g, '');
  const header = `*ELITE WASHWO — ${title.toUpperCase()}*\nDate: ${new Date().toLocaleDateString('en-PK')}\n`;
  const body = lines.filter(Boolean).join('\n');
  const footer = `\n_Generated via Elite Washwo ERP_`;
  const fullMessage = `${header}\n${body}${footer}`;

  const encoded = encodeURIComponent(fullMessage);
  let url = `https://wa.me/?text=${encoded}`;
  if (cleanPhone) {
    const formattedPhone = cleanPhone.startsWith('0') ? '92' + cleanPhone.substring(1) : cleanPhone;
    url = `https://wa.me/${formattedPhone}?text=${encoded}`;
  }

  window.open(url, '_blank');
}