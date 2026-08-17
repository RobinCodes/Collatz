import time

STEP_LIMIT = 500
TIME_LIMIT = 0.20 # in seconds per number
CURR_LOW_BOUND = 2**71+(10**7 * 1) + (10**9 * 3) + 1
N = 1_000_000_000 # no. of values to try after lower bound

history: set[int] = set()
start_time = time.time()
steps = 0
timeout: set[int] = set()
out_of_bounds: set[int] = set()

def collatz(n: int) -> int:
    global steps
    init_n = n
    history.add(init_n)
    
    while True:
        if n & 1 == 1:
            n = (3 * n + 1) >> 1
        while n & 1 == 0:
            n = n >> 1  # equivalent to n //= 2
        if n < init_n: 
            return 0
        if n in history:
            print("Cycle detected. (Other than 1-4-2)")
            return 1
        steps += 1
        if steps >= STEP_LIMIT:
            return 2
        history.add(n)
        if time.time() - start_time > TIME_LIMIT:
            return 3
    
for i in range(CURR_LOW_BOUND, CURR_LOW_BOUND + N, 2):
    result = collatz(i)
    if result != 0:
        if result == 1:
            print(f"Counterexample found: {i}")
        if result == 2:
            out_of_bounds.add(i)
        if result == 3:
            timeout.add(i)
    history.clear()
    steps = 0
    start_time = time.time()
    
print("Compiled.")
"""if (input("Overwrite timeout and out of bounds to data.txt? (T/F)")) == False:
    exit(0)"""

if len(timeout) > 0 or len(out_of_bounds) > 0:
    print("Some numbers ran over time, or ran out of bounds.")
    
with open("School Projects [Scripts]/8th Grade/Self/Collatz/data.txt", "w") as f:
    for i in timeout:
        f.write(f"{i}\n")
    f.write("1\n") # to separate
    for i in out_of_bounds:
        f.write(f"{i}\n")

#  2^71 ≈ 2.36×10^21 is how far the sequences have been tested so far (jan. 2025)