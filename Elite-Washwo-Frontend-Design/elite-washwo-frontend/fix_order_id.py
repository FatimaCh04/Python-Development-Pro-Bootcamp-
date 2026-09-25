import sys

content = open('src/lib/db.js', 'r', encoding='utf-8').read()

old_str = "sales_order_id: order.id,"
new_str = "sale_order_id: order.id,"

count = content.count(old_str)
print(f"Found {count} occurrences of '{old_str}'")

if count > 0:
    content = content.replace(old_str, new_str)
    open('src/lib/db.js', 'w', encoding='utf-8').write(content)
    print("Fixed 'sales_order_id' to 'sale_order_id'")
else:
    print("Could not find the string to replace.")
