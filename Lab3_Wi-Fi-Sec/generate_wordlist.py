with open("wordlist.txt", "w") as f:
    for i in range(1_000_000):
        f.write(f"Acme{i:06d}\n")
