import json

reports = json.load(open('scripts/detour_reports.json', encoding='utf-8'))
print(f"Total detour legs found across the entire network: {len(reports)}")
lines_affected = set(r['bid'] for r in reports)
print(f"Total lines affected: {len(lines_affected)} out of 190")

total_extra_km = sum(r['detour'] for r in reports) / 1000.0
print(f"Total wasted detour distance across all lines: {total_extra_km:.1f} km!")

reports.sort(key=lambda x: x['detour'], reverse=True)
print("\n--- TOP 20 WORST DETOURS IN NETWORK ---")
for r in reports[:20]:
    name1 = ''.join([c for c in (r['from_stop'] or '') if ord(c) < 128])
    name2 = ''.join([c for c in (r['to_stop'] or '') if ord(c) < 128])
    print(f"Line {r['line']} [{r['dir']} Leg {r['leg_idx']}] {name1} -> {name2}: straight {r['straight']}m, routed {r['routed']}m (+{r['detour']}m, {r['ratio']}x)")
