from pathlib import Path
import itertools

# ---------------- PARAMETERS ----------------
a_range = range(2, 4)  # coefficients a. case a = 1 solved.
k_range = range(1, 4)  # constants k 
# avoid a or k being zero, as they lead to known behaviours.

# ---------------- GENERATOR ----------------
def collatz_like_an_k_div2(a_range=a_range, k_range=k_range):
    """
    Generate Collatz-like functions of form:
        f(n) = a*n + k   if n odd
               n / 2     if n even
    Returns a list of dictionaries with piecewise rules.
    """
    functions = []
    
    for a, k in itertools.product(a_range, k_range):
        if a % 2 == 0 and k % 2 == 1:
            continue  # skip known non-terminating cases
        if a % 2 == 1 and k % 2 == 0:
            continue  # skip known non-terminating cases
        if a == 2 and k == 2:
            continue # skip solved function
        func = {
            1: f"{a}*n + {k}, if n ≡ 1 (mod 2)",  # odd
            0: "n / 2, if n ≡ 0 (mod 2)"          # even
        }
        functions.append(func)
    
    return functions

# ---------------- WRITE TO FILE ----------------
try:
    script_dir = Path(__file__).resolve().parent
except NameError:
    script_dir = Path.cwd()

out_file = script_dir / "functions.txt"

with out_file.open("w", encoding="utf-8") as f:
    all_funcs = collatz_like_an_k_div2()
    for i, func in enumerate(all_funcs):
        f.write(f"Function {i+1}:\n")
        for res in [1, 0]:  # odd first, even second
            f.write(f"      -> {func[res]}\n")
        f.write("\n")

print(f"Generated {len(all_funcs)} functions written to {out_file}")
