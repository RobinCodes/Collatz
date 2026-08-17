from collections import deque

def inverse_collatz_formulas(
    max_depth=6, 
    skip_double_only=True
):
    """
    Generate symbolic formulas for all numbers at each depth
    using inverse Collatz steps:
      even-step: x -> 2*x
      odd-step:  x -> (x-1)/3  if valid
    We start from '1' at depth 0.
    """

    # Each item: (formula_str, current_value_expr, depth, last_op)
    # last_op: 'double' or 'odd' to know if the last step was (x-1)/3 or doubling
    start = ("1", 1, 0, None)
    q = deque([start])
    levels = {0: ["1"]}

    while q:
        formula, val, depth, last_op = q.popleft()
        if depth >= max_depth:
            continue

        # Always-valid even parent: 2*x
        new_formula_double = f"2*({formula})"
        if not (skip_double_only and last_op == 'double'):  # skip pure 2^k growth if enabled
            levels.setdefault(depth + 1, []).append(new_formula_double)
        q.append((new_formula_double, 2 * val, depth + 1, 'double'))

        # Odd parent: (x-1)/3 if valid
        if val % 3 == 1:
            new_val = (val - 1) // 3
            if new_val > 0 and new_val % 2 == 1:  # valid odd parent
                new_formula_odd = f"({formula}-1)/3"
                levels.setdefault(depth + 1, []).append(new_formula_odd)
                q.append((new_formula_odd, new_val, depth + 1, 'odd'))

    # Print all formulas grouped by depth
    for d in range(max_depth + 1):
        if d in levels:
            print(f"Depth {d}: " + ", ".join(levels[d]))

    return levels


# Example: 6 depths, skipping formulas that are just doubling previous ones
formulas = inverse_collatz_formulas(max_depth=6, skip_double_only=False)
