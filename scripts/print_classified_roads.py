import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from inspect_street_network import ways, nodes

print("Main classified roads in area:")
for w in ways:
    hw = w.get('tags', {}).get('highway', '')
    if hw in ['primary', 'secondary', 'tertiary', 'trunk', 'primary_link', 'secondary_link']:
        name = w.get('tags', {}).get('name', 'unnamed')
        oneway = w.get('tags', {}).get('oneway', 'no')
        w_nodes = [nodes[nid] for nid in w['nodes'] if nid in nodes]
        if w_nodes:
            p0 = w_nodes[0]
            p1 = w_nodes[-1]
            print(f"Way #{w['id']}: '{name}' ({hw}, oneway={oneway}) | pts={len(w_nodes)} | ({p0[0]:.5f}, {p0[1]:.5f}) -> ({p1[0]:.5f}, {p1[1]:.5f})")
