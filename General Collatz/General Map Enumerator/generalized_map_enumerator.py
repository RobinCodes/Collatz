import sys
import multiprocessing as mp


def collatz_like_map(a, b, n, max_steps=5000):
    orbit = []
    seen = {}
    steps = 0

    while n not in seen and steps < max_steps:
        seen[n] = steps
        orbit.append(n)
        if n % 2 == 0:
            n //= 2
        else:
            n = a * n + b
        steps += 1

    if steps >= max_steps:
        return None

    return orbit, seen[n]


def analyze_single_a(args):
    """
    Worker function: analyzes one a for fixed b.
    Returns (a, converging_seeds, cycles)
    """
    a, b, odd_seeds, max_steps = args

    converging_seeds = []
    cycles = []
    cycle_reprs = set()

    for n in odd_seeds:
        res = collatz_like_map(a, b, n, max_steps=max_steps)
        if res is None:
            continue

        orbit, cycle_start = res
        cycle = orbit[cycle_start:]

        m = min(cycle)
        i = cycle.index(m)
        cycle_norm = tuple(cycle[i:] + cycle[:i])

        if cycle_norm not in cycle_reprs:
            cycle_reprs.add(cycle_norm)
            cycles.append((cycle_norm, n))

        converging_seeds.append(n)

    return a, converging_seeds, cycles


def analyze_maps_for_b_parallel(
    b,
    a_min=3,
    a_max=127,
    x_min=1,
    x_max=1000,
    max_steps=5000,
    processes=None,
):
    odd_as = [a for a in range(a_min, a_max + 1) if a % 2 == 1]
    odd_seeds = [n for n in range(x_min, x_max + 1) if n % 2 == 1]

    tasks = [
        (a, b, odd_seeds, max_steps)
        for a in odd_as
    ]

    converging_seeds = {}
    cycles = {}

    with mp.Pool(processes=processes) as pool:
        for a, seeds, cyc in pool.imap_unordered(analyze_single_a, tasks):
            converging_seeds[a] = seeds
            cycles[a] = cyc

    return converging_seeds, cycles


def write_results_to_file(b, converging_seeds, cycles):
    filename = f"b = {b}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Results for maps f(x) = a*x + {b}\n")
        f.write("=" * 50 + "\n\n")

        for a in sorted(converging_seeds):
            f.write(f"Map f(x) = {a}*x + {b}\n")
            f.write(f"Converging odd seeds ({len(converging_seeds[a])}):\n")
            f.write(f"{converging_seeds[a]}\n")

            f.write(f"Cycles ({len(cycles[a])}):\n")
            for cycle, seed in cycles[a]:
                f.write(f"  Seed {seed} -> cycle {list(cycle)}\n")
            f.write("\n")


def main():
    b = 1

    try:
        while True:
            print(f"Starting analysis for b = {b}")

            converging_seeds, cycles = analyze_maps_for_b_parallel(
                b=b,
                a_min=3,
                a_max=127,
                x_min=1,
                x_max=1000,
                max_steps=5000,
                processes=None,  # None = use all CPU cores
            )

            write_results_to_file(b, converging_seeds, cycles)
            b += 2

    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting cleanly.")
        sys.exit(0)


if __name__ == "__main__":
    mp.freeze_support()  # important for Windows
    main()
