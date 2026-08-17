from pathlib import Path
import itertools

# ---------------- PARAMETERS ----------------
limit = 10
count = 0

# ---------------- GENERATOR ----------------
def collatz_like_an_k_div2(a_range, k_range):
    global count 
    for a, k in itertools.product(a_range, k_range):
        if a % 2 == 0 and k % 2 == 1:
            continue  # skip known non-terminating cases
        if a % 2 == 1 and k % 2 == 0:
            continue  # skip known non-terminating cases
        if a == 2 and k == 2:
            continue # skip solved function
        count += 1

# ---------------- WRITE TO FILE ----------------
try:
    script_dir = Path(__file__).resolve().parent
except NameError:
    script_dir = Path.cwd()

out_file = script_dir / "counts.txt"

with out_file.open("w", encoding="utf-8") as f:
    for lim in range(1, limit + 1):
        a_range = range(2, lim + 1)
        k_range = range(1, lim + 1)
        count = 0
        collatz_like_an_k_div2(a_range=a_range, k_range=k_range)
        f.write(f"a, k < {lim + 1}, count of valid functions: {count}\n")

