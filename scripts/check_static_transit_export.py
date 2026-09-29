with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's see how staticTransit is exported
print("First 200 chars:")
print(text[:200])
print("\nLast 200 chars:")
print(text[-200:])
