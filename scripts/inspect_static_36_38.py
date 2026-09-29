with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

for target in ['bus_846', 'bus_847']:
    pos = text.find(f'"{target}"')
    print(f"=== Target: {target}, found at: {pos} ===")
    if pos != -1:
        # Find start of object
        start = text.rfind('\n  {\n', 0, pos)
        # Find next object
        next_obj = text.find('\n  {\n', pos)
        if next_obj == -1:
            next_obj = text.find('\n];', pos)
        chunk = text[start:next_obj]
        print(f"Length of chunk: {len(chunk)}")
        # Let's inspect stops_aller and stops_retour
        aller_idx = chunk.find('"stops_aller"')
        retour_idx = chunk.find('"stops_retour"')
        print(f"stops_aller pos: {aller_idx}, stops_retour pos: {retour_idx}")
        if aller_idx != -1:
            print("--- STOPS ALLER ---")
            print(chunk[aller_idx:aller_idx+800])
        if retour_idx != -1:
            print("--- STOPS RETOUR ---")
            print(chunk[retour_idx:retour_idx+800])
