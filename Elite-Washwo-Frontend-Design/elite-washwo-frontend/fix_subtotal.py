import sys

content = open('src/lib/db.js', 'r', encoding='utf-8').read()

old_str = """    sale_order_id: order.id,
    packaging_id: item.packagingId,
    quantity: item.quantity,
    unit_price: item.price
  }));"""

new_str = """    sale_order_id: order.id,
    packaging_id: item.packagingId,
    quantity: item.quantity,
    unit_price: item.price,
    subtotal: item.quantity * item.price
  }));"""

count = content.count(old_str)
print(f"Found {count} occurrences of old_str")

if count > 0:
    content = content.replace(old_str, new_str)
    open('src/lib/db.js', 'w', encoding='utf-8').write(content)
    print("Fixed 'subtotal' in db.js")
else:
    print("Could not find the exact string to replace.")
