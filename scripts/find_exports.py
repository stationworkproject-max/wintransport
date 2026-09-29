import re

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

exports = re.findall(r'export const (\w+)\s*=', text)
print("Exports:", exports)
