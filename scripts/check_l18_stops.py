from parse_static_transit import static_lines

# Check train_18 stops
l18 = [x for x in static_lines if x['id'] == 'train_18'][0]
stops = l18['stops']
print("Stops of train_18:")
for i, s in enumerate(stops):
    print(f"  {i+1:2d}. {s['name']:25s} lat={s['lat']:.4f}")
