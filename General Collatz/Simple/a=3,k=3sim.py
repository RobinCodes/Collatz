#!/usr/bin/env python3
"""
Collatz-like sequence generator (3x+3) with loop detection.

Configuration:
    max_steps : maximum number of steps per sequence
    limit_n   : highest starting integer to run (from 1)
"""

def collatz_next(n: int):
    return n // 2 if n % 2 == 0 else 3 * n + 3

def main():
    # --- User configuration ---
    max_steps = 1000
    limit_n = 100000
    # ---------------------------

    loop_counter = 1
    known_loops = {}  # number -> loop number

    for start in range(1, limit_n + 1):
        n = start
        seq = [n]
        visited = {}
        steps = 0

        while steps < max_steps:
            if n in known_loops:
                loop_num = known_loops[n]
                if loop_num != 1:
                    print(f"LOOP {loop_num}: " + " -> ".join(map(str, seq)))
                break

            if n in visited:
                # New loop detected
                loop_start_idx = visited[n]
                loop = seq[loop_start_idx:]
                # Assign loop number to all numbers in the loop
                for num in loop:
                    known_loops[num] = loop_counter
                if loop_counter != 1:
                    print(f"LOOP {loop_counter}: " + " -> ".join(map(str, seq)))
                loop_counter += 1
                break

            visited[n] = len(seq) - 1
            n = collatz_next(n)
            seq.append(n)
            steps += 1
        else:
            # Max steps reached without entering a loop
            print("DIVERGE: " + " -> ".join(map(str, seq)))

if __name__ == "__main__":
    main()
