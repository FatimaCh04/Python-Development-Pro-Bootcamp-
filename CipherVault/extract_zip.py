import zipfile
import os

zip_path = r"c:\Users\Shahab Computer's\Documents\GitHub\Python-Development-Pro-Bootcamp-\CipherVault\vault-frontend.zip"
extract_to = r"c:\Users\Shahab Computer's\Documents\GitHub\Python-Development-Pro-Bootcamp-\CipherVault\vault-frontend"

# List all files in the zip
print("=== FILES IN ZIP ===")
with zipfile.ZipFile(zip_path, 'r') as zf:
    names = zf.namelist()
    for name in names:
        print(name)

# Extract all files
print("\n=== EXTRACTING ===")
with zipfile.ZipFile(zip_path, 'r') as zf:
    zf.extractall(extract_to)
    print(f"Extracted to: {extract_to}")

# Walk and list extracted files
print("\n=== EXTRACTED FILE TREE ===")
for root, dirs, files in os.walk(extract_to):
    level = root.replace(extract_to, '').count(os.sep)
    indent = '  ' * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = '  ' * (level + 1)
    for f in files:
        print(f"{subindent}{f}")
