with open('src/lib/db.js', 'r', encoding='utf-8') as f:
    c = f.read()

import re

# We need to add logic to sum selected date sales
old_sale_loop = """  let cumulativeSalePackets = 0;
  let selectedDateCommission = 0;
  
  (allSales || []).forEach(sale => {
    const isSelectedDate = sale.sale_date >= sodIso && sale.sale_date <= eodIso;
    const pkts = (sale.sale_items || []).reduce((a, item) => a + Number(item.quantity || 0), 0);
    cumulativeSalePackets += pkts;
    
    if (isSelectedDate) {
      const commRate = Number(sale.distributors?.commission) || 0;
      selectedDateCommission += (pkts * commRate);
    }
  });"""

new_sale_loop = """  let cumulativeSalePackets = 0;
  let selectedDateCommission = 0;
  let selectedDateSalesAmount = 0;
  let selectedDateSalesPackets = 0;
  let selectedDateSalesCount = 0;
  
  (allSales || []).forEach(sale => {
    const isSelectedDate = sale.sale_date >= sodIso && sale.sale_date <= eodIso;
    const pkts = (sale.sale_items || []).reduce((a, item) => a + Number(item.quantity || 0), 0);
    cumulativeSalePackets += pkts;
    
    if (isSelectedDate) {
      const commRate = Number(sale.distributors?.commission) || 0;
      selectedDateCommission += (pkts * commRate);
      selectedDateSalesAmount += Number(sale.total_amount || 0);
      selectedDateSalesPackets += pkts;
      selectedDateSalesCount += 1;
    }
  });"""

c = c.replace(old_sale_loop, new_sale_loop)

old_return_block = """  return {
    booking: {"""

new_return_block = """  return {
    sales: {
      amount: selectedDateSalesAmount,
      packets: selectedDateSalesPackets,
      count: selectedDateSalesCount
    },
    booking: {"""

c = c.replace(old_return_block, new_return_block)

with open('src/lib/db.js', 'w', encoding='utf-8') as f:
    f.write(c)

print('Updated fetchReportsMetrics to return sales summary')
