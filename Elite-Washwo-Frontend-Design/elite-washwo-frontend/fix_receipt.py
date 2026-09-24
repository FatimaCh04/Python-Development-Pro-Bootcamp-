import re

content = open("src/lib/exportUtils.js", "r", encoding="utf-8").read()

# Remove the watermark image and container from HTML
content = re.sub(r'<img src="\$\{logoUrl\}" class="watermark" />', '', content)
content = re.sub(r'const logoUrl = window\.location\.origin \+ \'/elitewash-logo\.jpg\';\s*', '', content)
content = re.sub(r'\.watermark-container \{ position: relative; \}\s*\.watermark \{ position: absolute; top: 50%; left: 50%; transform: translate\(-50%, -50%\); opacity: 0\.15; width: 80%; max-width: 400px; z-index: 0; pointer-events: none; \}', '', content)

open("src/lib/exportUtils.js", "w", encoding="utf-8").write(content)
print("Receipt fixed")
