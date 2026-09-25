import sys

content = open('src/lib/db.js', 'r', encoding='utf-8').read()

# Fix the submitBooking function - wrong column name
old = "    product_packaging_id: item.packagingId,"
new = "    packaging_id: item.packagingId,"

count = content.count(old)
print(f'Found {count} occurrences of old string')

if count > 0:
    content = content.replace(old, new)
    open('src/lib/db.js', 'w', encoding='utf-8').write(content)
    print('Fixed - packaging_id updated in submitBooking')
else:
    # Show context around sale_items in the new function
    idx = content.find('submitBooking')
    print(repr(content[idx:idx+500]))
