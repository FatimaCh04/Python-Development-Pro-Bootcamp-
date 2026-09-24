code = '''
export function printSaleReceipt(sale) {
  const win = window.open("", "_blank");
  if (!win) {
    alert("Please allow popups to print receipts.");
    return;
  }

  const receiptUrl = window.location.origin + "/receipt.jpeg";

  // Image dimensions: 1014 x 1551 px
  // All positions are percentages of the image width/height
  // Measured from the reference image
  // Bill No value: top ~28.3%, left ~13%
  // Date value: top ~28.3%, right area ~74%
  // M/s value: top ~32.6%, left ~10%
  // Table rows start at top ~40.5%, row height ~3.93%
  // Total value: top ~73.9%, left ~79%

  const billNo    = sale.billNo || "";
  const saleDate  = sale.date  || new Date().toLocaleDateString("en-PK");
  const customer  = sale.customerName || "";
  const items     = sale.items || [];
  const total     = sale.totalAmount || 0;

  // Build table rows HTML (up to 15 rows, rest empty)
  const ROW_START_PCT = 40.5;   // % from top for first data row
  const ROW_HEIGHT_PCT = 3.93;  // % height per row
  const MAX_ROWS = 15;

  let rowsHtml = "";
  for (let i = 0; i < MAX_ROWS; i++) {
    const item   = items[i];
    const top    = ROW_START_PCT + i * ROW_HEIGHT_PCT;
    const srNo   = item ? (i + 1) : "";
    const desc   = item ? (item.description || "") : "";
    const qty    = item ? (item.quantity || "") : "";
    const price  = item ? (item.unit_price || "") : "";
    const amount = item ? ((item.quantity || 0) * (item.unit_price || 0)) : "";

    rowsHtml += `
      <div style="position:absolute; top:${top}%; left:3.5%; width:5%; font-size:1.2vw; font-weight:bold; display:flex; align-items:center; justify-content:center;">${srNo}</div>
      <div style="position:absolute; top:${top}%; left:9.5%; width:43%; font-size:1.1vw; display:flex; align-items:center; padding-left:4px;">${desc}</div>
      <div style="position:absolute; top:${top}%; left:45.5%; width:9%; font-size:1.1vw; display:flex; align-items:center; justify-content:center;">${qty}</div>
      <div style="position:absolute; top:${top}%; left:55%; width:12%; font-size:1.1vw; display:flex; align-items:center; justify-content:right; padding-right:4px;">${price}</div>
      <div style="position:absolute; top:${top}%; left:67%; width:30%; font-size:1.1vw; display:flex; align-items:center; justify-content:center;">${amount}</div>
    `;
  }

  const html = `<!DOCTYPE html>
<html>
<head>
  <title>Sale Receipt - ${billNo}</title>
  <style>
    * { margin:0; padding:0; box-sizing:border-box; }
    @page { size: A4 portrait; margin: 0; }
    body { width:100%; height:100vh; }
    .receipt-wrapper {
      position: relative;
      width: 100%;
      max-width: 100%;
    }
    .receipt-wrapper img {
      width: 100%;
      display: block;
    }
    .overlay {
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
    }
    @media print {
      body { margin: 0; }
      .receipt-wrapper { width: 100%; }
    }
  </style>
</head>
<body>
  <div class="receipt-wrapper">
    <img src="${receiptUrl}" alt="Receipt Template" />
    <div class="overlay">
      <!-- Bill No value -->
      <div style="position:absolute; top:28.2%; left:13%; font-size:1.25vw; font-weight:bold;">${billNo}</div>
      <!-- Date value -->
      <div style="position:absolute; top:28.2%; left:74%; font-size:1.25vw; font-weight:bold;">${saleDate}</div>
      <!-- M/s customer -->
      <div style="position:absolute; top:32.5%; left:10%; width:85%; font-size:1.25vw; font-weight:bold;">${customer}</div>

      <!-- Item rows -->
      ${rowsHtml}

      <!-- Total value -->
      <div style="position:absolute; top:73.8%; left:67%; width:30%; font-size:1.3vw; font-weight:bold; display:flex; align-items:center; justify-content:center;">${total}</div>
    </div>
  </div>
  <script>
    window.onload = function() { setTimeout(function() { window.print(); }, 600); };
  </script>
</body>
</html>`;

  win.document.open();
  win.document.write(html);
  win.document.close();
}
'''
with open("src/lib/exportUtils.js", "a", encoding="utf-8") as f:
    f.write(code)
print("Done")
