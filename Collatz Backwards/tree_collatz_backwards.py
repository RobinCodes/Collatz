from collections import deque, defaultdict

def is_power_of_two(n):
    return n > 0 and (n & (n - 1)) == 0

def inverse_collatz_by_depth(
    max_depth=10, 
    max_value=10**6, 
    exclude_powers_of_two=True, 
    exclude_even=False
):
    parents = defaultdict(list)
    visited = set([1])
    q = deque([(1, 0)])  # (node, depth)
    levels = defaultdict(list)  # depth -> list of nodes at that depth
    levels[0].append(1)

    while q:
        node, depth = q.popleft()
        if depth >= max_depth:
            continue

        # always-valid even parent
        p_even = 2 * node
        if p_even <= max_value:
            parents[node].append(p_even)
            if p_even not in visited:
                visited.add(p_even)
                q.append((p_even, depth + 1))
                if not ((exclude_powers_of_two and is_power_of_two(p_even)) or 
                        (exclude_even and p_even % 2 == 0)):
                    levels[depth + 1].append(p_even)

        # possible odd parent: p = (node - 1) // 3
        if node % 3 == 1:
            p_odd = (node - 1) // 3
            if p_odd > 0 and (p_odd % 2 == 1):
                parents[node].append(p_odd)
                if p_odd not in visited and p_odd <= max_value:
                    visited.add(p_odd)
                    q.append((p_odd, depth + 1))
                    if not ((exclude_powers_of_two and is_power_of_two(p_odd)) or 
                            (exclude_even and p_odd % 2 == 0)):
                        levels[depth + 1].append(p_odd)

    # Print each depth on one line
    for d in range(max_depth + 1):
        if d in levels:
            print(f"Depth {d}: ", " ".join(str(x) for x in sorted(levels[d])))

    return parents, levels


# Example: exclude even numbers and powers of 2
parents, levels = inverse_collatz_by_depth(
    max_depth=30, 
    max_value=1000000, 
    exclude_powers_of_two=True, 
    exclude_even=True
)
