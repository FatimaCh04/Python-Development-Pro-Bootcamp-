import codecs

code = r"""
export function printSaleReceipt(sale) {
  const win = window.open('', '_blank');
  if (!win) {
    alert('Please allow popups to print reports.');
    return;
  }
  
  const logoUrl = window.location.origin + '/elitewash-logo.jpg';
  
  const tableRows = (sale.items || []).map((item, idx) => `
    <tr>
      <td style="border: 1px solid #000; padding: 6px; text-align: center;">${idx + 1}</td>
      <td style="border: 1px solid #000; padding: 6px; text-align: left;">${item.description || item.product_packaging?.products?.name + ' ' + item.product_packaging?.packagings?.name || ''}</td>
      <td style="border: 1px solid #000; padding: 6px; text-align: center;">${item.quantity || 0}</td>
      <td style="border: 1px solid #000; padding: 6px; text-align: right;">${item.unit_price || 0}</td>
      <td style="border: 1px solid #000; padding: 6px; text-align: right;">${(item.quantity || 0) * (item.unit_price || 0)}</td>
    </tr>
  `).join('');
  
  const emptyRowsNeeded = Math.max(0, 10 - (sale.items || []).length);
  const emptyRows = Array.from({length: emptyRowsNeeded}).map((_, idx) => `
    <tr>
      <td style="border: 1px solid #000; padding: 6px;">&nbsp;</td>
      <td style="border: 1px solid #000; padding: 6px;">&nbsp;</td>
      <td style="border: 1px solid #000; padding: 6px;">&nbsp;</td>
      <td style="border: 1px solid #000; padding: 6px;">&nbsp;</td>
      <td style="border: 1px solid #000; padding: 6px;">&nbsp;</td>
    </tr>
  `).join('');

  const html = `
    <!DOCTYPE html>
    <html>
      <head>
        <title>Sale Receipt - ${sale.billNo || ''}</title>
        <style>
          @page { size: A4; margin: 20mm; }
          body { font-family: Arial, sans-serif; color: #000; margin: 0; padding: 0; font-size: 14px; }
          .header-container { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
          .title { font-size: 32px; font-weight: bold; letter-spacing: -1px; margin: 0; font-family: "Arial Black", Arial, sans-serif; text-transform: uppercase; }
          .address { text-align: center; font-size: 18px; font-weight: bold; border-top: 2px solid #000; border-bottom: 2px solid #000; padding: 4px 0; margin-top: 5px; margin-bottom: 10px; display: inline-block; padding-left: 20px; padding-right: 20px; }
          .ceo-info { font-size: 14px; font-weight: bold; text-align: center; }
          .reg-box { border: 2px solid #000; padding: 8px 12px; font-size: 14px; font-weight: bold; border-radius: 4px; line-height: 1.4; }
          .meta-row { display: flex; justify-content: space-between; margin-bottom: 20px; font-weight: bold; }
          .meta-row span { border-bottom: 1px solid #000; display: inline-block; }
          table { width: 100%; border-collapse: collapse; border: 2px solid #000; margin-bottom: 0; z-index: 2; position: relative; }
          th { border: 1px solid #000; padding: 8px; background: transparent; font-weight: bold; text-align: center; }
          .watermark-container { position: relative; }
          .watermark { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); opacity: 0.15; width: 80%; max-width: 400px; z-index: 0; pointer-events: none; }
          .total-box { display: flex; justify-content: flex-end; margin-top: 0; }
          .total-label { background: #000; color: #fff; font-weight: bold; padding: 6px 12px; border: 2px solid #000; border-top: 0; border-right: 0; }
          .total-value { border: 2px solid #000; border-top: 0; padding: 6px 12px; font-weight: bold; min-width: 100px; text-align: right; }
          .signatures { display: flex; justify-content: space-between; margin-top: 80px; font-weight: bold; }
          .sig-line { border-top: 2px solid #000; width: 220px; text-align: center; padding-top: 4px; }
        </style>
      </head>
      <body>
        <div class="header-container">
          <div style="flex: 1; text-align: center;">
            <div style="display: inline-block; text-align: center;">
              <h1 class="title">ELITEWASH DETERGENT</h1>
              <div class="address">Chak No: 56/W.B. Vehari</div>
              <div class="ceo-info">
                Chief Executive Officer &nbsp;&nbsp;&nbsp;0324-0106056<br/>
                <i style="font-size:16px;">Shoaib Mehmood</i> &nbsp;&nbsp;&nbsp;0300-2791243
              </div>
            </div>
          </div>
          <div class="reg-box">
            Registration No:<br/>
            36603-0283828-3<br/>
            Ref. No: J895834
          </div>
        </div>

        <div class="meta-row" style="margin-top: 40px;">
          <div>Bill No: <span style="min-width:120px;">${sale.billNo || ''}</span></div>
          <div>Date: <span style="min-width:160px;">${sale.date || new Date().toLocaleDateString()}</span></div>
        </div>
        <div class="meta-row">
          <div style="width: 100%;">M/s <span style="width:calc(100% - 40px);">${sale.customerName || ''}</span></div>
        </div>

        <div class="watermark-container">
          <img src="${logoUrl}" class="watermark" />
          <table>
            <thead>
              <tr>
                <th style="width: 10%;">Sr. No:</th>
                <th style="width: 45%;">Description</th>
                <th style="width: 15%;">Qty</th>
                <th style="width: 15%;">Price</th>
                <th style="width: 15%;">Amount</th>
              </tr>
            </thead>
            <tbody>
              ${tableRows}
              ${emptyRows}
            </tbody>
          </table>
        </div>
        
        <div class="total-box">
          <div class="total-label">TOTAL</div>
          <div class="total-value">${sale.totalAmount || 0}</div>
        </div>

        <div class="signatures">
          <div class="sig-line">Manager Signature</div>
          <div class="sig-line">Chief Executive Officer</div>
        </div>

        <script>
          window.onload = function() { setTimeout(function() { window.print(); }, 500); };
        </script>
      </body>
    </html>
  `;

  win.document.open();
  win.document.write(html);
  win.document.close();
}

export function generateSaleReceiptPdf(sale) {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'pt', format: 'a4' });
  const pageWidth = doc.internal.pageSize.getWidth();
  
  // Title
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(28);
  doc.text('ELITEWASH DETERGENT', 40, 50);
  
  // Reg Box
  doc.setFontSize(10);
  doc.setLineWidth(1);
  doc.rect(pageWidth - 160, 30, 120, 45);
  doc.text('Registration No:', pageWidth - 155, 45);
  doc.text('36603-0283828-3', pageWidth - 155, 57);
  doc.text('Ref. No: J895834', pageWidth - 155, 69);
  
  // Address
  doc.setFontSize(14);
  doc.setLineWidth(1.5);
  doc.line(80, 58, 300, 58);
  doc.text('Chak No: 56/W.B. Vehari', 110, 72);
  doc.line(80, 78, 300, 78);
  
  // CEO info
  doc.setFontSize(10);
  doc.text('Chief Executive Officer    0324-0106056', 90, 92);
  doc.setFont('helvetica', 'italic');
  doc.text('Shoaib Mehmood', 110, 104);
  doc.setFont('helvetica', 'bold');
  doc.text('0300-2791243', 210, 104);
  
  // Meta
  doc.setFontSize(12);
  doc.text('Bill No: ', 40, 140);
  doc.line(85, 142, 200, 142);
  doc.text(sale.billNo || '', 90, 140);
  
  doc.text('Date: ', pageWidth - 200, 140);
  doc.line(pageWidth - 160, 142, pageWidth - 40, 142);
  doc.text(sale.date || new Date().toLocaleDateString(), pageWidth - 155, 140);
  
  doc.text('M/s ', 40, 165);
  doc.line(65, 167, pageWidth - 40, 167);
  doc.text(sale.customerName || '', 70, 165);
  
  const rows = [];
  (sale.items || []).forEach((item, idx) => {
    rows.push([
      idx + 1,
      item.description || (item.product_packaging?.products?.name + ' ' + item.product_packaging?.packagings?.name) || '',
      item.quantity || 0,
      item.unit_price || 0,
      (item.quantity || 0) * (item.unit_price || 0)
    ]);
  });
  
  while (rows.length < 10) {
    rows.push(['', '', '', '', '']);
  }
  
  autoTable(doc, {
    startY: 185,
    head: [['Sr. No:', 'Description', 'Qty', 'Price', 'Amount']],
    body: rows,
    theme: 'grid',
    headStyles: { fillColor: [255, 255, 255], textColor: [0, 0, 0], lineColor: [0, 0, 0], lineWidth: 1, halign: 'center' },
    bodyStyles: { textColor: [0, 0, 0], lineColor: [0, 0, 0], lineWidth: 1 },
    columnStyles: { 0: { halign: 'center' }, 2: { halign: 'center' }, 3: { halign: 'right' }, 4: { halign: 'right' } },
    margin: { left: 40, right: 40 }
  });
  
  const finalY = doc.lastAutoTable.finalY;
  
  // Total Box
  doc.setFillColor(0, 0, 0);
  doc.rect(pageWidth - 140, finalY, 60, 20, 'F');
  doc.setTextColor(255, 255, 255);
  doc.text('TOTAL', pageWidth - 128, finalY + 14);
  
  doc.setLineWidth(1);
  doc.rect(pageWidth - 80, finalY, 40, 20, 'S');
  doc.setTextColor(0, 0, 0);
  doc.text(String(sale.totalAmount || 0), pageWidth - 75, finalY + 14);
  
  // Signatures
  doc.setLineWidth(1);
  doc.line(40, finalY + 80, 180, finalY + 80);
  doc.text('Manager Signature', 65, finalY + 95);
  
  doc.line(pageWidth - 180, finalY + 80, pageWidth - 40, finalY + 80);
  doc.text('Chief Executive Officer', pageWidth - 170, finalY + 95);
  
  doc.save('Sale_Receipt_' + (sale.billNo || '1') + '.pdf');
}
"""
with codecs.open('src/lib/exportUtils.js', 'a', encoding='utf-8') as f:
    f.write(code)
