import json
import re

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all lines in staticTransit.js
matches = re.findall(r'"id":\s*"(train_[^"]+|rfr_[^"]+)",\s*"name":\s*"([^"]+)"', content)
print(f"Total train/rfr lines matched: {len(matches)}")
for lid, name in matches:
    print(f"  {lid}: {name}")
