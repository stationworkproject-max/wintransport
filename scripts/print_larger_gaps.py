from find_all_network_gaps import dead_end_pairs

print("Dead-end pairs between 50m and 800m:")
for d, u, v in dead_end_pairs:
    if 50 < d < 800:
        print(f"  Gap = {d:6.1f}m between {u} and {v}")
