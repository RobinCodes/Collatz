"""
Collatz-like sequence analyzer for rule (a*x + k).

Determines whether, for given parameters `a` and `k`,
all starting numbers up to `limit_n` diverge or any enter a loop.
"""

from typing import Dict, List

# --- Observations ---
# 2x0 - LOOP
# 2x2 - LOOP
# 2x4 - DIVERGE
# 2x6 - LOOP
# 2x8 - DIVERGE
# 2x10 - LOOP
# 2x12 - DIVERGE
# --------------------
# 4x0 - LOOP
# 4x2 - DIVERGE
# 4x4 - LOOP
# 4x6 - DIVERGE
# 4x8 - DIVERGE
# 4x10 - DIVERGE
# 4x12 - LOOP
# 4x14 - DIVERGE
# 4x16 - DIVERGE
# 4x18 - DIVERGE
# 4x20 - LOOP
# --------------------
# 6x0 - Excluding k = 0 cases from now on
# 6x2 - LOOP
# 6x4 - DIVERGE
# 6x6 - LOOP
# 6x8 - DIVERGE
# 6x10 - LOOP
# 6x12 - DIVERGE
# 6x14 - LOOP
# --------------------
# 8x2 - DIVERGE
# 8x4 - DIVERGE
# 8x6 - DIVERGE
# 8x8 - LOOP
# 8x10 - DIVERGE
# 8x12 - DIVERGE
# 8x14 - DIVERGE
# 8x16 - DIVERGE
# 8x18 - DIVERGE
# 8x20 - DIVERGE
# 8x22 - DIVERGE
# 8x24 - LOOP

# --- Configuration ---
a: int = 8
k: int = 24
max_steps: int = 500
limit_n: int = 1000
# ----------------------

def collatz_next(n: int) -> int:
    """Compute next number in (a*x + k) Collatz-like sequence."""
    return n // 2 if n % 2 == 0 else a * n + k


def all_diverge_or_loop(a: int, k: int, limit_n: int, max_steps: int) -> bool:
    """
    Returns True if all sequences diverge (no loops detected),
    otherwise False if any loop is found.
    """
    known_loops: Dict[int, bool] = {}

    for start in range(1, limit_n + 1):
        n: int = start
        visited: Dict[int, int] = {}
        seq: List[int] = [n]
        steps: int = 0

        while steps < max_steps:
            if n in known_loops:
                # already confirmed part of a loop
                return False

            if n in visited:
                # loop detected
                loop_start_idx: int = visited[n]
                loop = seq[loop_start_idx:]
                for num in loop:
                    known_loops[num] = True
                return False

            visited[n] = len(seq) - 1
            n = collatz_next(n)
            seq.append(n)
            steps += 1

    # if we got here, no loops were found within max_steps
    return True


def main() -> None:
    diverge: bool = all_diverge_or_loop(a, k, limit_n, max_steps)
    print(f"For a={a}, k={k}, limit_n={limit_n}:")
    print("→ ALL DIVERGE" if diverge else "→ LOOPS EXIST")


if __name__ == "__main__":
    main()
