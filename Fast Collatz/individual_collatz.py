import time

STEP_LIMIT = 1000000
TIME_LIMIT = 1000 # in seconds per number

history: set[int] = set()
start_time = time.time()
steps = 0

def collatz(n: int) -> int:
    global steps
    init_n = n
    history.add(init_n)
    
    """Returns 0 normally. 1 if n is a counterexample. 2 for step, 3 for time limit."""
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

if __name__ == "__main__":
    with open("School Projects [Scripts]/8th Grade/Self/Collatz/data.txt") as f:
        for line in f:
            value = int(line.strip())
            # Reset history, steps, and start_time for each value
            history.clear()
            steps = 0
            start_time = time.time()
            if value != 1:
                result = collatz(value)
                if result != 0:
                    print(f"Value: {value}, Result: {result}")
                
print("Enumerated.")