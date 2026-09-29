import re

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's inspect bus_772 (Bus 104) and bus_703 (Bus 10)
lines = ['bus_772', 'bus_703', 'bus_773', 'bus_704', 'bus_705']
for lid in lines:
    idx = text.find(f'"id": "{lid}"')
    if idx != -1:
        snippet = text[idx:idx+800]
        # extract short_name, long_name, directions, stops count
        print(f"--- {lid} ---")
        print(snippet[:snippet.find('"stops":')])
